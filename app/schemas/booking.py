"""Pydantic schemas for bookings.

Structural validation (types, ranges, slot format) lives here; business rules
(cafe exists, capacity, duplicates, past dates) live in the booking service.
"""
import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Hourly slot like "18:00-19:00".
SLOT_RE = re.compile(r"^([01]\d|2[0-3]):00-([01]\d|2[0-3]):00$")


class BookingCreate(BaseModel):
    cafe_id: int = Field(..., gt=0)
    user_name: str = Field(..., min_length=1, max_length=120)
    date: datetime.date = Field(..., description="Booking date, YYYY-MM-DD")
    time_slot: str = Field(..., examples=["18:00-19:00"])
    seats_booked: int = Field(..., gt=0)

    @field_validator("time_slot")
    @classmethod
    def validate_slot(cls, v: str) -> str:
        v = v.strip()
        if not SLOT_RE.match(v):
            raise ValueError(
                "time_slot must be an hourly slot like '18:00-19:00'"
            )
        start, end = v.split("-")
        if int(end[:2]) != int(start[:2]) + 1:
            raise ValueError(
                "time_slot must span exactly one hour, e.g. '18:00-19:00'"
            )
        return v

    @field_validator("user_name")
    @classmethod
    def strip_user_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("user_name cannot be blank")
        return v


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    cafe_id: int
    user_name: str
    date: datetime.date
    time_slot: str
    seats_booked: int
    status: str
