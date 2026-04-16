from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

from backend.repositories.scan_repository import ScanRepository


SCAN_SCHEMA_VERSION = 1
STORAGE_BACKEND_SQLITE = "sqlite"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _completed_at(scan_result: dict[str, Any]) -> str:
    scan_metadata = (scan_result or {}).get("scan_metadata") or {}
    return scan_metadata.get("generated_at") or _utc_now_iso()


class SQLiteScanRepository(ScanRepository):
    """SQLite-backed persistence for canonical scan results.

    SQLite is the first durable backend. A future cloud database should replace
    this implementation behind the repository contract rather than changing
    callers in the service or trading layers.
    """

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
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id TEXT PRIMARY KEY,
                    generated_at TEXT NOT NULL,
                    stored_at TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1,
                    storage_backend TEXT NOT NULL DEFAULT 'sqlite',
                    owner_user_id TEXT,
                    profile TEXT,
                    ticker_group TEXT,
                    scan_result_json TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(scans)").fetchall()
            }
            if "schema_version" not in columns:
                connection.execute(
                    "ALTER TABLE scans ADD COLUMN schema_version INTEGER NOT NULL DEFAULT 1"
                )
            if "storage_backend" not in columns:
                connection.execute(
                    "ALTER TABLE scans ADD COLUMN storage_backend TEXT NOT NULL DEFAULT 'sqlite'"
                )
            if "owner_user_id" not in columns:
                connection.execute(
                    "ALTER TABLE scans ADD COLUMN owner_user_id TEXT"
                )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scans_latest_ordering
                ON scans (generated_at DESC, stored_at DESC, scan_id DESC)
                """
            )

    def _normalize_scan_result(
        self,
        scan_result: dict[str, Any],
        *,
        stored_at: str,
        schema_version: int = SCAN_SCHEMA_VERSION,
        storage_backend: str = STORAGE_BACKEND_SQLITE,
        owner_user_id: str | None = None,
    ) -> dict[str, Any]:
        normalized = deepcopy(scan_result)

        scan_metadata = normalized.get("scan_metadata")
        if not isinstance(scan_metadata, dict):
            scan_metadata = {}
            normalized["scan_metadata"] = scan_metadata

        summary = normalized.get("summary")
        normalized["summary"] = summary if isinstance(summary, dict) else {}

        for key in ("qualified_trades", "alerts", "near_miss_trades", "ticker_diagnostics"):
            value = normalized.get(key)
            normalized[key] = value if isinstance(value, list) else []

        for key in ("portfolio_summary", "history_context", "daily_summary", "diagnostics"):
            value = normalized.get(key)
            normalized[key] = value if isinstance(value, dict) else {}

        storage_metadata = normalized.get("storage_metadata")
        if not isinstance(storage_metadata, dict):
            storage_metadata = {}

        storage_metadata.update(
            {
                "schema_version": schema_version,
                "stored_at": stored_at,
                "storage_backend": storage_backend,
            }
        )
        if owner_user_id is not None:
            storage_metadata["user_id"] = owner_user_id
        normalized["storage_metadata"] = storage_metadata

        return normalized

    def _deserialize_scan(self, row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None

        try:
            payload = json.loads(row["scan_result_json"])
        except (TypeError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None

        return self._normalize_scan_result(
            payload,
            stored_at=row["stored_at"],
            schema_version=row["schema_version"],
            storage_backend=row["storage_backend"],
            owner_user_id=row["owner_user_id"],
        )

    def save_scan(
        self,
        scan_result: dict[str, Any],
        *,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        scan_metadata = (scan_result or {}).get("scan_metadata") or {}
        scan_id = scan_metadata.get("scan_id")
        generated_at = _completed_at(scan_result)

        if not scan_id:
            raise ValueError("Scan result is missing scan_metadata.scan_id.")

        stored_at = _utc_now_iso()
        owner_user_id = user_id or ((scan_result or {}).get("storage_metadata") or {}).get("user_id")
        normalized_scan_result = self._normalize_scan_result(
            scan_result,
            stored_at=stored_at,
            owner_user_id=owner_user_id,
        )
        payload_json = json.dumps(normalized_scan_result)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scans (
                    scan_id,
                    generated_at,
                    stored_at,
                    schema_version,
                    storage_backend,
                    owner_user_id,
                    profile,
                    ticker_group,
                    scan_result_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scan_id) DO UPDATE SET
                    generated_at = excluded.generated_at,
                    stored_at = excluded.stored_at,
                    schema_version = excluded.schema_version,
                    storage_backend = excluded.storage_backend,
                    owner_user_id = excluded.owner_user_id,
                    profile = excluded.profile,
                    ticker_group = excluded.ticker_group,
                    scan_result_json = excluded.scan_result_json
                """,
                (
                    scan_id,
                    generated_at,
                    stored_at,
                    SCAN_SCHEMA_VERSION,
                    STORAGE_BACKEND_SQLITE,
                    owner_user_id,
                    scan_metadata.get("profile"),
                    scan_metadata.get("ticker_group"),
                    payload_json,
                ),
            )

        return normalized_scan_result

    def get_scan(
        self,
        scan_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not scan_id:
            return None

        query = """
            SELECT scan_result_json, stored_at, schema_version, storage_backend, owner_user_id
            FROM scans
            WHERE scan_id = ?
        """
        parameters: tuple[Any, ...] = (scan_id,)
        if user_id is not None:
            query = f"{query} AND owner_user_id = ?"
            parameters = (scan_id, user_id)

        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()

        return self._deserialize_scan(row)

    def get_latest_scan(self, *, user_id: str | None = None) -> dict[str, Any] | None:
        query = """
            SELECT scan_result_json, stored_at, schema_version, storage_backend, owner_user_id
            FROM scans
        """
        parameters: tuple[Any, ...] = ()
        if user_id is not None:
            query = f"{query} WHERE owner_user_id = ?"
            parameters = (user_id,)
        query = (
            f"{query} ORDER BY COALESCE(generated_at, stored_at) DESC, stored_at DESC, scan_id DESC"
        )

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        for row in rows:
            scan = self._deserialize_scan(row)
            if scan is not None:
                return scan

        return None

    def list_scans(
        self,
        *,
        limit: int | None = None,
        newest_first: bool = True,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        order = "DESC" if newest_first else "ASC"
        query = "SELECT scan_result_json, stored_at, schema_version, storage_backend, owner_user_id FROM scans"
        parameters: tuple[Any, ...] = ()
        if user_id is not None:
            query = f"{query} WHERE owner_user_id = ?"
            parameters = (user_id,)
        query = (
            f"{query} ORDER BY COALESCE(generated_at, stored_at) {order}, stored_at {order}, scan_id {order}"
        )

        if isinstance(limit, int) and limit > 0:
            query = f"{query} LIMIT ?"
            parameters = (*parameters, limit)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        scans = []
        for row in rows:
            scan = self._deserialize_scan(row)
            if scan is not None:
                scans.append(scan)

        return scans

    def get_trade(
        self,
        scan_id: str,
        trade_id: str,
        *,
        user_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not scan_id or not trade_id:
            return None

        scan_result = self.get_scan(scan_id, user_id=user_id)
        if not scan_result:
            return None

        for collection_name in ("qualified_trades", "alerts", "near_miss_trades"):
            for trade in scan_result.get(collection_name, []) or []:
                if trade.get("trade_id") == trade_id:
                    return trade

        return None

    def clear(self, *, user_id: str | None = None) -> None:
        with self._connect() as connection:
            if user_id is None:
                connection.execute("DELETE FROM scans")
            else:
                connection.execute(
                    "DELETE FROM scans WHERE owner_user_id = ?",
                    (user_id,),
                )
