"""Workbench generation service for PU-15B.4 — What-If Strategy Workbench.

Generates a single what-if scenario from controlled, user-selected
parameter choices (strike_shift, width_adjustment) relative to a baseline
spread trade (bull_put_spread or bear_call_spread).

Design rules:
- All strikes are derived from the baseline trade; never invented.
- Credits are estimated using the same moneyness-ratio formula as the
  variant service; is_credit_estimated=True always on non-baseline scenarios.
- If a scenario cannot be built cleanly, an unavailable result is returned
  with a brief user-facing explanation.
- Delta-neutral is explicitly NOT part of this phase (PU-15B.4).
- Expiration-shift is deferred; only strike_shift and width_adjustment
  controls are implemented here.
"""

from __future__ import annotations

from typing import Any

from backend.contracts.payoff_models import PayoffInput
from backend.contracts.workbench_models import (
    SUPPORTED_WORKBENCH_STRATEGIES,
    WorkbenchComparison,
    WorkbenchParams,
    WorkbenchResult,
    WorkbenchScenarioSummary,
    _STRIKE_STEP,
)
from backend.services.payoff_engine import calculate_payoff


# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------

_MIN_CREDIT = 0.01
_MIN_OTM_BUFFER = 0.01


# ---------------------------------------------------------------------------
# Helpers — shared with variant service but kept local to avoid coupling
# ---------------------------------------------------------------------------

