"""Delta-neutral exploration service for PU-15B.5.

Provides a first-phase analytical comparison between:
- Baseline directional spread (selected scanned trade)
- Reduced-directionality candidate (when cleanly constructible)

The candidate is a disciplined nearby structural adjustment (further OTM,
often narrower) and is not execution-ready.
"""

from __future__ import annotations

from typing import Any

from backend.contracts.delta_neutral_models import (
    DeltaNeutralComparison,
    DeltaNeutralExploration,
    DeltaNeutralScenario,
    SUPPORTED_DELTA_NEUTRAL_STRATEGIES,
)
from backend.contracts.payoff_models import PayoffInput
from backend.services.payoff_engine import calculate_payoff


_MIN_CREDIT = 0.01
_MIN_OTM_BUFFER = 0.01
_STRIKE_STEP = 1.0


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
    if baseline_otm_buffer < _MIN_OTM_BUFFER or new_otm_buffer < _MIN_OTM_BUFFER:
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
        return calculate_payoff(
            PayoffInput(
                strategy_key=strategy_key,
                ticker=ticker,
                underlying_price_reference=underlying_price,
                short_strike=short_strike,
                long_strike=long_strike,
                net_credit=net_credit,
            )
        )
    except (TypeError, ValueError):
        return None


def _compute_position_net_delta(short_delta: float | None, long_delta: float | None) -> float | None:
    """Net delta for short vertical position.

    Position convention used:
    - short leg contributes -short_delta
    - long leg contributes +long_delta

    net_delta = (-short_delta) + long_delta
    """
    if short_delta is None or long_delta is None:
        return None
    return round((-short_delta) + long_delta, 6)


def _build_scenario(
    *,
    strategy_key: str,
    ticker: str | None,
    short_strike: float,
    long_strike: float,
    expiration_date: str | None,
    net_credit: float,
    underlying_price: float,
    label: str,
    is_credit_estimated: bool,
    net_delta: float,
) -> DeltaNeutralScenario | None:
    spread_width = round(abs(short_strike - long_strike), 4)
    if spread_width <= 0:
        return None
    if net_credit < _MIN_CREDIT or net_credit >= spread_width:
        return None

    max_profit = round(net_credit * 100, 2)
    max_loss = round((spread_width - net_credit) * 100, 2)
    breakeven = _breakeven_for(strategy_key, short_strike, net_credit)

    payoff = _build_payoff(
        strategy_key,
        ticker,
        underlying_price,
        short_strike,
        long_strike,
        net_credit,
    )

    return DeltaNeutralScenario(
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
        net_delta=net_delta,
        payoff=payoff,
    )


def _build_comparison(
    baseline: DeltaNeutralScenario,
    candidate: DeltaNeutralScenario,
) -> DeltaNeutralComparison:
    baseline_abs = abs(baseline.net_delta)
    candidate_abs = abs(candidate.net_delta)
    reduction = round(max(0.0, baseline_abs - candidate_abs), 6)
    reduction_pct = round((reduction / baseline_abs) * 100, 2) if baseline_abs > 0 else 0.0

    direction_text = (
        "closer to neutral" if candidate_abs < baseline_abs else "no directional reduction"
    )
    summary = (
        f"Reduced directional bias ({reduction_pct:.1f}%): {direction_text}. "
        "Lower directional conviction, different payoff tradeoff."
    )

    return DeltaNeutralComparison(
        baseline_net_delta=baseline.net_delta,
        candidate_net_delta=candidate.net_delta,
        delta_reduction=reduction,
        delta_reduction_pct=reduction_pct,
        delta_max_profit=round(candidate.max_profit - baseline.max_profit, 2),
        delta_max_loss=round(candidate.max_loss - baseline.max_loss, 2),
        delta_breakeven=round(candidate.breakeven - baseline.breakeven, 4),
        summary=summary,
    )


def _estimate_candidate_net_delta(
    *,
    baseline_net_delta: float,
    baseline_width: float,
    new_width: float,
    baseline_otm_buffer: float,
    new_otm_buffer: float,
) -> float | None:
    """Estimate candidate net delta magnitude from structural shifts.

    Approximation uses two explicit factors:
    1) OTM factor: baseline_otm_buffer / new_otm_buffer
    2) Width factor: new_width / baseline_width

    candidate_abs_delta ≈ baseline_abs_delta * OTM factor * Width factor
    """
    if baseline_width <= 0 or new_width <= 0:
        return None
    if baseline_otm_buffer < _MIN_OTM_BUFFER or new_otm_buffer < _MIN_OTM_BUFFER:
        return None

    baseline_abs = abs(baseline_net_delta)
    otm_factor = baseline_otm_buffer / new_otm_buffer
    width_factor = new_width / baseline_width
    candidate_abs = round(baseline_abs * otm_factor * width_factor, 6)

    # Preserve directional sign from baseline.
    if baseline_net_delta < 0:
        return -candidate_abs
    return candidate_abs


