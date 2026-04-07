import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_provider import get_market_data, is_cached_market_data_available
from decisions import classify_spread
from exporter import export_alerts_to_csv
from history import save_scan, compute_alert_stability
from metrics import evaluate_spread
from output import filter_results, build_summary
from portfolio import compute_portfolio_exposure_summary
from selection import select_leg
from settings import get_settings
from spreads import build_spread
from strategies import (
    BEAR_CALL_SPREAD,
    BULL_PUT_SPREAD,
    apply_strategy_metadata,
    get_active_strategies,
    get_strategy,
)
from ticker_groups import TICKER_GROUPS


def resolve_selected_strategy_keys(selected_strategy_keys=None):
    active_strategy_keys = [strategy["key"] for strategy in get_active_strategies()]

    if not selected_strategy_keys:
        return active_strategy_keys

    resolved_keys = []
    for strategy_key in selected_strategy_keys:
        strategy = get_strategy(strategy_key)
        if strategy is None:
            continue

        resolved_key = strategy["key"]
        if resolved_key in active_strategy_keys and resolved_key not in resolved_keys:
            resolved_keys.append(resolved_key)

    return resolved_keys or active_strategy_keys


def process_ticker(
    ticker,
    ticker_data,
    pop_weight,
    ror_weight,
    selected_strategy_keys=None,
):
    contracts = ticker_data["contracts"]
    underlying_price = ticker_data["underlying_price"]
    expiration_date = ticker_data["expiration_date"]
    dte = ticker_data["DTE"]
    provider_diagnostics = ticker_data.get("provider_diagnostics", {})
    selected_strategy_keys = set(resolve_selected_strategy_keys(selected_strategy_keys))

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

    bull_put_spread = None
    if BULL_PUT_SPREAD["key"] in selected_strategy_keys:
        bull_put_spread = build_spread(
            short_leg=short_put,
            long_leg=long_put,
            strategy_type=BULL_PUT_SPREAD["display_label"],
            ticker=ticker,
            underlying_price=underlying_price,
            expiration_date=expiration_date,
            dte=dte,
        )
        bull_put_spread = classify_spread(
            evaluate_spread(bull_put_spread, pop_weight=pop_weight, ror_weight=ror_weight)
        )
        bull_put_spread = apply_strategy_metadata(
            bull_put_spread,
            BULL_PUT_SPREAD["key"],
        )

    bear_call_spread = None
    if BEAR_CALL_SPREAD["key"] in selected_strategy_keys:
        bear_call_spread = build_spread(
            short_leg=short_call,
            long_leg=long_call,
            strategy_type=BEAR_CALL_SPREAD["display_label"],
            ticker=ticker,
            underlying_price=underlying_price,
            expiration_date=expiration_date,
            dte=dte,
        )
        bear_call_spread = classify_spread(
            evaluate_spread(bear_call_spread, pop_weight=pop_weight, ror_weight=ror_weight)
        )
        bear_call_spread = apply_strategy_metadata(
            bear_call_spread,
            BEAR_CALL_SPREAD["key"],
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


def enrich_spreads_with_stability(spreads, stability_map):
    for spread in spreads:
        key = f"{spread.get('ticker')}|{spread.get('strategy_type')}"
        stability_info = stability_map.get(key, {"count": 0, "stability": "new"})
        spread["stability_count"] = stability_info["count"]
        spread["stability_level"] = stability_info["stability"]


def compute_stability_boost(stability_level):
    if stability_level == "stable":
        return 1.0
    if stability_level == "emerging":
        return 0.5
    return 0.0


def apply_stability_boost(spreads):
    for spread in spreads:
        stability_level = spread.get("stability_level", "new")
        stability_boost = compute_stability_boost(stability_level)

        spread["stability_boost"] = round(stability_boost, 2)
        spread["adjusted_score"] = round(
            spread.get("adjusted_score", 0) + stability_boost, 2
        )

        if "score_breakdown" in spread:
            spread["score_breakdown"]["stability_boost"] = round(stability_boost, 2)
            spread["score_breakdown"]["adjusted_score"] = spread["adjusted_score"]


def run_scan_engine(
    profile_name="balanced",
    group_name="tech",
    tickers=None,
    dte_min=20,
    dte_max=35,
    min_score=65,
    min_consistency=3,
    pop_weight=None,
    ror_weight=None,
    export_csv=False,
    selected_strategy_keys=None,
):
    settings = get_settings(
        {
            "profile": profile_name,
            "ticker_group": group_name,
            "dte_min": dte_min,
            "dte_max": dte_max,
            "min_score": min_score,
            "min_consistency": min_consistency,
            "pop_weight": pop_weight,
            "ror_weight": ror_weight,
        }
    )

    effective_profile_name = settings.get("profile", profile_name)
    effective_group_name = settings.get("ticker_group", group_name)

    if tickers is None:
        tickers = TICKER_GROUPS.get(effective_group_name, ["TSLA", "META", "NVDA"])

    pop_weight = settings.get("pop_weight", pop_weight)
    ror_weight = settings.get("ror_weight", ror_weight)
    min_score = settings.get("min_score", min_score)
    min_consistency = settings.get("min_consistency", min_consistency)
    dte_min = settings.get("dte_min", dte_min)
    dte_max = settings.get("dte_max", dte_max)
    selected_strategy_keys = resolve_selected_strategy_keys(selected_strategy_keys)

    overall_start = time.time()

    provider_result = get_market_data(
        tickers,
        dte_min=dte_min,
        dte_max=dte_max,
    )

    data = provider_result["market_data"]
    missing_tickers = provider_result["missing_tickers"]
    provider_name = provider_result["provider"]
    provider_errors = provider_result.get("provider_errors", [])

    results = []
    available_tickers = list(data.keys())
    max_workers = min(5, len(available_tickers)) if available_tickers else 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for ticker in available_tickers:
            future = executor.submit(
                process_ticker,
                ticker,
                data[ticker],
                pop_weight,
                ror_weight,
                selected_strategy_keys,
            )
            futures[future] = ticker

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    filtered = filter_results(
        results,
        min_score=min_score,
        min_consistency=min_consistency,
    )

    stability_map = compute_alert_stability()
    enrich_spreads_with_stability(filtered.get("alerts", []), stability_map)
    enrich_spreads_with_stability(filtered.get("qualified", []), stability_map)

    apply_stability_boost(filtered.get("qualified", []))

    filtered["alerts"].sort(
        key=lambda s: s.get("adjusted_score", 0),
        reverse=True,
    )
    filtered["qualified"].sort(
        key=lambda s: s.get("adjusted_score", 0),
        reverse=True,
    )

    filtered["summary"] = build_summary(
        filtered.get("qualified", []),
        filtered.get("near_miss", []),
    )
    filtered["portfolio_exposure_summary"] = compute_portfolio_exposure_summary(
        filtered,
    )

    filtered["missing_tickers"] = missing_tickers
    filtered["provider"] = provider_name
    filtered["provider_errors"] = provider_errors
    filtered["execution_time_seconds"] = round(time.time() - overall_start, 2)
    filtered["profile"] = effective_profile_name
    filtered["ticker_group"] = effective_group_name
    filtered["selected_strategy_keys"] = list(selected_strategy_keys)
    filtered["scoring_weights"] = {
        "pop_weight": pop_weight,
        "ror_weight": ror_weight,
    }
    filtered["alert_thresholds"] = {
        "min_score": min_score,
        "min_consistency": min_consistency,
    }
    filtered["dte_range"] = {
        "dte_min": dte_min,
        "dte_max": dte_max,
    }

    if export_csv:
        filtered["alerts_export_path"] = export_alerts_to_csv(filtered.get("alerts", []))
    else:
        filtered["alerts_export_path"] = None

    save_scan(filtered)

    return filtered
