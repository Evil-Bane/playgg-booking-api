"""Pydantic schemas for the auth (login) flow."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str = Field(..., max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
