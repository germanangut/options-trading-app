"""Pydantic response schemas for PU-15B.5 delta-neutral exploration."""

from __future__ import annotations

from pydantic import BaseModel

from backend.api.schemas.payoff import PayoffAnalysisResponse


class DeltaNeutralScenarioResponse(BaseModel):
    strategy_key: str
    ticker: str | None = None
    short_strike: float
    long_strike: float
    expiration_date: str | None = None
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven: float
    label: str
    is_credit_estimated: bool
    net_delta: float
    payoff: PayoffAnalysisResponse | None = None


class DeltaNeutralComparisonResponse(BaseModel):
    baseline_net_delta: float
    candidate_net_delta: float
    delta_reduction: float
    delta_reduction_pct: float
    delta_max_profit: float
    delta_max_loss: float
    delta_breakeven: float
    summary: str


class DeltaNeutralExplorationResponse(BaseModel):
    scan_id: str
    trade_id: str
    baseline_trade_id: str | None = None
    strategy_key: str
    ticker: str | None = None
    underlying_price_reference: float

    baseline: DeltaNeutralScenarioResponse
    neutral_candidate_available: bool
    neutral_candidate: DeltaNeutralScenarioResponse | None = None
    comparison: DeltaNeutralComparisonResponse | None = None

    rationale: str
    limitation_note: str | None = None
    unavailable_reason: str | None = None
