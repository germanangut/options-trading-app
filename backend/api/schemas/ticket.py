from __future__ import annotations

from typing import Literal
from typing import Any

from pydantic import BaseModel, Field


ExecutionStatus = Literal[
    "draft",
    "ready",
    "submitted",
    "accepted",
    "rejected",
    "canceled",
    "filled",
]

OrderIntent = Literal["open_credit", "open_debit", "other"]


class ExecutionTicketResponse(BaseModel):
    ticket_id: str
    trade_id: str
    source_scan_id: str | None = None

    # Frozen snapshot
    ticker: str
    strategy_key: str
    strategy_label: str
    directional_bias: str | None = None
    expiration_date: str | None = None
    short_strike: float | None = None
    long_strike: float | None = None
    underlying_price_at_creation: float | None = None
    net_credit_estimate: float | None = None
    max_risk_estimate: float | None = None
    adjusted_score_at_creation: float | None = None

    # Execution parameters
    quantity: int = 1
    order_intent: OrderIntent = "open_credit"
    execution_status: ExecutionStatus = "draft"
    note: str | None = None

    # Audit
    created_at: str | None = None
    updated_at: str | None = None
    broker_order_id: str | None = None
    broker_status_raw: str | None = None
    broker_submitted_at: str | None = None
    broker_updated_at: str | None = None
    last_submission_payload: dict[str, Any] | None = None
    last_submission_response: dict[str, Any] | None = None
    submission_error_message: str | None = None


class ExecutionTicketListResponse(BaseModel):
    items: list[ExecutionTicketResponse]


class CreateExecutionTicketBody(BaseModel):
    trade_id: str
    source_scan_id: str | None = None

    # Frozen snapshot fields — captured by the frontend at creation time
    ticker: str
    strategy_key: str
    strategy_label: str
    directional_bias: str | None = None
    expiration_date: str | None = None
    short_strike: float | None = None
    long_strike: float | None = None
    underlying_price_at_creation: float | None = None
    net_credit_estimate: float | None = None
    max_risk_estimate: float | None = None
    adjusted_score_at_creation: float | None = None

    quantity: int = Field(default=1, ge=1, le=100)
    order_intent: OrderIntent = "open_credit"
    note: str | None = None


class PatchExecutionTicketBody(BaseModel):
    quantity: int | None = Field(default=None, ge=1, le=100)
    note: str | None = None
    clear_note: bool = False
    execution_status: Literal["draft", "ready"] | None = None
