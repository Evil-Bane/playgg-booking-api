"""Seed sample cafes and the demo admin user.

Idempotent: only inserts when the respective table is empty, so the hosted demo
always has data without duplicating on every restart.
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password
from app.models.cafe import Cafe
from app.models.user import User

SAMPLE_CAFES = [
    {"name": "Nexus Arena", "location": "MI Road", "city": "Jaipur", "price_per_hour": 120.0, "total_seats": 20},
    {"name": "Frag Hub", "location": "Vaishali Nagar", "city": "Jaipur", "price_per_hour": 100.0, "total_seats": 15},
    {"name": "Respawn Lounge", "location": "Koramangala", "city": "Bengaluru", "price_per_hour": 150.0, "total_seats": 30},
    {"name": "GG Station", "location": "Andheri West", "city": "Mumbai", "price_per_hour": 180.0, "total_seats": 25},
    {"name": "Critical Hit Cafe", "location": "Hauz Khas", "city": "Delhi", "price_per_hour": 160.0, "total_seats": 18},
    {"name": "Pixel Pit", "location": "Banjara Hills", "city": "Hyderabad", "price_per_hour": 140.0, "total_seats": 22},
]


def seed(db: Session) -> None:
    if db.execute(select(func.count(Cafe.id))).scalar_one() == 0:
        db.add_all(Cafe(**c) for c in SAMPLE_CAFES)
    if db.execute(select(func.count(User.id))).scalar_one() == 0:
        db.add(
            User(
                username=settings.ADMIN_USERNAME,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
            )
        )
    db.commit()
