"""Core booking business logic.

Kept separate from the routers so the rules are easy to unit-test in isolation.
All functions take an explicit Session so they work the same in tests and
request handlers.
"""
from datetime import date as date_type

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.errors import APIError
from app.models.booking import Booking
from app.models.cafe import Cafe

# Fixed hourly slots derived from the configured operating window.
VALID_SLOTS: list[str] = [
    f"{h:02d}:00-{h + 1:02d}:00"
    for h in range(settings.OPENING_HOUR, settings.CLOSING_HOUR)
]


def get_cafe_or_404(db: Session, cafe_id: int, *, lock: bool = False) -> Cafe:
    """Fetch a cafe or raise a 404. ``lock`` row-locks it (Postgres) so
    concurrent bookings on the same slot serialise and can't oversell."""
    stmt = select(Cafe).where(Cafe.id == cafe_id)
    if lock and db.bind.dialect.name != "sqlite":
        stmt = stmt.with_for_update()
    cafe = db.execute(stmt).scalar_one_or_none()
    if cafe is None:
        raise APIError(404, f"Cafe with id {cafe_id} not found.", code="cafe_not_found")
    return cafe


def _booked_seats(db: Session, cafe_id: int, on_date: date_type, time_slot: str) -> int:
    """Seats already taken by active bookings for one slot."""
    stmt = select(func.coalesce(func.sum(Booking.seats_booked), 0)).where(
        Booking.cafe_id == cafe_id,
        Booking.date == on_date,
        Booking.time_slot == time_slot,
        Booking.status == "confirmed",
    )
    return int(db.execute(stmt).scalar_one())


def create_booking(
    db: Session,
    *,
    cafe_id: int,
    user_name: str,
    on_date: date_type,
    time_slot: str,
    seats_booked: int,
) -> Booking:
    """Validate and persist a booking, or raise APIError with a clear message."""
    cafe = get_cafe_or_404(db, cafe_id, lock=True)

    if time_slot not in VALID_SLOTS:
        raise APIError(
            422,
            f"Invalid time_slot '{time_slot}'. Cafe operates "
            f"{settings.OPENING_HOUR:02d}:00–{settings.CLOSING_HOUR:02d}:00 "
            f"in 1-hour slots.",
            code="invalid_slot",
        )

    if on_date < date_type.today():
        raise APIError(422, "Cannot create a booking for a past date.", code="past_date")

    # A single request can never exceed the cafe's physical capacity.
    if seats_booked > cafe.total_seats:
        raise APIError(
            409,
            f"Requested {seats_booked} seat(s) but '{cafe.name}' only has "
            f"{cafe.total_seats} in total.",
            code="exceeds_total_seats",
        )

    # No double-booking: same user, same active slot.
    existing = db.execute(
        select(Booking).where(
            Booking.cafe_id == cafe_id,
            Booking.date == on_date,
            Booking.time_slot == time_slot,
            Booking.user_name == user_name,
            Booking.status == "confirmed",
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise APIError(
            409,
            f"'{user_name}' already has a booking for '{cafe.name}' on "
            f"{on_date} at {time_slot}.",
            code="double_booking",
        )

    # Capacity: requested seats must fit alongside existing bookings.
    available = cafe.total_seats - _booked_seats(db, cafe_id, on_date, time_slot)
    if seats_booked > available:
        raise APIError(
            409,
            f"Only {available} seat(s) left for {time_slot} on {on_date}; "
            f"you requested {seats_booked}.",
            code="not_enough_seats",
        )

    booking = Booking(
        cafe_id=cafe_id,
        user_name=user_name,
        date=on_date,
        time_slot=time_slot,
        seats_booked=seats_booked,
        status="confirmed",
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:
        # Backstop for the unique-index race if two duplicate requests interleave.
        db.rollback()
        raise APIError(
            409,
            f"'{user_name}' already has a booking for this slot.",
            code="double_booking",
        )
    db.refresh(booking)
    return booking


def list_cafe_bookings(db: Session, cafe_id: int) -> list[Booking]:
    get_cafe_or_404(db, cafe_id)
    return list(
        db.execute(
            select(Booking)
            .where(Booking.cafe_id == cafe_id)
            .order_by(Booking.date, Booking.time_slot, Booking.id)
        ).scalars()
    )


def cancel_booking(db: Session, booking_id: int) -> Booking:
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise APIError(
            404, f"Booking with id {booking_id} not found.", code="booking_not_found"
        )
    if booking.status == "cancelled":
        raise APIError(409, "Booking is already cancelled.", code="already_cancelled")
    booking.status = "cancelled"  # soft delete — releases the seats
    db.commit()
    db.refresh(booking)
    return booking


def get_availability(db: Session, cafe_id: int, on_date: date_type) -> dict:
    """Open seats per slot for a cafe on a given date."""
    cafe = get_cafe_or_404(db, cafe_id)
    rows = db.execute(
        select(Booking.time_slot, func.sum(Booking.seats_booked))
        .where(
            Booking.cafe_id == cafe_id,
            Booking.date == on_date,
            Booking.status == "confirmed",
        )
        .group_by(Booking.time_slot)
    ).all()
    booked = {slot: int(total) for slot, total in rows}
    slots = [
        {
            "time_slot": slot,
            "total_seats": cafe.total_seats,
            "booked_seats": booked.get(slot, 0),
            "available_seats": cafe.total_seats - booked.get(slot, 0),
        }
        for slot in VALID_SLOTS
    ]
    return {"cafe_id": cafe_id, "date": on_date, "slots": slots}
