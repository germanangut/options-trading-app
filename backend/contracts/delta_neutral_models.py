"""Delta-neutral exploration contracts for PU-15B.5.

This module defines analytical-only model types for comparing a directional
baseline spread against a reduced-directionality candidate.

Scope:
- Supported baseline strategies: bull_put_spread, bear_call_spread
- No execution workflow coupling
- No freeform multi-leg strategy builder
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.contracts.payoff_models import PayoffAnalysis


SUPPORTED_DELTA_NEUTRAL_STRATEGIES: tuple[str, ...] = (
    "bull_put_spread",
    "bear_call_spread",
)


@dataclass(frozen=True)
class DeltaNeutralScenario:
    strategy_key: str
    ticker: str | None
    short_strike: float
    long_strike: float
    expiration_date: str | None
    net_credit: float
    spread_width: float
    max_profit: float
    max_loss: float
    breakeven: float
    label: str
    is_credit_estimated: bool
    net_delta: float
    payoff: PayoffAnalysis | None = None


@dataclass(frozen=True)
class DeltaNeutralComparison:
    baseline_net_delta: float
    candidate_net_delta: float
    delta_reduction: float
    delta_reduction_pct: float
    delta_max_profit: float
    delta_max_loss: float
    delta_breakeven: float
    summary: str


@dataclass(frozen=True)
class DeltaNeutralExploration:
    scan_id: str
    trade_id: str
    baseline_trade_id: str | None
    strategy_key: str
    ticker: str | None
    underlying_price_reference: float

    baseline: DeltaNeutralScenario
    neutral_candidate_available: bool
    neutral_candidate: DeltaNeutralScenario | None
    comparison: DeltaNeutralComparison | None

    rationale: str
    limitation_note: str | None
    unavailable_reason: str | None
