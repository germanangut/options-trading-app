"""Workbench domain models for PU-15B.4 — What-If Strategy Workbench.

Provides the contract types for controlled what-if scenario exploration
on top of a baseline spread trade. These are analytical-only models;
they do not affect scan qualification, lifecycle, or execution workflow.

Supported controls (phase 1):
- Short strike shift: further_otm | baseline | closer_atm
- Width adjustment: narrower | baseline | wider

Delta-neutral and expiration-shift remain explicitly deferred.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.contracts.payoff_models import PayoffAnalysis


SUPPORTED_WORKBENCH_STRATEGIES: tuple[str, ...] = (
    "bull_put_spread",
    "bear_call_spread",
)

STRIKE_SHIFT_OPTIONS: tuple[str, ...] = (
    "further_otm",
    "baseline",
    "closer_atm",
)

WIDTH_OPTIONS: tuple[str, ...] = (
    "narrower",
    "baseline",
    "wider",
)

STRIKE_SHIFT_LABELS: dict[str, str] = {
    "further_otm": "Further out-of-the-money",
    "baseline": "Baseline",
    "closer_atm": "Closer for more credit",
}

WIDTH_LABELS: dict[str, str] = {
    "narrower": "Narrower spread",
    "baseline": "Baseline",
    "wider": "Wider spread",
}

# Strike increment used for what-if shifts.
# Keeps scenarios conservative and deterministic.
_STRIKE_STEP = 1.0


@dataclass(frozen=True)
class WorkbenchParams:
    """User-selected what-if parameter choices.

    All values are constrained enum-like strings, not free-form numbers.
    Backend owns the mapping from these choices to actual strikes/credits.
    """

    strike_shift: str  # "further_otm" | "baseline" | "closer_atm"
    width_adjustment: str  # "narrower" | "baseline" | "wider"


@dataclass(frozen=True)
class WorkbenchScenarioSummary:
    """A single resolved spread scenario (baseline or what-if).

    is_credit_estimated=True whenever credit is derived by moneyness
    approximation rather than from real chain data.
    """

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
    payoff: PayoffAnalysis | None = None


@dataclass(frozen=True)
class WorkbenchComparison:
    """Delta-to-baseline summary attached to a what-if scenario."""

    delta_net_credit: float
    delta_max_profit: float
    delta_max_loss: float
    delta_breakeven: float
    delta_spread_width: float
    risk_reward_ratio: float | None
    delta_risk_reward_ratio: float | None
    summary: str


@dataclass(frozen=True)
class WorkbenchResult:
    """Full workbench result: baseline + current scenario + diagnostics."""

    scan_id: str
    trade_id: str
    strategy_key: str
    underlying_price_reference: float
    ticker: str | None

    # Selected controls
    strike_shift: str
    width_adjustment: str

    # Resolved scenarios
    baseline: WorkbenchScenarioSummary
    scenario: WorkbenchScenarioSummary | None

    # Comparison when scenario is available
    comparison: WorkbenchComparison | None

    # Human-readable explanation when scenario is unavailable
    unavailable_reason: str | None
