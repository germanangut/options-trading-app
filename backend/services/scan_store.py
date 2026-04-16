"""Persistence and lookup for canonical scan results.

This store keeps the full canonical ScanResult payload so API routes can serve
stable scan-by-id responses without depending on the raw engine output shape.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from settings import get_settings


_LATEST_SCAN_RESULT: dict[str, Any] | None = None


def _scan_store_dir() -> Path:
    history_dir = Path(get_settings().get("history_dir", ".history"))
    store_dir = history_dir / "api_scans"
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def _scan_file_path(scan_id: str) -> Path:
    return _scan_store_dir() / f"{scan_id}.json"


def _latest_pointer_path() -> Path:
    return _scan_store_dir() / "latest_scan_id.txt"


def save_scan_result(scan_result: dict[str, Any]) -> dict[str, Any]:
    global _LATEST_SCAN_RESULT

    scan_id = ((scan_result or {}).get("scan_metadata") or {}).get("scan_id")
    if not scan_id:
        raise ValueError("Scan result is missing scan_metadata.scan_id.")

    file_path = _scan_file_path(scan_id)
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(scan_result, handle)

    _latest_pointer_path().write_text(scan_id, encoding="utf-8")
    _LATEST_SCAN_RESULT = scan_result
    return scan_result


def load_scan_result(scan_id: str) -> dict[str, Any] | None:
    if not scan_id:
        return None

    file_path = _scan_file_path(scan_id)
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def load_latest_scan_result() -> dict[str, Any] | None:
    global _LATEST_SCAN_RESULT

    if _LATEST_SCAN_RESULT is not None:
        return _LATEST_SCAN_RESULT

    pointer_path = _latest_pointer_path()
    if not pointer_path.exists():
        return None

    try:
        latest_scan_id = pointer_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None

    if not latest_scan_id:
        return None

    result = load_scan_result(latest_scan_id)
    _LATEST_SCAN_RESULT = result
    return result


def clear_scan_store() -> None:
    global _LATEST_SCAN_RESULT

    store_dir = _scan_store_dir()
    for file_path in store_dir.glob("*.json"):
        try:
            file_path.unlink()
        except OSError:
            pass

    try:
        _latest_pointer_path().unlink()
    except OSError:
        pass

    _LATEST_SCAN_RESULT = None
