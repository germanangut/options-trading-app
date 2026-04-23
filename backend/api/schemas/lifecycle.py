from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


LifecycleState = Literal[
    "new",
    "saved",
    "watching",
    "execution_ready",
    "paper_submitted",
    "paper_filled",
    "paper_closed",
    "dismissed",
]


class TradeLifecycleRecordResponse(BaseModel):
    trade_id: str
    lifecycle_state: LifecycleState
    state_updated_at: str | None = None
    note: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_scan_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    is_default: bool = False


class TradeLifecycleListResponse(BaseModel):
    items: list[TradeLifecycleRecordResponse]


class TradeLifecycleUpsertBody(BaseModel):
    lifecycle_state: LifecycleState | None = None
    note: str | None = None
    tags: list[str] | None = None
    source_scan_id: str | None = None
