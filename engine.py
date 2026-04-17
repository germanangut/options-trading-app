import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from data_provider import get_market_data, is_cached_market_data_available
from backend.observability.logging import get_logger, log_event
from decisions import classify_spread
from exporter import export_alerts_to_csv
from history import save_scan, compute_alert_stability
from metrics import evaluate_spread
from output import filter_results, build_summary
from portfolio import (
    compute_portfolio_exposure_summary,
    compute_position_sizing_summary,
    compute_exposure_overlap_summary,
    compute_portfolio_decision_summary,
)
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


logger = get_logger(__name__)


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
    started_at = time.perf_counter()
    ticker_data = ticker_data or {}
    contracts = ticker_data.get("contracts") or []
    underlying_price = ticker_data.get("underlying_price")
    expiration_date = ticker_data.get("expiration_date")
    dte = ticker_data.get("DTE")
    provider_diagnostics = dict(ticker_data.get("provider_diagnostics") or {})
    selected_strategy_keys = set(resolve_selected_strategy_keys(selected_strategy_keys))

    strategy_errors = []

    def _empty_result(reason=None):
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
            "provider_diagnostics": {
                **provider_diagnostics,
                "strategy_errors": strategy_errors,
                "processing_duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "processing_error": reason,
            },
        }

    if not contracts:
        return _empty_result("No contracts were available for this ticker.")

    if underlying_price is None or expiration_date is None or dte is None:
        return _empty_result("Required market context was incomplete for this ticker.")

    short_put = select_leg(contracts, target_delta=-0.30, option_type="put")
    long_put = select_leg(contracts, target_delta=-0.20, option_type="put")
    short_call = select_leg(contracts, target_delta=0.30, option_type="call")
    long_call = select_leg(contracts, target_delta=0.20, option_type="call")

    def _evaluate_strategy(short_leg, long_leg, strategy_type, strategy_key):
        try:
            spread = build_spread(
                short_leg=short_leg,
                long_leg=long_leg,
                strategy_type=strategy_type,
                ticker=ticker,
                underlying_price=underlying_price,
                expiration_date=expiration_date,
                dte=dte,
            )
            spread = classify_spread(
                evaluate_spread(spread, pop_weight=pop_weight, ror_weight=ror_weight)
            )
            return apply_strategy_metadata(spread, strategy_key)
        except Exception as exc:
            strategy_errors.append(
                {
                    "strategy_key": strategy_key,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            log_event(
                logger,
                "scan_ticker_strategy_failed",
                ticker=ticker,
                strategy_key=strategy_key,
                error_type=type(exc).__name__,
            )
            return None

    bull_put_spread = None
    if BULL_PUT_SPREAD["key"] in selected_strategy_keys:
        bull_put_spread = _evaluate_strategy(
            short_put,
            long_put,
            BULL_PUT_SPREAD["display_label"],
            BULL_PUT_SPREAD["key"],
        )

    bear_call_spread = None
    if BEAR_CALL_SPREAD["key"] in selected_strategy_keys:
        bear_call_spread = _evaluate_strategy(
            short_call,
            long_call,
            BEAR_CALL_SPREAD["display_label"],
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
        "provider_diagnostics": {
            **provider_diagnostics,
            "strategy_errors": strategy_errors,
            "processing_duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            "processing_error": None,
        },
    }


def _empty_ticker_result(ticker, provider_diagnostics=None, error_message=None):
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
        "provider_diagnostics": {
            **(provider_diagnostics or {}),
            "processing_error": error_message,
        },
    }


def _merge_ticker_diagnostics(tickers, results, provider_ticker_diagnostics):
    result_map = {item["ticker"]: item for item in results}
    provider_diag_map = {
        item.get("ticker"): item for item in (provider_ticker_diagnostics or []) if item.get("ticker")
    }
    merged = []

    for ticker in tickers:
        result = result_map.get(ticker, _empty_ticker_result(ticker))
        provider_diag = provider_diag_map.get(ticker, {})
        provider_diagnostics = dict(provider_diag.get("provider_diagnostics") or {})
        processing_diagnostics = dict(result.get("provider_diagnostics") or {})

        merged.append(
            {
                "ticker": ticker,
                "bull_put_available": bool(result.get("bull_put_available")),
                "bear_call_available": bool(result.get("bear_call_available")),
                "provider_status": provider_diag.get("provider_status", "unknown"),
                "provider": provider_diag.get("provider"),
                "cache_hit": provider_diag.get("cache_hit", False),
                "duration_ms": provider_diag.get("duration_ms"),
                "provider_diagnostics": {
                    **provider_diagnostics,
                    **processing_diagnostics,
                },
            }
        )

    return merged


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
    persist_history=True,
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

    overall_started_at = time.perf_counter()

    provider_started_at = time.perf_counter()
    provider_result = get_market_data(
        tickers,
        dte_min=dte_min,
        dte_max=dte_max,
    )
    provider_duration_ms = round((time.perf_counter() - provider_started_at) * 1000, 2)

    data = provider_result["market_data"]
    missing_tickers = provider_result["missing_tickers"]
    provider_name = provider_result["provider"]
    provider_errors = provider_result.get("provider_errors", [])
    provider_ticker_diagnostics = provider_result.get("ticker_diagnostics", [])

    results = []
    available_tickers = list(data.keys())
    max_workers = min(5, len(available_tickers)) if available_tickers else 1
    processing_started_at = time.perf_counter()

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
            ticker = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                log_event(
                    logger,
                    "scan_ticker_failed",
                    level=40,
                    ticker=ticker,
                    error_type=type(exc).__name__,
                )
                result = _empty_ticker_result(
                    ticker,
                    provider_diagnostics={"ticker": ticker},
                    error_message=str(exc),
                )
            results.append(result)
            log_event(
                logger,
                "scan_ticker_completed",
                ticker=ticker,
                bull_put_available=bool(result.get("bull_put_available")),
                bear_call_available=bool(result.get("bear_call_available")),
                processing_duration_ms=(result.get("provider_diagnostics") or {}).get("processing_duration_ms"),
            )

    processing_duration_ms = round((time.perf_counter() - processing_started_at) * 1000, 2)

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
    filtered["position_sizing_summary"] = compute_position_sizing_summary(
        filtered,
    )
    filtered["exposure_overlap_summary"] = compute_exposure_overlap_summary(
        filtered,
    )
    filtered["portfolio_decision_summary"] = compute_portfolio_decision_summary(
        filtered,
    )

    filtered["missing_tickers"] = missing_tickers
    filtered["provider"] = provider_name
    filtered["provider_errors"] = provider_errors
    filtered["ticker_diagnostics"] = _merge_ticker_diagnostics(
        tickers,
        results,
        provider_ticker_diagnostics,
    )
    filtered["partial_result"] = bool(provider_errors or missing_tickers)
    filtered["cache"] = provider_result.get("cache", {})
    filtered["performance"] = {
        **(provider_result.get("performance", {}) or {}),
        "provider_duration_ms": provider_duration_ms,
        "processing_duration_ms": processing_duration_ms,
        "scan_duration_ms": round((time.perf_counter() - overall_started_at) * 1000, 2),
        "ticker_count": len(tickers),
        "available_ticker_count": len(available_tickers),
        "missing_ticker_count": len(missing_tickers),
        "provider_error_count": len(provider_errors),
    }
    filtered["execution_time_seconds"] = round((time.perf_counter() - overall_started_at), 2)
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

    if persist_history:
        save_scan(filtered)

    log_event(
        logger,
        "scan_engine_completed",
        profile=effective_profile_name,
        ticker_group=effective_group_name,
        ticker_count=len(tickers),
        qualified_count=len(filtered.get("qualified", [])),
        alerts_count=len(filtered.get("alerts", [])),
        partial_result=filtered["partial_result"],
        scan_duration_ms=filtered["performance"]["scan_duration_ms"],
        provider_duration_ms=filtered["performance"]["provider_duration_ms"],
        processing_duration_ms=filtered["performance"]["processing_duration_ms"],
    )

    return filtered
