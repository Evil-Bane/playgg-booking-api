"""FastAPI application entrypoint.

On startup it creates tables and seeds demo data. Interactive API docs are
served at /docs (Swagger UI) and /redoc.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401 — registers models on Base.metadata
from app.core.errors import register_error_handlers
from app.database import Base, SessionLocal, engine
from app.routers import auth, bookings, cafes
from app.seed import seed


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="PlayGG Cafe Booking API",
    description=(
        "Backend for booking seats at gaming cafes across India. "
        "Browse cafes, check availability, and book or cancel seats."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.include_router(cafes.router)
app.include_router(bookings.router)
app.include_router(auth.router)


@app.get("/", tags=["health"], summary="Service info")
def root():
    return {"status": "ok", "service": "PlayGG Cafe Booking API", "docs": "/docs"}


@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "healthy"}
