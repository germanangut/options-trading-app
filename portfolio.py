"""Lightweight portfolio exposure summaries for current-run candidates.

This module is intentionally descriptive only. It does not enforce portfolio
rules, suppress trades, or alter ranking/scoring behavior.
"""

from collections import Counter

from strategies import get_strategy


DEFAULT_ACCOUNT_SIZE = 10000.0
DEFAULT_MAX_RISK_PCT = 0.02


def _resolve_strategy_name(spread):
    return (
        spread.get("strategy_label")
        or spread.get("strategy_type")
        or spread.get("strategy_key")
        or "unknown"
    )


def _resolve_directional_bias(spread):
    bias = spread.get("directional_bias")
    if bias not in (None, ""):
        return str(bias).strip().lower()

    strategy = get_strategy(
        spread.get("strategy_key")
        or spread.get("strategy_label")
        or spread.get("strategy_type")
    ) or {}

    strategy_bias = strategy.get("directional_bias")
    if strategy_bias not in (None, ""):
        return str(strategy_bias).strip().lower()

    return "unknown"


def _resolve_strategy_family(spread):
    family = spread.get("strategy_family")
    if family not in (None, ""):
        return str(family).strip().lower()

    strategy = get_strategy(
        spread.get("strategy_key")
        or spread.get("strategy_label")
        or spread.get("strategy_type")
    ) or {}

    strategy_family = strategy.get("family")
    if strategy_family not in (None, ""):
        return str(strategy_family).strip().lower()

    return "unknown"


