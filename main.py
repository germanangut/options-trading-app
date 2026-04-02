import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config_loader import load_config
from data_provider import get_market_data, is_cached_market_data_available
from decisions import classify_spread
from exporter import export_alerts_to_csv
from history import save_scan
from metrics import evaluate_spread
from output import filter_results
from profiles import PROFILES
from selection import select_leg
from spreads import build_spread
from ticker_groups import TICKER_GROUPS


DEBUG_MODE = "--debug" in sys.argv
ALERTS_ONLY_MODE = "--alerts-only" in sys.argv
EXPORT_CSV_MODE = "--export-csv" in sys.argv
COMPACT_MODE = "--compact" in sys.argv
EXPLAIN_SCORE_MODE = "--explain-score" in sys.argv
DAILY_SUMMARY_MODE = "--daily-summary" in sys.argv


def progress_print(message):
    print(message, file=sys.stderr, flush=True)


def has_cli_flag(flag_name):
    return flag_name in sys.argv


def has_any_scoring_override():
    scoring_flags = [
        "--pop-weight",
        "--ror-weight",
        "--min-score",
        "--min-consistency",
    ]
    return any(flag in sys.argv for flag in scoring_flags)


def get_top_n_arg():
    if "--top" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--top")
        value = int(sys.argv[idx + 1])
        if value <= 0:
            return None
        return value
    except (IndexError, ValueError):
        return None


def get_tickers_arg(default_tickers):
    if "--tickers" not in sys.argv:
        return default_tickers

    try:
        idx = sys.argv.index("--tickers")
        raw_value = sys.argv[idx + 1]
        tickers = [t.strip().upper() for t in raw_value.split(",") if t.strip()]
        return tickers if tickers else default_tickers
    except IndexError:
        return default_tickers


def get_group_arg():
    if "--group" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--group")
        group_name = sys.argv[idx + 1].lower()
        return group_name if group_name in TICKER_GROUPS else None
    except IndexError:
        return None


def get_profile_arg():
    if "--profile" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--profile")
        profile_name = sys.argv[idx + 1].lower()
        return profile_name if profile_name in PROFILES else None
    except IndexError:
        return None


def get_float_arg(flag_name, default_value=None):
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


