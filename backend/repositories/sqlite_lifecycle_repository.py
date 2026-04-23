from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from backend.contracts.lifecycle_models import TradeLifecycleRecord
from backend.repositories.lifecycle_repository import LifecycleRepository


class SQLiteLifecycleRepository(LifecycleRepository):
    """SQLite-backed persistence for user-managed trade lifecycle records."""

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
                CREATE TABLE IF NOT EXISTS trade_lifecycle (
                    owner_user_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    lifecycle_state TEXT NOT NULL,
                    state_updated_at TEXT NOT NULL,
                    note TEXT,
                    tags_json TEXT NOT NULL,
                    source_scan_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (owner_user_id, trade_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trade_lifecycle_owner_updated
                ON trade_lifecycle (owner_user_id, updated_at DESC, trade_id DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trade_lifecycle_owner_state
                ON trade_lifecycle (owner_user_id, lifecycle_state)
                """
            )

    def _row_to_record(self, row: sqlite3.Row | None) -> TradeLifecycleRecord | None:
        if row is None:
            return None

        tags: list[str]
        try:
            parsed = json.loads(row["tags_json"])
            if isinstance(parsed, list):
                tags = [str(item) for item in parsed]
            else:
                tags = []
        except (TypeError, json.JSONDecodeError):
            tags = []

        return TradeLifecycleRecord(
            owner_user_id=row["owner_user_id"],
            trade_id=row["trade_id"],
            lifecycle_state=row["lifecycle_state"],
            state_updated_at=row["state_updated_at"],
            note=row["note"],
            tags=tags,
            source_scan_id=row["source_scan_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_trade_lifecycle(
        self,
        trade_id: str,
        *,
        user_id: str,
    ) -> TradeLifecycleRecord | None:
        if not trade_id or not user_id:
            return None

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    owner_user_id,
                    trade_id,
                    lifecycle_state,
                    state_updated_at,
                    note,
                    tags_json,
                    source_scan_id,
                    created_at,
                    updated_at
                FROM trade_lifecycle
                WHERE owner_user_id = ? AND trade_id = ?
                """,
                (user_id, trade_id),
            ).fetchone()

        return self._row_to_record(row)

    def upsert_trade_lifecycle(
        self,
        *,
        trade_id: str,
        lifecycle_state: str,
        state_updated_at: str,
        note: str | None,
        tags: list[str],
        source_scan_id: str | None,
        created_at: str,
        updated_at: str,
        user_id: str,
    ) -> TradeLifecycleRecord:
        tags_json = json.dumps(list(tags or []))

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO trade_lifecycle (
                    owner_user_id,
                    trade_id,
                    lifecycle_state,
                    state_updated_at,
                    note,
                    tags_json,
                    source_scan_id,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(owner_user_id, trade_id) DO UPDATE SET
                    lifecycle_state = excluded.lifecycle_state,
                    state_updated_at = excluded.state_updated_at,
                    note = excluded.note,
                    tags_json = excluded.tags_json,
                    source_scan_id = excluded.source_scan_id,
                    updated_at = excluded.updated_at
                """,
                (
                    user_id,
                    trade_id,
                    lifecycle_state,
                    state_updated_at,
                    note,
                    tags_json,
                    source_scan_id,
                    created_at,
                    updated_at,
                ),
            )

        record = self.get_trade_lifecycle(trade_id, user_id=user_id)
        if record is None:
            raise RuntimeError("Lifecycle record was not persisted.")
        return record

    def list_trade_lifecycles(
        self,
        *,
        user_id: str,
        lifecycle_state: str | None = None,
        limit: int | None = None,
    ) -> list[TradeLifecycleRecord]:
        if not user_id:
            return []

        query = """
            SELECT
                owner_user_id,
                trade_id,
                lifecycle_state,
                state_updated_at,
                note,
                tags_json,
                source_scan_id,
                created_at,
                updated_at
            FROM trade_lifecycle
            WHERE owner_user_id = ?
        """
        params: list[object] = [user_id]
        if lifecycle_state:
            query = f"{query} AND lifecycle_state = ?"
            params.append(lifecycle_state)

        query = f"{query} ORDER BY updated_at DESC, trade_id DESC"
        if isinstance(limit, int) and limit > 0:
            query = f"{query} LIMIT ?"
            params.append(limit)

        with self._connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()

        return [record for row in rows if (record := self._row_to_record(row)) is not None]

    def clear(self, *, user_id: str | None = None) -> None:
        with self._connect() as connection:
            if user_id is None:
                connection.execute("DELETE FROM trade_lifecycle")
            else:
                connection.execute(
                    "DELETE FROM trade_lifecycle WHERE owner_user_id = ?",
                    (user_id,),
                )
