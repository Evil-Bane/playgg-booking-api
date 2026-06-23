"""Auth endpoint: exchange demo credentials for a JWT (bonus)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Log in, get a JWT")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise APIError(401, "Invalid username or password.", code="invalid_credentials")
    return {"access_token": create_access_token(user.username)}
