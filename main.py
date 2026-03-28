import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_provider import get_market_data, is_cached_market_data_available
from selection import select_leg
from spreads import build_spread
from metrics import evaluate_spread
from decisions import classify_spread
from output import filter_results
from history import save_scan
from exporter import export_alerts_to_csv



DEBUG_MODE = "--debug" in sys.argv
ALERTS_ONLY_MODE = "--alerts-only" in sys.argv
EXPORT_CSV_MODE = "--export-csv" in sys.argv


def get_top_n_arg():
    if "--top" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--top")
        value = sys.argv[idx + 1]
        top_n = int(value)

        if top_n <= 0:
            return None

        return top_n
    except (IndexError, ValueError):
        return None


def get_tickers_arg(default_tickers):
    if "--tickers" not in sys.argv:
        return default_tickers

    try:
        idx = sys.argv.index("--tickers")
        raw_value = sys.argv[idx + 1]

        tickers = [t.strip().upper() for t in raw_value.split(",") if t.strip()]

        if not tickers:
            return default_tickers

        return tickers

    except IndexError:
        return default_tickers


def get_float_arg(flag_name, default_value):
    if flag_name not in sys.argv:
        return default_value

    try:
        idx = sys.argv.index(flag_name)
        value = float(sys.argv[idx + 1])

        if value < 0:
            return default_value

        return value
    except (IndexError, ValueError):
        return default_value


TOP_N = get_top_n_arg()
POP_WEIGHT = get_float_arg("--pop-weight", 0.6)
ROR_WEIGHT = get_float_arg("--ror-weight", 0.4)


def progress_print(message):
    print(message, file=sys.stderr, flush=True)


def process_ticker(ticker, ticker_data, pop_weight, ror_weight):
    contracts = ticker_data["contracts"]
    underlying_price = ticker_data["underlying_price"]
    expiration_date = ticker_data["expiration_date"]
    dte = ticker_data["DTE"]
    provider_diagnostics = ticker_data.get("provider_diagnostics", {})

    if not contracts:
        return {
            "ticker": ticker,
            "bull_put_spread": None,
            "bear_call_spread": None,
            "bull_put_available": False,
            "bear_call_available": False,
            "selected_legs": {
                "short_put": None,
                "long_put": None,
                "short_call": None,
                "long_call": None,
            },
            "provider_diagnostics": provider_diagnostics,
        }

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

    bull_put_spread = classify_spread(
        evaluate_spread(bull_put_spread, pop_weight=pop_weight, ror_weight=ror_weight)
    )
    bear_call_spread = classify_spread(
        evaluate_spread(bear_call_spread, pop_weight=pop_weight, ror_weight=ror_weight)
    )

    return {
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
        "provider_diagnostics": provider_diagnostics,
    }


def apply_top_n(filtered, top_n):
    if top_n is None:
        return filtered

    filtered = dict(filtered)

    qualified = filtered.get("qualified", [])
    near_miss = filtered.get("near_miss", [])
    alerts = filtered.get("alerts", [])

    filtered["qualified"] = qualified[:top_n]
    filtered["near_miss"] = near_miss[:top_n]
    filtered["alerts"] = alerts[:top_n]

    summary = dict(filtered.get("summary", {}))
    if summary:
        summary["top_n_applied"] = top_n
    filtered["summary"] = summary

    return filtered


def build_alerts_only_output(filtered):
    return {
        "summary": filtered.get("summary"),
        "alerts": filtered.get("alerts", []),
        "provider": filtered.get("provider"),
        "provider_errors": filtered.get("provider_errors", []),
        "missing_tickers": filtered.get("missing_tickers", []),
        "execution_time_seconds": filtered.get("execution_time_seconds"),
    }


def main():
    default_tickers = ["TSLA", "META", "NVDA"]
    tickers = get_tickers_arg(default_tickers)

    overall_start = time.time()
    progress_print(f"Starting scan for {len(tickers)} tickers...")
    progress_print(f"Scoring weights -> POP: {POP_WEIGHT}, ROR: {ROR_WEIGHT}")

    if is_cached_market_data_available(tickers):
        progress_print("Using cached market data...")
    else:
        progress_print("Fetching fresh market data...")

    provider_start = time.time()
    provider_result = get_market_data(tickers)
    provider_elapsed = time.time() - provider_start
    progress_print(f"Market data retrieval completed in {provider_elapsed:.2f}s")

    data = provider_result["market_data"]
    missing_tickers = provider_result["missing_tickers"]
    provider_name = provider_result["provider"]
    provider_errors = provider_result.get("provider_errors", [])

    results = []

    available_tickers = list(data.keys())
    total_available = len(available_tickers)
    max_workers = min(5, total_available) if total_available > 0 else 1

    progress_print(f"Running with {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for ticker in available_tickers:
            progress_print(f"[SUBMITTED] {ticker}")
            futures[executor.submit(process_ticker, ticker, data[ticker], POP_WEIGHT, ROR_WEIGHT)] = ticker

        for future in as_completed(futures):
            ticker = futures[future]

            try:
                result = future.result()
                results.append(result)
                progress_print(f"[DONE] {ticker}")
            except Exception as e:
                progress_print(f"[ERROR] {ticker}: {str(e)}")

    filtered = filter_results(results)
    filtered["missing_tickers"] = missing_tickers
    filtered["provider"] = provider_name
    filtered["provider_errors"] = provider_errors
    filtered["execution_time_seconds"] = round(time.time() - overall_start, 2)
    filtered["scoring_weights"] = {
        "pop_weight": POP_WEIGHT,
        "ror_weight": ROR_WEIGHT,
    }

    save_scan(filtered)
    if EXPORT_CSV_MODE:
        exported_alerts_path = export_alerts_to_csv(filtered.get("alerts", []))
        filtered["alerts_export_path"] = exported_alerts_path

    filtered = apply_top_n(filtered, TOP_N)

    total_elapsed = time.time() - overall_start
    progress_print(f"Total execution time: {total_elapsed:.2f}s")

    if ALERTS_ONLY_MODE:
        filtered = build_alerts_only_output(filtered)

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