from __future__ import annotations

from pathlib import Path

from backend.repositories.sqlite_auth_repository import SQLiteAuthRepository
from backend.repositories.sqlite_lifecycle_repository import SQLiteLifecycleRepository
from backend.repositories.sqlite_scan_repository import SQLiteScanRepository
from settings import get_settings


def _default_scan_database_path() -> Path:
    settings = get_settings()
    configured_path = settings.get("scan_database_path")
    if configured_path:
        return Path(configured_path)

    history_dir = Path(settings.get("history_dir", ".history"))
    return history_dir / "scan_store.sqlite"


def get_scan_repository() -> SQLiteScanRepository:
    return SQLiteScanRepository(_default_scan_database_path())


def get_auth_repository() -> SQLiteAuthRepository:
    return SQLiteAuthRepository(_default_scan_database_path())


def get_lifecycle_repository() -> SQLiteLifecycleRepository:
    return SQLiteLifecycleRepository(_default_scan_database_path())