from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.observability.context import bind_context
from backend.observability.logging import get_logger, log_event
from backend.services.auth_service import get_current_user_from_token


bearer_scheme = HTTPBearer(auto_error=False)
logger = get_logger(__name__)


def require_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, str | None]:
    if credentials is None or not credentials.credentials:
        log_event(
            logger,
            "unauthorized_access_attempt",
            level=logging.WARNING,
            endpoint=request.url.path,
            method=request.method,
            error_type="missing_bearer_token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_current_user_from_token(credentials.credentials)
    request.state.user_id = user.get("user_id")
    bind_context(user_id=user.get("user_id"))
    return user


def require_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials is None or not credentials.credentials:
        log_event(
            logger,
            "unauthorized_access_attempt",
            level=logging.WARNING,
            endpoint=request.url.path,
            method=request.method,
            error_type="missing_bearer_token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials