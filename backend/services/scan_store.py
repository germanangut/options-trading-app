"""Compatibility wrapper over the durable scan repository.

The service layer continues to import these functions while the actual storage
implementation lives behind the repository abstraction.
"""

from __future__ import annotations

from typing import Any

from backend.repositories.factory import get_scan_repository


def save_scan_result(
    scan_result: dict[str, Any],
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    return get_scan_repository().save_scan(scan_result, user_id=user_id)


def load_scan_result(scan_id: str, *, user_id: str | None = None) -> dict[str, Any] | None:
    return get_scan_repository().get_scan(scan_id, user_id=user_id)


def load_latest_scan_result(*, user_id: str | None = None) -> dict[str, Any] | None:
    return get_scan_repository().get_latest_scan(user_id=user_id)


def list_scan_results(
    *,
    limit: int | None = None,
    newest_first: bool = True,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    return get_scan_repository().list_scans(
        limit=limit,
        newest_first=newest_first,
        user_id=user_id,
    )


def load_trade_result(
    scan_id: str,
    trade_id: str,
    *,
    user_id: str | None = None,
) -> dict[str, Any] | None:
    return get_scan_repository().get_trade(scan_id, trade_id, user_id=user_id)


def clear_scan_store(*, user_id: str | None = None) -> None:
    get_scan_repository().clear(user_id=user_id)
