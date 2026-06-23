"""Application configuration, loaded from environment variables (or a .env file).

Everything has a sensible local default so the API runs out of the box with
SQLite. In production (Render) only DATABASE_URL and JWT_SECRET need to be set.
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database -----------------------------------------------------------
    # SQLite by default for zero-config local dev; set DATABASE_URL to a
    # Postgres connection string in production.
    DATABASE_URL: str = "sqlite:///./playgg.db"

    # --- Auth (bonus) -------------------------------------------------------
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Seeded demo admin used to obtain a token via POST /login.
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin"

    # --- Booking slots ------------------------------------------------------
    # Hourly slots are generated for the [OPENING_HOUR, CLOSING_HOUR) window
    # and used by both validation and the availability endpoint.
    OPENING_HOUR: int = 10
    CLOSING_HOUR: int = 22

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        # Render/Heroku hand out "postgres://" which SQLAlchemy no longer
        # accepts — rewrite to the modern "postgresql://" scheme.
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()