def _safe_float(value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_max_risk_pct(max_risk_pct):
    normalized_pct = _safe_float(max_risk_pct)

    if normalized_pct is None or normalized_pct <= 0:
        return DEFAULT_MAX_RISK_PCT

    if normalized_pct > 1:
        normalized_pct = normalized_pct / 100.0

    return normalized_pct


def _estimate_trade_risk_dollars(spread):
    max_risk = _safe_float(spread.get("max_risk"))
    if max_risk is not None and max_risk > 0:
        return round(max_risk * 100, 2)

    spread_width = _safe_float(spread.get("spread_width"))
    net_credit = _safe_float(spread.get("net_credit"))
    if spread_width is None or net_credit is None:
        return None

    return round(max(spread_width - net_credit, 0) * 100, 2)


def _build_count_rows(counter, key_name, total_count=None, limit=5):
    rows = []

    for name, count in counter.most_common(limit):
        row = {
            key_name: name,
            "count": count,
        }

        if total_count:
            row["share_pct"] = round((count / total_count) * 100, 1)

        rows.append(row)

    return rows


def _summarize_trade_group(spreads, group_label, limit=5):
    spreads = [spread for spread in (spreads or []) if isinstance(spread, dict)]

    ticker_counter = Counter()
    strategy_counter = Counter()
    directional_counter = Counter()

    for spread in spreads:
        ticker = spread.get("ticker")
        strategy_name = _resolve_strategy_name(spread)
        directional_bias = _resolve_directional_bias(spread)

        if ticker:
            ticker_counter[ticker] += 1

        if strategy_name and strategy_name != "unknown":
            strategy_counter[strategy_name] += 1

        if directional_bias:
            directional_counter[directional_bias] += 1

    trade_count = len(spreads)
    top_ticker_concentration = _build_count_rows(
        ticker_counter,
        "ticker",
        total_count=trade_count,
        limit=min(3, limit),
    )
    directional_exposure = _build_count_rows(
        directional_counter,
        "directional_bias",
        total_count=trade_count,
        limit=limit,
    )

    notes = []

    if trade_count == 0:
        notes.append(f"No current {group_label} trades to summarize.")
    else:
        top_ticker = top_ticker_concentration[0] if top_ticker_concentration else None
        if top_ticker and top_ticker.get("share_pct", 0) >= 50:
            notes.append(
                f"{group_label.title()} candidates are concentrated in {top_ticker['ticker']} "
                f"({top_ticker['share_pct']}% of current {group_label} trades)."
            )

        top_direction = directional_exposure[0] if directional_exposure else None
        if (
            top_direction
            and top_direction.get("directional_bias") != "unknown"
            and top_direction.get("share_pct", 0) >= 70
        ):
            notes.append(
                f"Current {group_label} exposure is tilted toward "
                f"{top_direction['directional_bias']} setups "
                f"({top_direction['share_pct']}%)."
            )

    return {
        "trade_count": trade_count,
        "unique_ticker_count": len(ticker_counter),
        "counts_by_ticker": _build_count_rows(
            ticker_counter,
            "ticker",
            total_count=trade_count,
            limit=limit,
        ),
        "counts_by_strategy": _build_count_rows(
            strategy_counter,
            "strategy",
            total_count=trade_count,
            limit=limit,
        ),
        "directional_exposure": directional_exposure,
        "top_ticker_concentration": top_ticker_concentration,
        "notes": notes,
    }


def compute_portfolio_exposure_summary(run_output, limit=5):
    """Summarize current-run exposure and concentration without changing behavior."""
    run_output = run_output or {}

    qualified_summary = _summarize_trade_group(
        run_output.get("qualified", []),
        "qualified",
        limit=limit,
    )
    alert_summary = _summarize_trade_group(
        run_output.get("alerts", []),
        "alert",
        limit=limit,
    )

    combined_notes = qualified_summary.get("notes", []) + alert_summary.get("notes", [])

    return {
        "metadata": {
            "qualified_trade_count": qualified_summary.get("trade_count", 0),
            "alert_trade_count": alert_summary.get("trade_count", 0),
            "unique_qualified_ticker_count": qualified_summary.get("unique_ticker_count", 0),
            "unique_alert_ticker_count": alert_summary.get("unique_ticker_count", 0),
        },
        "qualified": qualified_summary,
        "alerts": alert_summary,
        "notes": combined_notes[:4],
    }


def compute_position_sizing_summary(
    run_output,
    account_size=DEFAULT_ACCOUNT_SIZE,
    max_risk_pct=DEFAULT_MAX_RISK_PCT,
    limit=5,
):
    """Build a lightweight, descriptive sizing summary for current qualified trades."""
    run_output = run_output or {}
    qualified_trades = [
        spread for spread in (run_output.get("qualified", []) or []) if isinstance(spread, dict)
    ]

    normalized_account_size = _safe_float(account_size) or DEFAULT_ACCOUNT_SIZE
    normalized_max_risk_pct = _normalize_max_risk_pct(max_risk_pct)
    max_risk_dollars = round(normalized_account_size * normalized_max_risk_pct, 2)

    trade_sizing = []
    estimated_risks = []
    fits_budget_count = 0
    oversized_count = 0
    insufficient_data_count = 0

    for spread in qualified_trades:
        estimated_risk_dollars = _estimate_trade_risk_dollars(spread)
        fits_risk_budget = None
        approx_contracts_within_budget = None
        sizing_note = "Risk estimate unavailable from current trade fields."

        if estimated_risk_dollars is not None and estimated_risk_dollars > 0:
            estimated_risks.append(estimated_risk_dollars)
            approx_contracts_within_budget = int(max_risk_dollars // estimated_risk_dollars)
            fits_risk_budget = approx_contracts_within_budget >= 1

            if fits_risk_budget:
                fits_budget_count += 1
                sizing_note = (
                    f"Estimated one-contract risk fits within the current budget; up to {approx_contracts_within_budget} contract(s) fit by risk."
                )
            else:
                oversized_count += 1
                sizing_note = (
                    "Estimated one-contract risk is above the current per-trade budget."
                )
        else:
            insufficient_data_count += 1

        trade_sizing.append(
            {
                "ticker": spread.get("ticker"),
                "strategy": _resolve_strategy_name(spread),
                "adjusted_score": spread.get("adjusted_score"),
                "estimated_max_risk_dollars": estimated_risk_dollars,
                "fits_risk_budget": fits_risk_budget,
                "approx_contracts_within_budget": approx_contracts_within_budget,
                "sizing_note": sizing_note,
            }
        )

    warnings = []
    if not qualified_trades:
        warnings.append("No qualified trades are available for sizing context in this run.")
    if oversized_count > 0:
        warnings.append(
            f"{oversized_count} qualified trade(s) appear oversized relative to the current per-trade risk budget."
        )
    if insufficient_data_count > 0:
        warnings.append(
            f"{insufficient_data_count} qualified trade(s) do not have enough risk fields for a simple sizing estimate."
        )

    average_estimated_risk = (
        round(sum(estimated_risks) / len(estimated_risks), 2)
        if estimated_risks
        else None
    )

    return {
        "inputs": {
            "account_size": round(normalized_account_size, 2),
            "max_risk_pct": round(normalized_max_risk_pct, 4),
            "max_risk_dollars": max_risk_dollars,
        },
        "summary": {
            "qualified_trade_count": len(qualified_trades),
            "trade_count_with_risk_estimate": len(estimated_risks),
            "fits_budget_count": fits_budget_count,
            "oversized_count": oversized_count,
            "insufficient_data_count": insufficient_data_count,
            "average_estimated_max_risk_dollars": average_estimated_risk,
        },
        "trade_sizing": trade_sizing[:limit],
        "warnings": warnings[:4],
    }


def compute_exposure_overlap_summary(run_output, limit=5):
    """Summarize overlap awareness using current qualified trades and strategy metadata."""
    run_output = run_output or {}
    qualified_trades = [
        spread for spread in (run_output.get("qualified", []) or []) if isinstance(spread, dict)
    ]

    direction_counter = Counter()
    family_counter = Counter()
    ticker_direction_counter = Counter()

    for spread in qualified_trades:
        ticker = spread.get("ticker") or "unknown"
        direction = _resolve_directional_bias(spread)
        family = _resolve_strategy_family(spread)

        if direction:
            direction_counter[direction] += 1
        if family:
            family_counter[family] += 1
        if ticker and direction and ticker != "unknown":
            ticker_direction_counter[f"{ticker} | {direction}"] += 1

    counts_by_direction = _build_count_rows(
        direction_counter,
        "direction",
        total_count=len(qualified_trades),
        limit=limit,
    )
    counts_by_strategy_family = _build_count_rows(
        family_counter,
        "strategy_family",
        total_count=len(qualified_trades),
        limit=limit,
    )
    repeated_ticker_direction_combinations = [
        {"ticker_direction": name, "count": count}
        for name, count in ticker_direction_counter.most_common(limit)
        if count >= 2
    ]

    notes = []
    top_direction = counts_by_direction[0] if counts_by_direction else None
    top_family = counts_by_strategy_family[0] if counts_by_strategy_family else None
    top_overlap = repeated_ticker_direction_combinations[0] if repeated_ticker_direction_combinations else None

    if not qualified_trades:
        notes.append("No qualified trades are available yet, so overlap awareness is limited for this run.")
    else:
        if top_direction and top_direction.get("share_pct", 0) >= 70:
            notes.append(
                f"Qualified exposure is clustered toward {top_direction['direction']} setups ({top_direction['share_pct']}%)."
            )

        if top_family and top_family.get("share_pct", 0) >= 70:
            notes.append(
                f"Most current qualified trades fall into the {top_family['strategy_family']} family ({top_family['share_pct']}%)."
            )

        if top_overlap:
            notes.append(
                f"Repeated overlap is present in {top_overlap['ticker_direction']} ({top_overlap['count']} current qualified trades)."
            )

        if not notes:
            notes.append("Current qualified trades appear relatively spread across directions and ticker exposures.")

    return {
        "summary": {
            "qualified_trade_count": len(qualified_trades),
            "unique_direction_count": len(direction_counter),
            "unique_strategy_family_count": len(family_counter),
            "repeated_overlap_count": len(repeated_ticker_direction_combinations),
        },
        "counts_by_direction": counts_by_direction,
        "counts_by_strategy_family": counts_by_strategy_family,
        "repeated_ticker_direction_combinations": repeated_ticker_direction_combinations,
        "warnings": notes[:4],
    }


def compute_portfolio_decision_summary(run_output, limit=5):
    """Combine existing portfolio-aware summaries into a concise portfolio interpretation."""
    run_output = run_output or {}

    exposure_summary = run_output.get("portfolio_exposure_summary") or compute_portfolio_exposure_summary(
        run_output,
        limit=limit,
    )
    sizing_summary = run_output.get("position_sizing_summary") or compute_position_sizing_summary(
        run_output,
        limit=limit,
    )
    overlap_summary = run_output.get("exposure_overlap_summary") or compute_exposure_overlap_summary(
        run_output,
        limit=limit,
    )

    qualified_trade_count = (exposure_summary.get("metadata") or {}).get(
        "qualified_trade_count",
        0,
    )
    top_ticker = ((exposure_summary.get("qualified") or {}).get("top_ticker_concentration") or [None])[0] or {}
    top_direction = ((exposure_summary.get("qualified") or {}).get("directional_exposure") or [None])[0] or {}
    sizing_core = sizing_summary.get("summary") or {}
    overlap_core = overlap_summary.get("summary") or {}

    posture = "Balanced Watchlist"
    if qualified_trade_count == 0:
        posture = "No Current Portfolio Setup"
    elif sizing_core.get("oversized_count", 0) > 0 and overlap_core.get("repeated_overlap_count", 0) > 0:
        posture = "Concentrated Risk Watch"
    elif top_ticker.get("share_pct", 0) >= 50 or top_direction.get("share_pct", 0) >= 70:
        posture = "Clustered Opportunity Set"
    elif sizing_core.get("fits_budget_count", 0) >= max(1, qualified_trade_count - 1):
        posture = "Budget-Aligned Opportunity Set"

    key_signals = []
    if qualified_trade_count:
        key_signals.append(f"{qualified_trade_count} qualified trade(s) are active in the current run.")
    if top_ticker:
        key_signals.append(
            f"Top ticker concentration: {top_ticker.get('ticker', 'n/a')} at {top_ticker.get('share_pct', 0)}%."
        )
    if top_direction:
        key_signals.append(
            f"Directional tilt: {top_direction.get('directional_bias', 'n/a')} at {top_direction.get('share_pct', 0)}%."
        )
    if sizing_core.get("average_estimated_max_risk_dollars") is not None:
        key_signals.append(
            f"Average estimated one-contract risk: ${sizing_core.get('average_estimated_max_risk_dollars')}"
        )

    interpretations = []
    if qualified_trade_count == 0:
        interpretations.append("No portfolio-level interpretation is needed because there are no qualified trades in this run.")
    else:
        if posture == "Concentrated Risk Watch":
            interpretations.append(
                "Current qualified ideas are actionable, but they cluster enough to warrant a closer portfolio-level review before combining them."
            )
        elif posture == "Clustered Opportunity Set":
            interpretations.append(
                "The opportunity set is somewhat concentrated, so these trades may be related exposures rather than fully distinct ideas."
            )
        elif posture == "Budget-Aligned Opportunity Set":
            interpretations.append(
                "Most current qualified trades appear to fit the sample per-trade risk budget, keeping the set broadly manageable for review."
            )
        else:
            interpretations.append(
                "The current mix of qualified trades looks relatively balanced across the portfolio signals tracked so far."
            )

    cautions = []
    cautions.extend((exposure_summary.get("notes") or [])[:2])
    cautions.extend((sizing_summary.get("warnings") or [])[:2])
    cautions.extend((overlap_summary.get("warnings") or [])[:2])

    deduped_cautions = []
    seen = set()
    for caution in cautions:
        if not caution or caution in seen:
            continue
        seen.add(caution)
        deduped_cautions.append(caution)

    return {
        "posture_label": posture,
        "key_portfolio_signals": key_signals[:4],
        "interpretation": interpretations[:2],
        "cautions": deduped_cautions[:5],
    }
