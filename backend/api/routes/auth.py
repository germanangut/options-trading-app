"""App-level authentication routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies.auth import require_bearer_token, require_current_user
from backend.api.schemas.auth import (
    AuthCredentialsBody,
    AuthSessionResponse,
    CurrentUserResponse,
    LogoutResponse,
)
from backend.services.auth_service import login_user, logout_user, register_user


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSessionResponse)
def register_route(payload: AuthCredentialsBody) -> dict[str, object]:
    try:
        return register_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthSessionResponse)
def login_route(payload: AuthCredentialsBody) -> dict[str, object]:
    try:
        return login_user(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/logout", response_model=LogoutResponse)
def logout_route(token: str = Depends(require_bearer_token)) -> dict[str, bool]:
    logout_user(token)
    return {"success": True}


@router.get("/me", response_model=CurrentUserResponse)
def me_route(
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, str | None]:
    return current_user