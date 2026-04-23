"""Pydantic response schemas for the What-If Workbench API (PU-15B.4)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.api.schemas.payoff import PayoffAnalysisResponse


class WorkbenchScenarioResponse(BaseModel):
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
    payoff: PayoffAnalysisResponse | None = None


class WorkbenchComparisonResponse(BaseModel):
    delta_net_credit: float
    delta_max_profit: float
    delta_max_loss: float
    delta_breakeven: float
    delta_spread_width: float
    risk_reward_ratio: float | None = None
    delta_risk_reward_ratio: float | None = None
    summary: str


class WorkbenchResultResponse(BaseModel):
    scan_id: str
    trade_id: str
    strategy_key: str
    underlying_price_reference: float
    ticker: str | None = None

    strike_shift: str
    width_adjustment: str

    baseline: WorkbenchScenarioResponse
    scenario: WorkbenchScenarioResponse | None = None
    comparison: WorkbenchComparisonResponse | None = None
    unavailable_reason: str | None = None

    # Available control options with display labels (sent once, avoids hardcoding in frontend)
    strike_shift_options: list[dict] = Field(default_factory=list)
    width_options: list[dict] = Field(default_factory=list)
