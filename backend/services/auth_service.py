from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import logging
import secrets
from uuid import uuid4

from fastapi import HTTPException, status

from backend.contracts.identity_models import UserRecord
from backend.observability.context import bind_context
from backend.observability.logging import get_logger, log_event
from backend.repositories.factory import get_auth_repository
from settings import get_settings


LOCAL_AUTH_PROVIDER = "local"
MIN_PASSWORD_LENGTH = 8
logger = get_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        200_000,
    ).hex()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _session_ttl_hours() -> int:
    value = get_settings().get("auth_session_ttl_hours", 168)
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return 168


def _serialize_user(user: UserRecord) -> dict[str, str | None]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "auth_provider": user.auth_provider,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


def _validate_credentials(email: str, password: str) -> tuple[str, str]:
    normalized_email = _normalize_email(email)
    password = password or ""

    if not normalized_email or "@" not in normalized_email:
        raise ValueError("A valid email address is required.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )

    return normalized_email, password


def _issue_session(user: UserRecord) -> dict[str, object]:
    repository = get_auth_repository()
    created_at = _utc_now_iso()
    expires_at = (
        datetime.now(UTC) + timedelta(hours=_session_ttl_hours())
    ).isoformat().replace("+00:00", "Z")
    raw_token = secrets.token_urlsafe(32)

    repository.create_session(
        session_id=f"session_{uuid4().hex}",
        user_id=user.user_id,
        token_hash=_hash_token(raw_token),
        created_at=created_at,
        expires_at=expires_at,
    )

    return {
        "access_token": raw_token,
        "token_type": "bearer",
        "expires_at": expires_at,
        "user": _serialize_user(user),
    }


def register_user(email: str, password: str) -> dict[str, object]:
    normalized_email, password = _validate_credentials(email, password)
    repository = get_auth_repository()

    if repository.get_user_by_email(normalized_email) is not None:
        raise ValueError("A user with that email already exists.")

    now = _utc_now_iso()
    salt_hex = secrets.token_hex(16)
    user = repository.create_user(
        user_id=f"user_{uuid4().hex}",
        email=normalized_email,
        auth_provider=LOCAL_AUTH_PROVIDER,
        created_at=now,
        last_login_at=now,
        password_hash=_hash_password(password, salt_hex),
        password_salt=salt_hex,
    )
    repository.update_last_login_at(user.user_id, now)
    refreshed_user = repository.get_user_by_id(user.user_id)
    log_event(
        logger,
        "auth_register_success",
        user_id=refreshed_user.user_id,
        email=normalized_email,
        auth_provider=LOCAL_AUTH_PROVIDER,
    )
    return _issue_session(refreshed_user)


def login_user(email: str, password: str) -> dict[str, object]:
    normalized_email, password = _validate_credentials(email, password)
    repository = get_auth_repository()
    user = repository.get_user_by_email(normalized_email)

    if user is None:
        log_event(
            logger,
            "auth_login_failure",
            level=logging.WARNING,
            email=normalized_email,
            error_type="user_not_found",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    expected_hash = _hash_password(password, user.password_salt)
    if not hmac.compare_digest(expected_hash, user.password_hash):
        log_event(
            logger,
            "auth_login_failure",
            level=logging.WARNING,
            user_id=user.user_id,
            email=normalized_email,
            error_type="invalid_password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    now = _utc_now_iso()
    repository.update_last_login_at(user.user_id, now)
    refreshed_user = repository.get_user_by_id(user.user_id)
    bind_context(user_id=refreshed_user.user_id)
    log_event(
        logger,
        "auth_login_success",
        user_id=refreshed_user.user_id,
        email=refreshed_user.email,
        auth_provider=refreshed_user.auth_provider,
    )
    return _issue_session(refreshed_user)


def logout_user(token: str) -> None:
    if not token:
        return

    repository = get_auth_repository()
    token_hash = _hash_token(token)
    session = repository.get_session_by_token_hash(token_hash)
    repository.revoke_session(token_hash, _utc_now_iso())
    log_event(
        logger,
        "auth_logout",
        user_id=session.user_id if session is not None else None,
    )


def get_current_user_from_token(token: str) -> dict[str, str | None]:
    if not token:
        log_event(
            logger,
            "token_validation_failed",
            level=logging.WARNING,
            error_type="missing_token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repository = get_auth_repository()
    session = repository.get_session_by_token_hash(_hash_token(token))
    if session is None or session.revoked_at:
        log_event(
            logger,
            "token_validation_failed",
            level=logging.WARNING,
            error_type="invalid_or_revoked_session",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if session.expires_at <= _utc_now_iso():
        repository.revoke_session(session.token_hash, _utc_now_iso())
        log_event(
            logger,
            "token_validation_failed",
            level=logging.WARNING,
            user_id=session.user_id,
            error_type="session_expired",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = repository.get_user_by_id(session.user_id)
    if user is None:
        log_event(
            logger,
            "token_validation_failed",
            level=logging.WARNING,
            user_id=session.user_id,
            error_type="user_unavailable",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    bind_context(user_id=user.user_id)
    return _serialize_user(user)