def _resolve_candidate_for_bull_put(
    *,
    underlying: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
    baseline_net_delta: float,
    ticker: str | None,
    expiration_date: str | None,
) -> tuple[DeltaNeutralScenario | None, str | None, str | None]:
    """Build reduced-directionality candidate for a bull put spread.

    Strategy:
    - Shift short strike further OTM by one step.
    - Narrow width by one step when possible.
    - Estimate credit and net delta deterministically.
    """
    baseline_width = abs(short_strike - long_strike)
    baseline_otm = underlying - short_strike

    new_short = round(short_strike - _STRIKE_STEP, 2)
    new_width = max(_STRIKE_STEP, round(baseline_width - _STRIKE_STEP, 2))
    new_long = round(new_short - new_width, 2)

    if new_short >= underlying:
        return None, "No clean delta-neutral alternative found: adjusted short strike is no longer out-of-the-money.", None
    if new_long <= 0:
        return None, "No clean delta-neutral alternative found: adjusted long strike is invalid.", None

    new_otm = underlying - new_short
    est_credit = _estimate_credit(net_credit, baseline_otm, new_otm, new_width)
    if est_credit is None:
        return None, "No clean delta-neutral alternative found: premium estimate is invalid for the nearby structure.", None

    est_net_delta = _estimate_candidate_net_delta(
        baseline_net_delta=baseline_net_delta,
        baseline_width=baseline_width,
        new_width=new_width,
        baseline_otm_buffer=baseline_otm,
        new_otm_buffer=new_otm,
    )
    if est_net_delta is None:
        return None, "No clean delta-neutral alternative found: directional estimate could not be computed reliably.", None

    candidate = _build_scenario(
        strategy_key="bull_put_spread",
        ticker=ticker,
        short_strike=new_short,
        long_strike=new_long,
        expiration_date=expiration_date,
        net_credit=est_credit,
        underlying_price=underlying,
        label="Reduced directional bias candidate",
        is_credit_estimated=True,
        net_delta=est_net_delta,
    )
    if candidate is None:
        return None, "No clean delta-neutral alternative found: nearby structure is invalid.", None

    limitation = (
        "Candidate net delta is an approximation from baseline leg deltas and nearby structural shifts; "
        "it is intended for directional comparison only."
    )
    return candidate, None, limitation


def _resolve_candidate_for_bear_call(
    *,
    underlying: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
    baseline_net_delta: float,
    ticker: str | None,
    expiration_date: str | None,
) -> tuple[DeltaNeutralScenario | None, str | None, str | None]:
    baseline_width = abs(long_strike - short_strike)
    baseline_otm = short_strike - underlying

    new_short = round(short_strike + _STRIKE_STEP, 2)
    new_width = max(_STRIKE_STEP, round(baseline_width - _STRIKE_STEP, 2))
    new_long = round(new_short + new_width, 2)

    if new_short <= underlying:
        return None, "No clean delta-neutral alternative found: adjusted short strike is no longer out-of-the-money.", None

    new_otm = new_short - underlying
    est_credit = _estimate_credit(net_credit, baseline_otm, new_otm, new_width)
    if est_credit is None:
        return None, "No clean delta-neutral alternative found: premium estimate is invalid for the nearby structure.", None

    est_net_delta = _estimate_candidate_net_delta(
        baseline_net_delta=baseline_net_delta,
        baseline_width=baseline_width,
        new_width=new_width,
        baseline_otm_buffer=baseline_otm,
        new_otm_buffer=new_otm,
    )
    if est_net_delta is None:
        return None, "No clean delta-neutral alternative found: directional estimate could not be computed reliably.", None

    candidate = _build_scenario(
        strategy_key="bear_call_spread",
        ticker=ticker,
        short_strike=new_short,
        long_strike=new_long,
        expiration_date=expiration_date,
        net_credit=est_credit,
        underlying_price=underlying,
        label="Reduced directional bias candidate",
        is_credit_estimated=True,
        net_delta=est_net_delta,
    )
    if candidate is None:
        return None, "No clean delta-neutral alternative found: nearby structure is invalid.", None

    limitation = (
        "Candidate net delta is an approximation from baseline leg deltas and nearby structural shifts; "
        "it is intended for directional comparison only."
    )
    return candidate, None, limitation


