"""Unit tests for the booking business logic.

Each test gets a fresh in-memory SQLite database with one cafe (10 seats) so the
rules can be exercised in isolation without a running server.
"""
import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.errors import APIError
from app.database import Base
from app.models.cafe import Cafe
from app.services import booking_service

FUTURE = datetime.date.today() + datetime.timedelta(days=3)
SLOT = "18:00-19:00"


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # keep one shared in-memory connection
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(
        Cafe(name="Test Cafe", location="X", city="Jaipur", price_per_hour=100.0, total_seats=10)
    )
    session.commit()
    yield session
    session.close()


def book(db, **overrides):
    params = dict(cafe_id=1, user_name="alice", on_date=FUTURE, time_slot=SLOT, seats_booked=2)
    params.update(overrides)
    return booking_service.create_booking(db, **params)


def test_successful_booking(db):
    b = book(db)
    assert b.id is not None
    assert b.status == "confirmed"


def test_cafe_not_found(db):
    with pytest.raises(APIError) as exc:
        book(db, cafe_id=999)
    assert exc.value.code == "cafe_not_found"
    assert exc.value.status_code == 404


def test_request_exceeds_total_seats(db):
    with pytest.raises(APIError) as exc:
        book(db, seats_booked=99)
    assert exc.value.code == "exceeds_total_seats"


def test_capacity_exceeded_across_bookings(db):
    book(db, user_name="a", seats_booked=8)
    with pytest.raises(APIError) as exc:
        book(db, user_name="b", seats_booked=5)  # 8 + 5 > 10
    assert exc.value.code == "not_enough_seats"


def test_different_users_share_a_slot(db):
    book(db, user_name="alice", seats_booked=4)
    b = book(db, user_name="bob", seats_booked=4)  # 4 + 4 <= 10
    assert b.id is not None


def test_double_booking_same_user_rejected(db):
    book(db, user_name="alice")
    with pytest.raises(APIError) as exc:
        book(db, user_name="alice")
    assert exc.value.code == "double_booking"


def test_cancel_releases_seats(db):
    b = book(db, user_name="alice", seats_booked=10)  # fills the slot
    with pytest.raises(APIError):
        book(db, user_name="bob", seats_booked=1)
    booking_service.cancel_booking(db, b.id)
    freed = book(db, user_name="bob", seats_booked=1)
    assert freed.id is not None


def test_user_can_rebook_after_cancelling(db):
    b = book(db, user_name="alice", seats_booked=2)
    booking_service.cancel_booking(db, b.id)
    again = book(db, user_name="alice", seats_booked=2)
    assert again.id != b.id


def test_cancel_unknown_booking(db):
    with pytest.raises(APIError) as exc:
        booking_service.cancel_booking(db, 12345)
    assert exc.value.code == "booking_not_found"


def test_cancel_twice_rejected(db):
    b = book(db)
    booking_service.cancel_booking(db, b.id)
    with pytest.raises(APIError) as exc:
        booking_service.cancel_booking(db, b.id)
    assert exc.value.code == "already_cancelled"


def test_past_date_rejected(db):
    past = datetime.date.today() - datetime.timedelta(days=1)
    with pytest.raises(APIError) as exc:
        book(db, on_date=past)
    assert exc.value.code == "past_date"


def test_invalid_slot_rejected(db):
    with pytest.raises(APIError) as exc:
        book(db, time_slot="25:00-26:00")
    assert exc.value.code == "invalid_slot"


def test_availability_reflects_bookings(db):
    book(db, user_name="alice", seats_booked=3)
    availability = booking_service.get_availability(db, 1, FUTURE)
    slot = next(s for s in availability["slots"] if s["time_slot"] == SLOT)
    assert slot["booked_seats"] == 3
    assert slot["available_seats"] == 7
