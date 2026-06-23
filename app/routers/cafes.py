"""Cafe endpoints: list (filter + paginate), detail, availability, create."""
import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.database import get_db
from app.models.cafe import Cafe
from app.schemas.cafe import AvailabilityOut, CafeCreate, CafeOut, PaginatedCafes
from app.services import booking_service

router = APIRouter(prefix="/cafes", tags=["cafes"])


@router.get("", response_model=PaginatedCafes, summary="List cafes (filter by city, paginated)")
def list_cafes(
    db: Session = Depends(get_db),
    city: str | None = Query(None, description="Filter by city (case-insensitive)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    base = select(Cafe)
    count = select(func.count(Cafe.id))
    if city:
        condition = func.lower(Cafe.city) == city.strip().lower()
        base = base.where(condition)
        count = count.where(condition)

    total = db.execute(count).scalar_one()
    items = db.execute(
        base.order_by(Cafe.id).offset((page - 1) * limit).limit(limit)
    ).scalars().all()
    pages = (total + limit - 1) // limit if total else 0
    return {"items": items, "total": total, "page": page, "limit": limit, "pages": pages}


@router.get("/{cafe_id}", response_model=CafeOut, summary="Get a single cafe")
def get_cafe(cafe_id: int, db: Session = Depends(get_db)):
    return booking_service.get_cafe_or_404(db, cafe_id)


@router.get(
    "/{cafe_id}/availability",
    response_model=AvailabilityOut,
    summary="Open seats per slot for a date",
)
def cafe_availability(
    cafe_id: int,
    date: datetime.date = Query(..., description="Date to check, YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    return booking_service.get_availability(db, cafe_id, date)


@router.post(
    "",
    response_model=CafeOut,
    status_code=201,
    dependencies=[Depends(require_auth)],
    summary="Add a cafe (admin, auth required)",
)
def create_cafe(payload: CafeCreate, db: Session = Depends(get_db)):
    cafe = Cafe(**payload.model_dump())
    db.add(cafe)
    db.commit()
    db.refresh(cafe)
    return cafe
