from __future__ import annotations

from pydantic import BaseModel, Field


class AuthCredentialsBody(BaseModel):
    email: str
    password: str = Field(min_length=8)


class CurrentUserResponse(BaseModel):
    user_id: str
    email: str
    auth_provider: str
    created_at: str
    last_login_at: str | None = None


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: str
    user: CurrentUserResponse


class LogoutResponse(BaseModel):
    success: bool = True