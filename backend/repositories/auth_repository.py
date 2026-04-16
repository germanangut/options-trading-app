from __future__ import annotations

from abc import ABC, abstractmethod

from backend.contracts.identity_models import (
    BrokerConnectionRecord,
    SessionRecord,
    UserRecord,
)


class AuthRepository(ABC):
    """Storage abstraction for app-owned identity and session state."""

    @abstractmethod
    def create_user(
        self,
        *,
        user_id: str,
        email: str,
        auth_provider: str,
        created_at: str,
        last_login_at: str | None,
        password_hash: str,
        password_salt: str,
    ) -> UserRecord:
        """Persist a local app user."""

    @abstractmethod
    def get_user_by_email(self, email: str) -> UserRecord | None:
        """Load a user by normalized email."""

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        """Load a user by stable application user id."""

    @abstractmethod
    def update_last_login_at(self, user_id: str, last_login_at: str) -> None:
        """Update the timestamp of the user's most recent successful login."""

    @abstractmethod
    def create_session(
        self,
        *,
        session_id: str,
        user_id: str,
        token_hash: str,
        created_at: str,
        expires_at: str,
    ) -> SessionRecord:
        """Persist an application session token."""

    @abstractmethod
    def get_session_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        """Load the active session for a token hash, if any."""

    @abstractmethod
    def revoke_session(self, token_hash: str, revoked_at: str) -> None:
        """Invalidate an active session token."""

    @abstractmethod
    def create_broker_connection(
        self,
        *,
        connection_id: str,
        user_id: str,
        broker_provider: str,
        broker_account_label: str,
        status: str,
        created_at: str,
        last_validated_at: str | None,
    ) -> BrokerConnectionRecord:
        """Persist a future broker-connection seam separate from app auth."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all auth records. Intended for tests only."""