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

    qualified.sort(key=lambda spread: spread["score"], reverse=True)
    near_miss.sort(key=lambda spread: spread["score"], reverse=True)

    return {
        "qualified": qualified,
        "near_miss": near_miss,
        "ticker_diagnostics": ticker_diagnostics,
    }