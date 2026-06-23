"""Pydantic schemas for cafes, pagination, and availability."""
import datetime

from pydantic import BaseModel, ConfigDict, Field


class CafeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    location: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=80)
    price_per_hour: float = Field(..., gt=0, description="Hourly price in INR")
    total_seats: int = Field(..., gt=0)


class CafeCreate(CafeBase):
    """Body for the (auth-protected) admin endpoint to add a cafe."""


class CafeOut(CafeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PaginatedCafes(BaseModel):
    items: list[CafeOut]
    total: int
    page: int
    limit: int
    pages: int


class SlotAvailability(BaseModel):
    time_slot: str
    total_seats: int
    booked_seats: int
    available_seats: int


class AvailabilityOut(BaseModel):
    cafe_id: int
    date: datetime.date
    slots: list[SlotAvailability]
