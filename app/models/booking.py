"""Booking ORM model.

Design notes
------------
* A slot is identified by (cafe_id, date, time_slot). Many bookings can share a
  slot as long as their seats sum to <= the cafe's total_seats.
* ``status`` is "confirmed" or "cancelled". Cancellation is a soft delete so
  seats are released while history is preserved.
* The partial unique index enforces "no double-booking" at the DB level — the
  same user cannot hold two *active* bookings for the same slot — while still
  allowing them to rebook after cancelling.
"""
from __future__ import annotations

from datetime import date as date_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.cafe import Cafe


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        # Speeds up the per-slot capacity aggregation query.
        Index("ix_booking_slot", "cafe_id", "date", "time_slot"),
        # No double-booking: one active booking per (cafe, date, slot, user).
        # Partial so cancelled rows don't block a legitimate rebooking.
        Index(
            "uq_active_booking",
            "cafe_id",
            "date",
            "time_slot",
            "user_name",
            unique=True,
            sqlite_where=text("status = 'confirmed'"),
            postgresql_where=text("status = 'confirmed'"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cafe_id: Mapped[int] = mapped_column(
        ForeignKey("cafes.id", ondelete="CASCADE"), nullable=False
    )
    user_name: Mapped[str] = mapped_column(String(120), nullable=False)
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    time_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    seats_booked: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")

    cafe: Mapped["Cafe"] = relationship(back_populates="bookings")
