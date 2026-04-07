"""Lightweight portfolio exposure summaries for current-run candidates.

This module is intentionally descriptive only. It does not enforce portfolio
rules, suppress trades, or alter ranking/scoring behavior.
"""

from collections import Counter

from strategies import get_strategy


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
