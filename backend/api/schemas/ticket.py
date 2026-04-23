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


class PaperPositionRow(BaseModel):
    symbol: str | None = None
    ticker: str | None = None
    qty: int | None = None
    side: str | None = None
    avg_entry_price: float | None = None
    market_value: float | None = None
    cost_basis: float | None = None
    unrealized_pl: float | None = None
    unrealized_plpc: float | None = None
    realized_pl: float | None = None
    broker_updated_at: str | None = None
    linked_ticket_id: str | None = None
    strategy_label: str | None = None
    directional_bias: str | None = None
    ticket_execution_status: ExecutionStatus | None = None
    estimated_credit_or_debit: float | None = None


class PaperOrderHistoryRow(BaseModel):
    broker_order_id: str | None = None
    symbol: str | None = None
    status: str | None = None
    order_type: str | None = None
    side: str | None = None
    qty: int | None = None
    filled_qty: int | None = None
    filled_avg_price: float | None = None
    submitted_at: str | None = None
    updated_at: str | None = None


class PaperDashboardSummary(BaseModel):
    pending_count: int
    open_positions_count: int
    closed_count: int
    recent_orders_count: int


class PaperDashboardDataSource(BaseModel):
    mode: str
    app_history_source: str
    broker_live_data_available: bool
    broker_live_data_warning: str | None = None
    status_refresh_attempted: bool
    status_refresh_errors: list[str]
    generated_at: str


class PaperDashboardResponse(BaseModel):
    pending_orders: list[ExecutionTicketResponse]
    open_positions: list[PaperPositionRow]
    closed_trades: list[ExecutionTicketResponse]
    recent_orders: list[PaperOrderHistoryRow]
    summary: PaperDashboardSummary
    data_source: PaperDashboardDataSource
