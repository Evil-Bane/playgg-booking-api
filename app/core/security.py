"""Password hashing (bcrypt) and JWT issue/verify for the auth bonus."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.errors import APIError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# auto_error=False so we can return our own consistent error envelope.
_bearer = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """Dependency that validates the Bearer token and returns the username."""
    if credentials is None:
        raise APIError(
            401, "Authentication required. Provide a Bearer token.", code="unauthorized"
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise APIError(401, "Token has expired. Please log in again.", code="token_expired")
    except jwt.InvalidTokenError:
        raise APIError(401, "Invalid authentication token.", code="invalid_token")
    return payload.get("sub")
