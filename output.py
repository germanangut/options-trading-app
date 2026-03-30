def compact_spread(spread):
    if not spread:
        return None

    return {
        "ticker": spread.get("ticker"),
        "strategy_type": spread.get("strategy_type"),
        "adjusted_score": spread.get("adjusted_score", spread.get("score")),
        "score": spread.get("score"),
        "consistency_bonus": spread.get("consistency_bonus", 0),
        "POP": spread.get("POP"),
        "ROR": spread.get("ROR"),
        "short_strike": spread.get("short_strike"),
        "long_strike": spread.get("long_strike"),
        "underlying_price": spread.get("underlying_price"),
        "expiration_date": spread.get("expiration_date"),
        "DTE": spread.get("DTE"),
        "label": spread.get("label"),
    }


def build_summary(qualified, near_miss):
    top_overall = qualified[0] if qualified else None

    bull_puts = [s for s in qualified if s["strategy_type"] == "bull put spread"]
    bear_calls = [s for s in qualified if s["strategy_type"] == "bear call spread"]

    top_bull_put = bull_puts[0] if bull_puts else None
    top_bear_call = bear_calls[0] if bear_calls else None

    return {
        "qualified_count": len(qualified),
        "near_miss_count": len(near_miss),
        "top_overall": compact_spread(top_overall),
        "top_bull_put": compact_spread(top_bull_put),
        "top_bear_call": compact_spread(top_bear_call),
    }


def build_alerts(qualified, min_score=65, min_consistency=3):
    alerts = []

    allowed_volatility_contexts = {"rich_premium", "balanced_premium"}

    for spread in qualified:
        if (
            spread["label"] == "High Quality"
            and spread.get("adjusted_score", 0) >= min_score
            and spread.get("consistency_bonus", 0) >= min_consistency
            and spread.get("volatility_context") in allowed_volatility_contexts
        ):
            alerts.append(spread)

    return alerts

def filter_results(results, min_score=65, min_consistency=3):
    qualified = []
    near_miss = []
    ticker_diagnostics = []

    for ticker_result in results:
        ticker_diagnostics.append(
            {
                "ticker": ticker_result["ticker"],
                "bull_put_available": ticker_result["bull_put_available"],
                "bear_call_available": ticker_result["bear_call_available"],
            }
        )

        for spread_key in ["bull_put_spread", "bear_call_spread"]:
            spread = ticker_result[spread_key]

            if spread is None:
                continue

            if spread["label"] == "High Quality":
                qualified.append(spread)
            elif spread["label"] == "Near Miss":
                near_miss.append(spread)

    qualified.sort(
        key=lambda s: s.get("adjusted_score", s["score"]),
        reverse=True,
    )
    near_miss.sort(
        key=lambda s: s.get("adjusted_score", s["score"]),
        reverse=True,
    )

    summary = build_summary(qualified, near_miss)
    alerts = build_alerts(
                qualified,
                min_score=min_score,
                min_consistency=min_consistency
            )

    return {
        "summary": summary,
        "alerts": alerts,
        "qualified": qualified,
        "near_miss": near_miss,
        "ticker_diagnostics": ticker_diagnostics,
    }