def get_int_arg(flag_name, default_value=None):
    if flag_name not in sys.argv:
        return default_value

    try:
        idx = sys.argv.index(flag_name)
        value = int(sys.argv[idx + 1])
        if value < 0:
            return default_value
        return value
    except (IndexError, ValueError):
        return default_value


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
        evaluate_spread(
            bull_put_spread,
            pop_weight=pop_weight,
            ror_weight=ror_weight,
        )
    )
    bear_call_spread = classify_spread(
        evaluate_spread(
            bear_call_spread,
            pop_weight=pop_weight,
            ror_weight=ror_weight,
        )
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

    trimmed = dict(filtered)
    trimmed["qualified"] = filtered.get("qualified", [])[:top_n]
    trimmed["near_miss"] = filtered.get("near_miss", [])[:top_n]
    trimmed["alerts"] = filtered.get("alerts", [])[:top_n]

    summary = dict(trimmed.get("summary", {}))
    summary["top_n_applied"] = top_n
    trimmed["summary"] = summary

    return trimmed


def build_alerts_only_output(filtered):
    return {
        "summary": filtered.get("summary"),
        "alerts": filtered.get("alerts", []),
        "provider": filtered.get("provider"),
        "provider_errors": filtered.get("provider_errors", []),
        "missing_tickers": filtered.get("missing_tickers", []),
        "execution_time_seconds": filtered.get("execution_time_seconds"),
        "profile": filtered.get("profile"),
        "ticker_group": filtered.get("ticker_group"),
        "scoring_weights": filtered.get("scoring_weights"),
        "alert_thresholds": filtered.get("alert_thresholds"),
        "dte_range": filtered.get("dte_range"),
        "alerts_export_path": filtered.get("alerts_export_path"),
    }

def format_compact_spread(spread, index=None):
    if not spread:
        return ""

    prefix = f"{index}. " if index is not None else ""
    header = (
        f"{prefix}{spread.get('ticker')} | {spread.get('strategy_type')} | "
        f"Adjusted {spread.get('adjusted_score')}"
    )
    details = (
        f"   POP {spread.get('POP')} | ROR {spread.get('ROR')} | "
        f"DTE {spread.get('DTE')} | Premium {spread.get('volatility_context')}"
    )
    summary = f"   {spread.get('decision_summary', '')}"
    return "\n".join([header, details, summary])


def build_compact_output(filtered):
    lines = []

    summary = filtered.get("summary", {})
    qualified = filtered.get("qualified", [])
    top_overall = qualified[0] if qualified else None

    lines.append("SUMMARY")
    lines.append(f"Qualified: {summary.get('qualified_count', 0)}")
    lines.append(f"Near Miss: {summary.get('near_miss_count', 0)}")

    if top_overall:
        lines.append("")
        lines.append("TOP OVERALL")
        lines.append(format_compact_spread(top_overall))

    alerts = filtered.get("alerts", [])
    if alerts:
        lines.append("")
        lines.append("ALERTS")
        for i, spread in enumerate(alerts, start=1):
            lines.append(format_compact_spread(spread, index=i))
    else:
        lines.append("")
        lines.append("ALERTS")
        lines.append("No alerts")

    return "\n".join(lines)

def format_explain_score_spread(spread, index=None):
    if not spread:
        return ""

    sb = spread.get("score_breakdown", {})
    penalties = spread.get("penalties", {})

    prefix = f"{index}. " if index is not None else ""
    lines = [
        f"{prefix}{spread.get('ticker')} | {spread.get('strategy_type')}",
        f"Adjusted Score: {spread.get('adjusted_score')}",
        f"Base Score: {spread.get('score')}",
        f"Consistency Bonus: {spread.get('consistency_bonus')}",
        f"Volatility Boost: {spread.get('volatility_boost', 0.0)}",
        f"Total Penalty: {penalties.get('total_penalty', 0.0)}",
        "",
        f"POP Component: {sb.get('pop_component')}",
        f"ROR Component: {sb.get('ror_component')}",
        f"Premium/Width: {sb.get('premium_to_width')}",
        f"Volatility Context: {sb.get('volatility_context')}",
        "",
        "Penalties:",
        f"- Liquidity: {penalties.get('liquidity_penalty', 0.0)}",
        f"- Width: {penalties.get('width_penalty', 0.0)}",
        f"- Volatility: {penalties.get('volatility_penalty', 0.0)}",
        "",
        f"Decision: {spread.get('decision_summary', '')}",
    ]
    return "\n".join(lines)

def build_explain_score_output(filtered):
    lines = []

    alerts = filtered.get("alerts", [])
    qualified = filtered.get("qualified", [])

    lines.append("EXPLAIN SCORE")

    if alerts:
        lines.append("")
        lines.append("ALERTS")
        for i, spread in enumerate(alerts, start=1):
            lines.append(format_explain_score_spread(spread, index=i))
            lines.append("")
    else:
        lines.append("")
        lines.append("ALERTS")
        lines.append("No alerts")
        lines.append("")

    lines.append("TOP QUALIFIED")
    for i, spread in enumerate(qualified[:3], start=1):
        lines.append(format_explain_score_spread(spread, index=i))
        lines.append("")

    return "\n".join(lines).strip()

def format_summary_line(spread, index=None):
    if not spread:
        return ""

    prefix = f"{index}. " if index is not None else ""
    return (
        f"{prefix}{spread.get('ticker')} | {spread.get('strategy_type')} | "
        f"Adjusted {spread.get('adjusted_score')}"
    )

def build_daily_summary_output(filtered):
    lines = []

    summary = filtered.get("summary", {})
    alerts = filtered.get("alerts", [])
    top_overall = summary.get("top_overall")
    dte_range = filtered.get("dte_range", {})
    profile = filtered.get("profile")
    ticker_group = filtered.get("ticker_group")
    execution_time = filtered.get("execution_time_seconds")

    lines.append("DAILY SUMMARY")
    lines.append("")

    lines.append("Run Context")
    lines.append(f"- Profile: {profile}")
    lines.append(f"- Ticker Group: {ticker_group}")
    lines.append(
        f"- DTE Range: {dte_range.get('dte_min')}-{dte_range.get('dte_max')}"
    )
    lines.append(f"- Execution Time: {execution_time}s")
    lines.append("")

    lines.append("Scan Overview")
    lines.append(f"- Qualified Trades: {summary.get('qualified_count', 0)}")
    lines.append(f"- Near Misses: {summary.get('near_miss_count', 0)}")
    lines.append(f"- Alerts: {len(alerts)}")
    lines.append("")

    if top_overall:
        lines.append("Top Overall")
        lines.append(format_compact_spread(top_overall))
        lines.append("")

    lines.append("Alerts")
    if alerts:
        for i, spread in enumerate(alerts, start=1):
            lines.append(format_summary_line(spread, index=i))
    else:
        lines.append("No alerts")
    lines.append("")

    # Simple narrative takeaway
    rich_count = sum(
        1 for spread in alerts if spread.get("volatility_context") == "rich_premium"
    )
    balanced_count = sum(
        1 for spread in alerts if spread.get("volatility_context") == "balanced_premium"
    )

    if rich_count > 0:
        takeaway = (
            f"The strongest current opportunities include {rich_count} rich-premium "
            f"alert(s), suggesting unusually attractive pricing in this run."
        )
    elif balanced_count > 0:
        takeaway = (
            "The strongest current opportunities are balanced-premium setups with "
            "solid POP and manageable friction. No rich-premium setups were identified "
            "in this run."
        )
    else:
        takeaway = (
            "No high-priority opportunities were identified in this run. The market may "
            "not be offering attractive premium conditions right now."
        )

    lines.append("Takeaway")
    lines.append(takeaway)

    return "\n".join(lines)

def main():
    config = load_config()

    cli_tickers_provided = has_cli_flag("--tickers")
    cli_group_provided = has_cli_flag("--group")
    cli_profile_provided = has_cli_flag("--profile")
    cli_scoring_override_provided = has_any_scoring_override()

    default_tickers = ["TSLA", "META", "NVDA"]
    top_n = get_top_n_arg()

    # Profile source
    profile_name = get_profile_arg() or config.get("profile")
    profile_config = PROFILES.get(profile_name) if profile_name else None

    # Ticker/group precedence:
    # 1. explicit CLI tickers
    # 2. explicit CLI group
    # 3. config group
    # 4. default tickers
    config_group_name = config.get("ticker_group")
    group_name = None

    if cli_tickers_provided:
        tickers = get_tickers_arg(default_tickers)
    elif cli_group_provided:
        group_name = get_group_arg()
        tickers = TICKER_GROUPS[group_name] if group_name else default_tickers
    elif config_group_name and config_group_name in TICKER_GROUPS:
        group_name = config_group_name
        tickers = TICKER_GROUPS[group_name]
    else:
        tickers = default_tickers

    # Raw CLI values first
    pop_weight = get_float_arg("--pop-weight", None)
    ror_weight = get_float_arg("--ror-weight", None)
    min_score = get_int_arg("--min-score", None)
    min_consistency = get_int_arg("--min-consistency", None)

    if cli_profile_provided and profile_config:
        # Explicit CLI profile beats config, unless specific CLI scoring flags were also provided
        pop_weight = pop_weight if pop_weight is not None else profile_config["pop_weight"]
        ror_weight = ror_weight if ror_weight is not None else profile_config["ror_weight"]
        min_score = min_score if min_score is not None else profile_config["min_score"]
        min_consistency = (
            min_consistency
            if min_consistency is not None
            else profile_config["min_consistency"]
        )

        # If anything still missing, fall back to config
        pop_weight = pop_weight if pop_weight is not None else config.get("pop_weight")
        ror_weight = ror_weight if ror_weight is not None else config.get("ror_weight")
        min_score = min_score if min_score is not None else config.get("min_score")
        min_consistency = (
            min_consistency if min_consistency is not None else config.get("min_consistency")
        )
    else:
        # Normal case: CLI > config > profile defaults
        pop_weight = pop_weight if pop_weight is not None else config.get("pop_weight")
        ror_weight = ror_weight if ror_weight is not None else config.get("ror_weight")
        min_score = min_score if min_score is not None else config.get("min_score")
        min_consistency = (
            min_consistency if min_consistency is not None else config.get("min_consistency")
        )

        if profile_config:
            pop_weight = pop_weight if pop_weight is not None else profile_config["pop_weight"]
            ror_weight = ror_weight if ror_weight is not None else profile_config["ror_weight"]
            min_score = min_score if min_score is not None else profile_config["min_score"]
            min_consistency = (
                min_consistency
                if min_consistency is not None
                else profile_config["min_consistency"]
            )

    # Final fallback defaults
    pop_weight = 0.6 if pop_weight is None else pop_weight
    ror_weight = 0.4 if ror_weight is None else ror_weight
    min_score = 65 if min_score is None else min_score
    min_consistency = 3 if min_consistency is None else min_consistency

    # Hide profile in logs/output if explicit scoring overrides were used
    effective_profile_name = None if cli_scoring_override_provided else profile_name

    # DTE config support
    dte_min = config.get("dte_min", 30)
    dte_max = config.get("dte_max", 45)

    overall_start = time.time()
    progress_print(f"Starting scan for {len(tickers)} tickers...")

    if effective_profile_name:
        progress_print(f"Using profile: {effective_profile_name}")

    if group_name:
        progress_print(f"Using ticker group: {group_name}")

    progress_print(f"Scoring weights -> POP: {pop_weight}, ROR: {ror_weight}")
    progress_print(f"Alert thresholds -> Score: {min_score}, Consistency: {min_consistency}")
    progress_print(f"DTE range -> Min: {dte_min}, Max: {dte_max}")

    if is_cached_market_data_available(tickers, dte_min=dte_min, dte_max=dte_max):
        progress_print("Using cached market data...")
    else:
        progress_print("Fetching fresh market data...")

    provider_start = time.time()
    provider_result = get_market_data(
        tickers,
        dte_min=dte_min,
        dte_max=dte_max,
    )
    provider_elapsed = time.time() - provider_start
    progress_print(f"Market data retrieval completed in {provider_elapsed:.2f}s")

    data = provider_result["market_data"]
    missing_tickers = provider_result["missing_tickers"]
    provider_name = provider_result["provider"]
    provider_errors = provider_result.get("provider_errors", [])

    results = []
    available_tickers = list(data.keys())
    max_workers = min(5, len(available_tickers)) if available_tickers else 1

    progress_print(f"Running with {max_workers} parallel workers...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for ticker in available_tickers:
            progress_print(f"[SUBMITTED] {ticker}")
            future = executor.submit(
                process_ticker,
                ticker,
                data[ticker],
                pop_weight,
                ror_weight,
            )
            futures[future] = ticker

        for future in as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
                results.append(result)
                progress_print(f"[DONE] {ticker}")
            except Exception as e:
                progress_print(f"[ERROR] {ticker}: {str(e)}")

    filtered = filter_results(
        results,
        min_score=min_score,
        min_consistency=min_consistency,
    )

    save_scan(filtered)

    filtered = apply_top_n(filtered, top_n)

    filtered["missing_tickers"] = missing_tickers
    filtered["provider"] = provider_name
    filtered["provider_errors"] = provider_errors
    filtered["execution_time_seconds"] = round(time.time() - overall_start, 2)
    filtered["profile"] = effective_profile_name
    filtered["ticker_group"] = group_name

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

    if EXPORT_CSV_MODE:
        exported_alerts_path = export_alerts_to_csv(filtered.get("alerts", []))
        filtered["alerts_export_path"] = exported_alerts_path
        progress_print(f"Alerts exported to {exported_alerts_path}")
    else:
        filtered["alerts_export_path"] = None

    total_elapsed = time.time() - overall_start
    progress_print(f"Total execution time: {total_elapsed:.2f}s")

    if ALERTS_ONLY_MODE:
        filtered = build_alerts_only_output(filtered)

    if COMPACT_MODE and not DEBUG_MODE:
        print(build_compact_output(filtered))
    elif EXPLAIN_SCORE_MODE and not DEBUG_MODE:
        print(build_explain_score_output(filtered))
    elif DAILY_SUMMARY_MODE and not DEBUG_MODE:
        print(build_daily_summary_output(filtered))
    else:
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