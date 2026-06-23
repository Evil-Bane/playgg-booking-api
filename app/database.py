"""Database engine, session factory, and the declarative Base."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base class shared by all ORM models."""


# SQLite needs check_same_thread disabled for use across FastAPI's threadpool.
connect_args = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # gracefully recycle dropped Postgres connections
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    """FastAPI dependency that yields a request-scoped database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
