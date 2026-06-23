"""Importing the package registers every model on the shared Base metadata."""
from app.models.booking import Booking
from app.models.cafe import Cafe
from app.models.user import User

__all__ = ["Cafe", "Booking", "User"]
