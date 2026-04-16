from __future__ import annotations

from pathlib import Path
import sqlite3

from backend.contracts.identity_models import (
    BrokerConnectionRecord,
    SessionRecord,
    UserRecord,
)
from backend.repositories.auth_repository import AuthRepository


class SQLiteAuthRepository(AuthRepository):
    """SQLite-backed identity store for local app auth foundations."""

    def __init__(self, database_path: str | Path):
        self._database_path = Path(database_path)
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    auth_provider TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS broker_connections (
                    connection_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    broker_provider TEXT NOT NULL,
                    broker_account_label TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_validated_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_token_hash
                ON auth_sessions (token_hash)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id
                ON auth_sessions (user_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_broker_connections_user_id
                ON broker_connections (user_id)
                """
            )

    def _row_to_user(self, row: sqlite3.Row | None) -> UserRecord | None:
        if row is None:
            return None

        return UserRecord(
            user_id=row["user_id"],
            email=row["email"],
            auth_provider=row["auth_provider"],
            created_at=row["created_at"],
            last_login_at=row["last_login_at"],
            password_hash=row["password_hash"],
            password_salt=row["password_salt"],
        )

    def _row_to_session(self, row: sqlite3.Row | None) -> SessionRecord | None:
        if row is None:
            return None

        return SessionRecord(
            session_id=row["session_id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )

    def _row_to_broker_connection(
        self,
        row: sqlite3.Row | None,
    ) -> BrokerConnectionRecord | None:
        if row is None:
            return None

        return BrokerConnectionRecord(
            connection_id=row["connection_id"],
            user_id=row["user_id"],
            broker_provider=row["broker_provider"],
            broker_account_label=row["broker_account_label"],
            status=row["status"],
            created_at=row["created_at"],
            last_validated_at=row["last_validated_at"],
        )

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
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (
                    user_id,
                    email,
                    auth_provider,
                    created_at,
                    last_login_at,
                    password_hash,
                    password_salt
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    email,
                    auth_provider,
                    created_at,
                    last_login_at,
                    password_hash,
                    password_salt,
                ),
            )

        return self.get_user_by_id(user_id)

    def get_user_by_email(self, email: str) -> UserRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,),
            ).fetchone()

        return self._row_to_user(row)

    def get_user_by_id(self, user_id: str) -> UserRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        return self._row_to_user(row)

    def update_last_login_at(self, user_id: str, last_login_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE users SET last_login_at = ? WHERE user_id = ?",
                (last_login_at, user_id),
            )

    def create_session(
        self,
        *,
        session_id: str,
        user_id: str,
        token_hash: str,
        created_at: str,
        expires_at: str,
    ) -> SessionRecord:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions (
                    session_id,
                    user_id,
                    token_hash,
                    created_at,
                    expires_at,
                    revoked_at
                )
                VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (session_id, user_id, token_hash, created_at, expires_at),
            )

        return self.get_session_by_token_hash(token_hash)

    def get_session_by_token_hash(self, token_hash: str) -> SessionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM auth_sessions WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()

        return self._row_to_session(row)

    def revoke_session(self, token_hash: str, revoked_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE auth_sessions SET revoked_at = ? WHERE token_hash = ?",
                (revoked_at, token_hash),
            )

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
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO broker_connections (
                    connection_id,
                    user_id,
                    broker_provider,
                    broker_account_label,
                    status,
                    created_at,
                    last_validated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    connection_id,
                    user_id,
                    broker_provider,
                    broker_account_label,
                    status,
                    created_at,
                    last_validated_at,
                ),
            )

        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM broker_connections WHERE connection_id = ?",
                (connection_id,),
            ).fetchone()

        return self._row_to_broker_connection(row)

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM auth_sessions")
            connection.execute("DELETE FROM broker_connections")
            connection.execute("DELETE FROM users")