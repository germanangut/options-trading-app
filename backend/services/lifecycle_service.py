from __future__ import annotations

from datetime import UTC, datetime

from backend.contracts.lifecycle_models import (
    DEFAULT_LIFECYCLE_STATE,
    VALID_LIFECYCLE_TRANSITIONS,
    is_valid_lifecycle_state,
)
from backend.repositories.factory import get_lifecycle_repository


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _normalized_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []

    cleaned: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        value = str(tag).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def _serialize_record(record, *, is_default: bool) -> dict[str, object]:
    return {
        "trade_id": record.trade_id,
        "lifecycle_state": record.lifecycle_state,
        "state_updated_at": record.state_updated_at,
        "note": record.note,
        "tags": list(record.tags or []),
        "source_scan_id": record.source_scan_id,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "is_default": is_default,
    }


def _build_default_lifecycle(trade_id: str) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "lifecycle_state": DEFAULT_LIFECYCLE_STATE,
        "state_updated_at": None,
        "note": None,
        "tags": [],
        "source_scan_id": None,
        "created_at": None,
        "updated_at": None,
        "is_default": True,
    }


def get_trade_lifecycle(trade_id: str, *, user_id: str) -> dict[str, object]:
    trade_id = (trade_id or "").strip()
    if not trade_id:
        raise ValueError("trade_id is required.")

    record = get_lifecycle_repository().get_trade_lifecycle(trade_id, user_id=user_id)
    if record is None:
        return _build_default_lifecycle(trade_id)

    return _serialize_record(record, is_default=False)


def list_trade_lifecycles(
    *,
    user_id: str,
    lifecycle_state: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    if lifecycle_state is not None and not is_valid_lifecycle_state(lifecycle_state):
        raise ValueError(f"Unsupported lifecycle_state '{lifecycle_state}'.")

    records = get_lifecycle_repository().list_trade_lifecycles(
        user_id=user_id,
        lifecycle_state=lifecycle_state,
        limit=limit,
    )
    return [_serialize_record(record, is_default=False) for record in records]


def upsert_trade_lifecycle(
    trade_id: str,
    *,
    user_id: str,
    lifecycle_state: str | None = None,
    note: str | None = None,
    tags: list[str] | None = None,
    source_scan_id: str | None = None,
) -> dict[str, object]:
    trade_id = (trade_id or "").strip()
    if not trade_id:
        raise ValueError("trade_id is required.")

    repository = get_lifecycle_repository()
    existing = repository.get_trade_lifecycle(trade_id, user_id=user_id)
    current_state = existing.lifecycle_state if existing is not None else DEFAULT_LIFECYCLE_STATE
    next_state = lifecycle_state or current_state

    if not is_valid_lifecycle_state(next_state):
        raise ValueError(f"Unsupported lifecycle_state '{next_state}'.")

    if next_state not in VALID_LIFECYCLE_TRANSITIONS.get(current_state, {current_state}):
        raise ValueError(
            f"Invalid lifecycle transition from '{current_state}' to '{next_state}'."
        )

    now = _utc_now_iso()
    merged_note = note if note is not None else (existing.note if existing is not None else None)
    merged_tags = (
        _normalized_tags(tags)
        if tags is not None
        else _normalized_tags(existing.tags if existing is not None else [])
    )
    merged_source_scan_id = (
        source_scan_id
        if source_scan_id is not None
        else (existing.source_scan_id if existing is not None else None)
    )
    state_updated_at = (
        now
        if existing is None or next_state != current_state
        else existing.state_updated_at
    )
    created_at = existing.created_at if existing is not None else now

    persisted = repository.upsert_trade_lifecycle(
        trade_id=trade_id,
        lifecycle_state=next_state,
        state_updated_at=state_updated_at,
        note=merged_note,
        tags=merged_tags,
        source_scan_id=merged_source_scan_id,
        created_at=created_at,
        updated_at=now,
        user_id=user_id,
    )
    return _serialize_record(persisted, is_default=False)