def generate_delta_neutral_exploration(
    trade: dict[str, Any],
    *,
    scan_id: str,
    trade_id: str,
) -> DeltaNeutralExploration:
    strategy_key = _normalize_strategy_key(trade.get("strategy_type") or trade.get("strategy_key") or "")
    ticker = trade.get("ticker")
    underlying = float(trade.get("underlying_price", 0) or 0)
    short_strike = float(trade.get("short_strike", 0) or 0)
    long_strike = float(trade.get("long_strike", 0) or 0)
    net_credit = float(trade.get("net_credit", 0) or 0)
    expiration_date = trade.get("expiration_date")
    short_delta = trade.get("short_delta")
    long_delta = trade.get("long_delta")
    baseline_trade_id = trade.get("trade_id")

    short_delta_value = float(short_delta) if short_delta is not None else None
    long_delta_value = float(long_delta) if long_delta is not None else None

    baseline_net_delta = _compute_position_net_delta(short_delta_value, long_delta_value)
    if baseline_net_delta is None:
        baseline_net_delta = 0.0

    baseline = _build_scenario(
        strategy_key=strategy_key,
        ticker=ticker,
        short_strike=short_strike,
        long_strike=long_strike,
        expiration_date=expiration_date,
        net_credit=net_credit,
        underlying_price=underlying,
        label="Current scanned setup",
        is_credit_estimated=False,
        net_delta=baseline_net_delta,
    )

    if baseline is None:
        fallback = DeltaNeutralScenario(
            strategy_key=strategy_key,
            ticker=ticker,
            short_strike=short_strike,
            long_strike=long_strike,
            expiration_date=expiration_date,
            net_credit=net_credit,
            spread_width=abs(short_strike - long_strike),
            max_profit=0.0,
            max_loss=0.0,
            breakeven=0.0,
            label="Current scanned setup",
            is_credit_estimated=False,
            net_delta=0.0,
            payoff=None,
        )
        return DeltaNeutralExploration(
            scan_id=scan_id,
            trade_id=trade_id,
            baseline_trade_id=baseline_trade_id,
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying,
            baseline=fallback,
            neutral_candidate_available=False,
            neutral_candidate=None,
            comparison=None,
            rationale="Baseline trade structure is invalid for delta-neutral exploration.",
            limitation_note=None,
            unavailable_reason="No clean delta-neutral alternative found because the baseline structure is invalid.",
        )

    if strategy_key not in SUPPORTED_DELTA_NEUTRAL_STRATEGIES:
        return DeltaNeutralExploration(
            scan_id=scan_id,
            trade_id=trade_id,
            baseline_trade_id=baseline_trade_id,
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying,
            baseline=baseline,
            neutral_candidate_available=False,
            neutral_candidate=None,
            comparison=None,
            rationale="Delta-neutral exploration is currently limited to supported vertical credit spreads.",
            limitation_note=None,
            unavailable_reason=f"No clean delta-neutral alternative found for strategy '{strategy_key}'.",
        )

    if short_delta_value is None or long_delta_value is None:
        return DeltaNeutralExploration(
            scan_id=scan_id,
            trade_id=trade_id,
            baseline_trade_id=baseline_trade_id,
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying,
            baseline=baseline,
            neutral_candidate_available=False,
            neutral_candidate=None,
            comparison=None,
            rationale="Directional exposure cannot be computed without both leg deltas.",
            limitation_note=None,
            unavailable_reason="No clean delta-neutral alternative found because leg deltas are missing.",
        )

    candidate: DeltaNeutralScenario | None
    unavailable_reason: str | None
    limitation_note: str | None

    if strategy_key == "bull_put_spread":
        candidate, unavailable_reason, limitation_note = _resolve_candidate_for_bull_put(
            underlying=underlying,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
            baseline_net_delta=baseline.net_delta,
            ticker=ticker,
            expiration_date=expiration_date,
        )
    else:
        candidate, unavailable_reason, limitation_note = _resolve_candidate_for_bear_call(
            underlying=underlying,
            short_strike=short_strike,
            long_strike=long_strike,
            net_credit=net_credit,
            baseline_net_delta=baseline.net_delta,
            ticker=ticker,
            expiration_date=expiration_date,
        )

    if candidate is None:
        return DeltaNeutralExploration(
            scan_id=scan_id,
            trade_id=trade_id,
            baseline_trade_id=baseline_trade_id,
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying,
            baseline=baseline,
            neutral_candidate_available=False,
            neutral_candidate=None,
            comparison=None,
            rationale="No clean reduced-bias structure was found in nearby spread context.",
            limitation_note=limitation_note,
            unavailable_reason=unavailable_reason,
        )

    comparison = _build_comparison(baseline, candidate)

    if abs(candidate.net_delta) >= abs(baseline.net_delta):
        return DeltaNeutralExploration(
            scan_id=scan_id,
            trade_id=trade_id,
            baseline_trade_id=baseline_trade_id,
            strategy_key=strategy_key,
            ticker=ticker,
            underlying_price_reference=underlying,
            baseline=baseline,
            neutral_candidate_available=False,
            neutral_candidate=None,
            comparison=None,
            rationale="Nearby structural adjustments did not reduce directional exposure.",
            limitation_note=limitation_note,
            unavailable_reason="No clean delta-neutral alternative found that reduces directional exposure.",
        )

    return DeltaNeutralExploration(
        scan_id=scan_id,
        trade_id=trade_id,
        baseline_trade_id=baseline_trade_id,
        strategy_key=strategy_key,
        ticker=ticker,
        underlying_price_reference=underlying,
        baseline=baseline,
        neutral_candidate_available=True,
        neutral_candidate=candidate,
        comparison=comparison,
        rationale="Reduced directional bias candidate built from nearby valid spread context.",
        limitation_note=limitation_note,
        unavailable_reason=None,
    )
