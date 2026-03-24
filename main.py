import json
import sys

from data_provider import get_market_data
from selection import select_leg
from spreads import build_spread
from metrics import evaluate_spread
from decisions import classify_spread
from output import filter_results


DEBUG_MODE = "--debug" in sys.argv


def process_ticker(ticker, ticker_data):
    contracts = ticker_data["contracts"]
    underlying_price = ticker_data["underlying_price"]
    expiration_date = ticker_data["expiration_date"]
    dte = ticker_data["DTE"]

    short_put = select_leg(contracts, target_delta=-0.30, option_type="put")
    long_put = select_leg(contracts, target_delta=-0.20, option_type="put")
    short_call = select_leg(contracts, target_delta=0.30, option_type="call")
    long_call = select_leg(contracts, target_delta=0.20, option_type="call")

    bull_put_spread = build_spread(
        short_leg=short_put,
        long_leg=long_put,
        strategy_type="bull put spread",
        ticker=ticker,
        underlying_price=underlying_price,
        expiration_date=expiration_date,
        dte=dte,
    )

    bear_call_spread = build_spread(
        short_leg=short_call,
        long_leg=long_call,
        strategy_type="bear call spread",
        ticker=ticker,
        underlying_price=underlying_price,
        expiration_date=expiration_date,
        dte=dte,
    )

    bull_put_spread = classify_spread(evaluate_spread(bull_put_spread))
    bear_call_spread = classify_spread(evaluate_spread(bear_call_spread))

    result = {
        "ticker": ticker,
        "bull_put_spread": bull_put_spread,
        "bear_call_spread": bear_call_spread,
        "bull_put_available": bull_put_spread is not None,
        "bear_call_available": bear_call_spread is not None,
        "selected_legs": {
            "short_put": short_put,
            "long_put": long_put,
            "short_call": short_call,
            "long_call": long_call,
        },
    }

    return result


def main():
    tickers = ["SPY", "QQQ", "AAPL", "IWM", "MSFT"]
    provider_result = get_market_data(tickers)

    data = provider_result["market_data"]
    missing_tickers = provider_result["missing_tickers"]
    provider_name = provider_result["provider"]
    provider_errors = provider_result.get("provider_errors", [])

    results = []

    for ticker, ticker_data in data.items():
        ticker_result = process_ticker(ticker, ticker_data)
        results.append(ticker_result)

    filtered = filter_results(results)
    filtered["missing_tickers"] = missing_tickers
    filtered["provider"] = provider_name
    filtered["provider_errors"] = provider_errors

    if DEBUG_MODE:
        output = {
            "user_view": filtered,
            "debug_view": results,
        }
    else:
        output = filtered

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()