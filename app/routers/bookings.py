"""Booking endpoints: create, list-for-cafe, cancel.

Paths follow the assignment brief verbatim:
  * GET    /bookings/{cafe_id}   -> bookings for a cafe
  * DELETE /bookings/{id}        -> cancel a booking
(A more RESTful alternative would nest listing under /cafes/{id}/bookings.)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.database import get_db
from app.schemas.booking import BookingCreate, BookingOut
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingOut,
    status_code=201,
    dependencies=[Depends(require_auth)],
    summary="Create a booking (auth required)",
)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    return booking_service.create_booking(
        db,
        cafe_id=payload.cafe_id,
        user_name=payload.user_name,
        on_date=payload.date,
        time_slot=payload.time_slot,
        seats_booked=payload.seats_booked,
    )


@router.get(
    "/{cafe_id}",
    response_model=list[BookingOut],
    summary="List all bookings for a cafe",
)
def bookings_for_cafe(cafe_id: int, db: Session = Depends(get_db)):
    return booking_service.list_cafe_bookings(db, cafe_id)


@router.delete(
    "/{booking_id}",
    response_model=BookingOut,
    dependencies=[Depends(require_auth)],
    summary="Cancel a booking (auth required)",
)
def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    return booking_service.cancel_booking(db, booking_id)
