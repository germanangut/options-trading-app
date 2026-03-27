def build_summary(qualified, near_miss):
    top_overall = qualified[0] if qualified else None

    bull_puts = [s for s in qualified if s["strategy_type"] == "bull put spread"]
    bear_calls = [s for s in qualified if s["strategy_type"] == "bear call spread"]

    top_bull_put = bull_puts[0] if bull_puts else None
    top_bear_call = bear_calls[0] if bear_calls else None

    return {
        "qualified_count": len(qualified),
        "near_miss_count": len(near_miss),
        "top_overall": top_overall,
        "top_bull_put": top_bull_put,
        "top_bear_call": top_bear_call,
    }


def build_alerts(qualified):
    alerts = []

    for spread in qualified:
        if (
            spread["label"] == "High Quality"
            and spread.get("adjusted_score", 0) >= 65
            and spread.get("consistency_bonus", 0) >= 3
        ):
            alerts.append(spread)

    return alerts


def filter_results(results):
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

    # sorting
    qualified.sort(
        key=lambda s: s.get("adjusted_score", s["score"]),
        reverse=True,
    )
    near_miss.sort(
        key=lambda s: s.get("adjusted_score", s["score"]),
        reverse=True,
    )

    summary = build_summary(qualified, near_miss)
    alerts = build_alerts(qualified)

    return {
        "summary": summary,
        "alerts": alerts,
        "qualified": qualified,
        "near_miss": near_miss,
        "ticker_diagnostics": ticker_diagnostics,
    }