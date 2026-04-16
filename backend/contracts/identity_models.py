from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    email: str
    auth_provider: str
    created_at: str
    last_login_at: str | None
    password_hash: str
    password_salt: str


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    user_id: str
    token_hash: str
    created_at: str
    expires_at: str
    revoked_at: str | None


@dataclass(frozen=True)
class BrokerConnectionRecord:
    connection_id: str
    user_id: str
    broker_provider: str
    broker_account_label: str
    status: str
    created_at: str
    last_validated_at: str | None