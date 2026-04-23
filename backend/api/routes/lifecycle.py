"""Lifecycle routes for user-managed trade workflow state."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.dependencies.auth import require_current_user
from backend.api.schemas.lifecycle import (
    TradeLifecycleListResponse,
    TradeLifecycleRecordResponse,
    TradeLifecycleUpsertBody,
)
from backend.services.lifecycle_service import (
    get_trade_lifecycle,
    list_trade_lifecycles,
    upsert_trade_lifecycle,
)


router = APIRouter(prefix="/api/v1/lifecycle", tags=["lifecycle"])


@router.get("", response_model=TradeLifecycleListResponse)
def list_lifecycle_records(
    lifecycle_state: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=500),
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, list[dict[str, object]]]:
    try:
        items = list_trade_lifecycles(
            user_id=current_user["user_id"],
            lifecycle_state=lifecycle_state,
            limit=limit,
        )
        return {"items": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{trade_id}", response_model=TradeLifecycleRecordResponse)
def get_lifecycle_record(
    trade_id: str,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    try:
        return get_trade_lifecycle(trade_id, user_id=current_user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{trade_id}", response_model=TradeLifecycleRecordResponse)
@router.patch("/{trade_id}", response_model=TradeLifecycleRecordResponse)
def upsert_lifecycle_record(
    trade_id: str,
    payload: TradeLifecycleUpsertBody,
    current_user: dict[str, str | None] = Depends(require_current_user),
) -> dict[str, object]:
    if (
        payload.lifecycle_state is None
        and payload.note is None
        and payload.tags is None
        and payload.source_scan_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one lifecycle field is required for update.",
        )

    try:
        return upsert_trade_lifecycle(
            trade_id,
            user_id=current_user["user_id"],
            lifecycle_state=payload.lifecycle_state,
            note=payload.note,
            tags=payload.tags,
            source_scan_id=payload.source_scan_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