def _normalize_strategy_key(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    alias_map = {
        "bull_put_spread": "bull_put_spread",
        "bull_put": "bull_put_spread",
        "bear_call_spread": "bear_call_spread",
        "bear_call": "bear_call_spread",
    }
    return alias_map.get(normalized, normalized)


def _estimate_credit(
    baseline_credit: float,
    baseline_otm_buffer: float,
    new_otm_buffer: float,
    spread_width: float,
) -> float | None:
    """Moneyness-ratio credit estimate for a shifted scenario.

    new_credit ≈ baseline_credit * (baseline_otm_buffer / new_otm_buffer)

    Returns None when the result is invalid (zero denominator, below
    minimum threshold, or ≥ spread width).
    """
    if new_otm_buffer < _MIN_OTM_BUFFER:
        return None
    if baseline_otm_buffer < _MIN_OTM_BUFFER:
        return None

    estimated = round(baseline_credit * (baseline_otm_buffer / new_otm_buffer), 3)
    if estimated < _MIN_CREDIT:
        return None
    if estimated >= spread_width:
        estimated = round(spread_width * 0.90, 3)
        if estimated < _MIN_CREDIT:
            return None
    return estimated


def _breakeven_for(strategy_key: str, short_strike: float, net_credit: float) -> float:
    if strategy_key == "bull_put_spread":
        return round(short_strike - net_credit, 4)
    return round(short_strike + net_credit, 4)


def _build_payoff(
    strategy_key: str,
    ticker: str | None,
    underlying_price: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
) -> Any:
    try:
        payoff_input = PayoffInput(
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying_price,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
        )
        return calculate_payoff(payoff_input)
    except (ValueError, TypeError):
        return None


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


# ---------------------------------------------------------------------------
# Scenario summary builder
# ---------------------------------------------------------------------------

def _build_scenario(
    *,
    strategy_key: str,
    ticker: str | None,
    underlying_price: float,
    short_strike: float,
    long_strike: float,
    expiration_date: str | None,
    net_credit: float,
    is_credit_estimated: bool,
    label: str,
) -> WorkbenchScenarioSummary | None:
    """Construct a WorkbenchScenarioSummary; returns None if invalid."""
    spread_width = round(abs(short_strike - long_strike), 4)
    if spread_width <= 0:
        return None
    if net_credit < _MIN_CREDIT or net_credit >= spread_width:
        return None
    if short_strike <= 0 or long_strike <= 0:
        return None

    max_profit = round(net_credit * 100, 2)
    max_loss = round((spread_width - net_credit) * 100, 2)
    breakeven = _breakeven_for(strategy_key, short_strike, net_credit)

    payoff = _build_payoff(
        strategy_key, ticker, underlying_price, short_strike, long_strike, net_credit
    )

    return WorkbenchScenarioSummary(
        strategy_key=strategy_key,
        ticker=ticker,
        short_strike=short_strike,
        long_strike=long_strike,
        expiration_date=expiration_date,
        net_credit=net_credit,
        spread_width=spread_width,
        max_profit=max_profit,
        max_loss=max_loss,
        breakeven=breakeven,
        label=label,
        is_credit_estimated=is_credit_estimated,
        payoff=payoff,
    )


def _build_comparison(
    scenario: WorkbenchScenarioSummary,
    baseline: WorkbenchScenarioSummary,
    strategy_key: str,
) -> WorkbenchComparison:
    delta_credit = round(scenario.net_credit - baseline.net_credit, 4)
    delta_profit = round(scenario.max_profit - baseline.max_profit, 2)
    delta_loss = round(scenario.max_loss - baseline.max_loss, 2)
    delta_breakeven = round(scenario.breakeven - baseline.breakeven, 4)
    delta_width = round(scenario.spread_width - baseline.spread_width, 4)

    baseline_rr = _safe_ratio(baseline.max_profit, baseline.max_loss)
    scenario_rr = _safe_ratio(scenario.max_profit, scenario.max_loss)
    delta_rr: float | None = None
    if scenario_rr is not None and baseline_rr is not None:
        delta_rr = round(scenario_rr - baseline_rr, 4)

    # Build a single human-readable summary line
    parts: list[str] = []
    if delta_credit > 0:
        parts.append(f"Higher credit (+${abs(delta_credit):.2f})")
    elif delta_credit < 0:
        parts.append(f"Lower credit (−${abs(delta_credit):.2f})")
    else:
        parts.append("Same credit as baseline")

    if delta_width > 0:
        parts.append("wider spread")
    elif delta_width < 0:
        parts.append("narrower spread")

    # Directional breakeven story
    if strategy_key == "bull_put_spread":
        if delta_breakeven < 0:
            parts.append("more room before loss")
        elif delta_breakeven > 0:
            parts.append("tighter room before loss")
    else:  # bear_call_spread
        if delta_breakeven > 0:
            parts.append("more room before loss")
        elif delta_breakeven < 0:
            parts.append("tighter room before loss")

    summary = "; ".join(parts).capitalize() if parts else "No structural change from baseline."

    return WorkbenchComparison(
        delta_net_credit=delta_credit,
        delta_max_profit=delta_profit,
        delta_max_loss=delta_loss,
        delta_breakeven=delta_breakeven,
        delta_spread_width=delta_width,
        risk_reward_ratio=scenario_rr,
        delta_risk_reward_ratio=delta_rr,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Strike and width resolution — bull put spread
# ---------------------------------------------------------------------------

def _resolve_bull_put(
    *,
    underlying: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
    spread_width: float,
    ticker: str | None,
    expiration_date: str | None,
    params: WorkbenchParams,
) -> tuple[WorkbenchScenarioSummary | None, str | None]:
    """Resolve the what-if scenario for a bull put spread.

    Returns (scenario, unavailable_reason). Exactly one will be non-None
    unless params are both 'baseline'.
    """
    strategy_key = "bull_put_spread"
    # OTM buffer = how far the short put is below the underlying
    otm_buffer = underlying - short_strike  # positive = OTM

    # --- Compute new short strike from strike_shift ---
    if params.strike_shift == "further_otm":
        new_short = round(short_strike - _STRIKE_STEP, 2)
        shift_delta = -_STRIKE_STEP
        shift_label = f"Short strike shifted further OTM to {new_short:.2f}"
    elif params.strike_shift == "closer_atm":
        new_short = round(short_strike + _STRIKE_STEP, 2)
        shift_delta = +_STRIKE_STEP
        shift_label = f"Short strike moved closer to ATM ({new_short:.2f})"
    else:
        new_short = short_strike
        shift_delta = 0.0
        shift_label = "Short strike unchanged"

    # Validate short strike remains OTM for bull put (must be below underlying)
    if new_short >= underlying:
        return None, f"No clean alternative: moving the short strike to {new_short:.2f} would place it at or above the current underlying ({underlying:.2f}), making this no longer an OTM spread."

    if new_short <= 0:
        return None, "No clean alternative: the adjusted short strike would fall to or below zero."

    # --- Compute new long strike from width_adjustment ---
    # For bull put, long_strike < short_strike; width = short_strike - long_strike
    if params.width_adjustment == "narrower":
        new_width = max(spread_width - _STRIKE_STEP, _STRIKE_STEP)
        if new_width <= 0:
            return None, "No clean alternative: narrowing the spread further would collapse the width to zero."
        new_long = round(new_short - new_width, 2)
        width_label = "Spread narrowed"
    elif params.width_adjustment == "wider":
        new_width = spread_width + _STRIKE_STEP
        new_long = round(new_short - new_width, 2)
        width_label = "Spread widened"
    else:
        new_long = round(new_short - spread_width, 2)
        new_width = spread_width
        width_label = "Spread width unchanged"

    if new_long <= 0:
        return None, f"No clean alternative: the adjusted long strike would fall to or below zero ({new_long:.2f})."

    # --- Estimate credit ---
    new_otm_buffer = underlying - new_short
    estimated_credit = _estimate_credit(net_credit, otm_buffer, new_otm_buffer, new_width)
    if estimated_credit is None:
        return None, (
            f"No clean alternative: the credit estimate for this scenario is invalid "
            f"(short strike {new_short:.2f}, OTM buffer {new_otm_buffer:.2f}). "
            "The scenario may be too far in-the-money or produce no meaningful premium."
        )

    # Build label
    parts = [shift_label, width_label]
    label = "; ".join(p for p in parts if "unchanged" not in p) or "Baseline"

    scenario = _build_scenario(
        strategy_key=strategy_key,
        ticker=ticker,
        underlying_price=underlying,
        short_strike=new_short,
        long_strike=new_long,
        expiration_date=expiration_date,
        net_credit=estimated_credit,
        is_credit_estimated=True,
        label=label,
    )
    if scenario is None:
        return None, "No clean alternative: the adjusted scenario produced an invalid spread structure."
    return scenario, None


# ---------------------------------------------------------------------------
# Strike and width resolution — bear call spread
# ---------------------------------------------------------------------------

def _resolve_bear_call(
    *,
    underlying: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
    spread_width: float,
    ticker: str | None,
    expiration_date: str | None,
    params: WorkbenchParams,
) -> tuple[WorkbenchScenarioSummary | None, str | None]:
    """Resolve the what-if scenario for a bear call spread.

    For bear call: short_call < long_call; short strike is OTM above spot.
    Further OTM = higher short strike. Closer ATM = lower short strike.
    """
    strategy_key = "bear_call_spread"
    otm_buffer = short_strike - underlying  # positive = OTM

    # --- Compute new short strike ---
    if params.strike_shift == "further_otm":
        new_short = round(short_strike + _STRIKE_STEP, 2)
        shift_delta = +_STRIKE_STEP
        shift_label = f"Short strike shifted further OTM to {new_short:.2f}"
    elif params.strike_shift == "closer_atm":
        new_short = round(short_strike - _STRIKE_STEP, 2)
        shift_delta = -_STRIKE_STEP
        shift_label = f"Short strike moved closer to ATM ({new_short:.2f})"
    else:
        new_short = short_strike
        shift_delta = 0.0
        shift_label = "Short strike unchanged"

    # Validate short strike remains OTM for bear call (must be above underlying)
    if new_short <= underlying:
        return None, f"No clean alternative: moving the short strike to {new_short:.2f} would place it at or below the current underlying ({underlying:.2f}), making this no longer an OTM spread."

    # --- Compute new long strike ---
    # For bear call, long_strike > short_strike; width = long_strike - short_strike
    if params.width_adjustment == "narrower":
        new_width = max(spread_width - _STRIKE_STEP, _STRIKE_STEP)
        if new_width <= 0:
            return None, "No clean alternative: narrowing the spread further would collapse the width to zero."
        new_long = round(new_short + new_width, 2)
        width_label = "Spread narrowed"
    elif params.width_adjustment == "wider":
        new_width = spread_width + _STRIKE_STEP
        new_long = round(new_short + new_width, 2)
        width_label = "Spread widened"
    else:
        new_long = round(new_short + spread_width, 2)
        new_width = spread_width
        width_label = "Spread width unchanged"

    # --- Estimate credit ---
    new_otm_buffer = new_short - underlying
    estimated_credit = _estimate_credit(net_credit, otm_buffer, new_otm_buffer, new_width)
    if estimated_credit is None:
        return None, (
            f"No clean alternative: the credit estimate for this scenario is invalid "
            f"(short strike {new_short:.2f}, OTM buffer {new_otm_buffer:.2f}). "
            "The scenario may be too far in-the-money or produce no meaningful premium."
        )

    parts = [shift_label, width_label]
    label = "; ".join(p for p in parts if "unchanged" not in p) or "Baseline"

    scenario = _build_scenario(
        strategy_key=strategy_key,
        ticker=ticker,
        underlying_price=underlying,
        short_strike=new_short,
        long_strike=new_long,
        expiration_date=expiration_date,
        net_credit=estimated_credit,
        is_credit_estimated=True,
        label=label,
    )
    if scenario is None:
        return None, "No clean alternative: the adjusted scenario produced an invalid spread structure."
    return scenario, None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_workbench(
    trade: dict[str, Any],
    *,
    scan_id: str,
    trade_id: str,
    params: WorkbenchParams,
) -> WorkbenchResult:
    """Generate the workbench result for a trade and what-if parameter set.

    Always returns a WorkbenchResult. When the scenario cannot be built,
    scenario=None and unavailable_reason explains why.

    The baseline is always constructed and included.
    """
    strategy_key = _normalize_strategy_key(trade.get("strategy_type") or trade.get("strategy_key") or "")
    ticker = trade.get("ticker")
    underlying = float(trade.get("underlying_price", 0) or 0)
    short_strike = float(trade.get("short_strike", 0) or 0)
    long_strike = float(trade.get("long_strike", 0) or 0)
    net_credit = float(trade.get("net_credit", 0) or 0)
    expiration_date = trade.get("expiration_date")
    spread_width = abs(short_strike - long_strike)

    # Build baseline — always from real trade data, never estimated
    baseline = _build_scenario(
        strategy_key=strategy_key,
        ticker=ticker,
        underlying_price=underlying,
        short_strike=short_strike,
        long_strike=long_strike,
        expiration_date=expiration_date,
        net_credit=net_credit,
        is_credit_estimated=False,
        label="Current scanned setup",
    )

    if baseline is None:
        return WorkbenchResult(
            scan_id=scan_id,
            trade_id=trade_id,
            strategy_key=strategy_key,
            underlying_price_reference=underlying,
            ticker=ticker,
            strike_shift=params.strike_shift,
            width_adjustment=params.width_adjustment,
            baseline=WorkbenchScenarioSummary(
                strategy_key=strategy_key,
                ticker=ticker,
                short_strike=short_strike,
                long_strike=long_strike,
                expiration_date=expiration_date,
                net_credit=net_credit,
                spread_width=spread_width,
                max_profit=0.0,
                max_loss=0.0,
                breakeven=0.0,
                label="Current scanned setup",
                is_credit_estimated=False,
                payoff=None,
            ),
            scenario=None,
            comparison=None,
            unavailable_reason="Baseline trade structure is invalid; cannot build workbench scenarios.",
        )

    # When both controls are at baseline, return no scenario (it is identical)
    is_baseline_params = params.strike_shift == "baseline" and params.width_adjustment == "baseline"
    if is_baseline_params:
        return WorkbenchResult(
            scan_id=scan_id,
            trade_id=trade_id,
            strategy_key=strategy_key,
            underlying_price_reference=underlying,
            ticker=ticker,
            strike_shift=params.strike_shift,
            width_adjustment=params.width_adjustment,
            baseline=baseline,
            scenario=None,
            comparison=None,
            unavailable_reason=None,
        )

    if strategy_key not in SUPPORTED_WORKBENCH_STRATEGIES:
        return WorkbenchResult(
            scan_id=scan_id,
            trade_id=trade_id,
            strategy_key=strategy_key,
            underlying_price_reference=underlying,
            ticker=ticker,
            strike_shift=params.strike_shift,
            width_adjustment=params.width_adjustment,
            baseline=baseline,
            scenario=None,
            comparison=None,
            unavailable_reason=f"What-if analysis is not yet supported for strategy '{strategy_key}'.",
        )

    # Resolve scenario
    if strategy_key == "bull_put_spread":
        scenario, reason = _resolve_bull_put(
            underlying=underlying,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
            spread_width=spread_width,
            ticker=ticker,
            expiration_date=expiration_date,
            params=params,
        )
    else:
        scenario, reason = _resolve_bear_call(
            underlying=underlying,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
            spread_width=spread_width,
            ticker=ticker,
            expiration_date=expiration_date,
            params=params,
        )

    comparison: WorkbenchComparison | None = None
    if scenario is not None:
        comparison = _build_comparison(scenario, baseline, strategy_key)

    return WorkbenchResult(
        scan_id=scan_id,
        trade_id=trade_id,
        strategy_key=strategy_key,
        underlying_price_reference=underlying,
        ticker=ticker,
        strike_shift=params.strike_shift,
        width_adjustment=params.width_adjustment,
        baseline=baseline,
        scenario=scenario,
        comparison=comparison,
        unavailable_reason=reason,
    )
