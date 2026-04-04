"""CLI entry point for options trading scanner."""

import json
import sys
from pathlib import Path

from config_loader import load_config
from engine import run_scan_engine
from history import compute_trend_insights
from output import build_summary
from profiles import PROFILES
from ticker_groups import TICKER_GROUPS


DEBUG_MODE = "--debug" in sys.argv
ALERTS_ONLY_MODE = "--alerts-only" in sys.argv
EXPORT_CSV_MODE = "--export-csv" in sys.argv
COMPACT_MODE = "--compact" in sys.argv
EXPLAIN_SCORE_MODE = "--explain-score" in sys.argv
DAILY_SUMMARY_MODE = "--daily-summary" in sys.argv
TREND_INSIGHTS_MODE = "--trend-insights" in sys.argv


def has_cli_flag(flag_name):
    """Check if a CLI flag is present."""
    return flag_name in sys.argv


def get_tickers_arg(default_tickers):
    """Get tickers from --tickers CLI argument."""
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
    """Get ticker group from --group CLI argument."""
    if "--group" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--group")
        group_name = sys.argv[idx + 1].lower()
        return group_name if group_name in TICKER_GROUPS else None
    except IndexError:
        return None


def get_profile_arg():
    """Get profile from --profile CLI argument."""
    if "--profile" not in sys.argv:
        return None

    try:
        idx = sys.argv.index("--profile")
        profile_name = sys.argv[idx + 1].lower()
        return profile_name if profile_name in PROFILES else None
    except IndexError:
        return None


def get_float_arg(flag_name, default_value=None):
    """Get float value from CLI argument."""
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
    """Get int value from CLI argument."""
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


def parse_arguments():
    """Parse CLI arguments and return configuration dict."""
    config = load_config()

    # Get basic parameters
    profile_name = get_profile_arg() or config.get("profile", "balanced")
    group_name = get_group_arg() or config.get("ticker_group", "tech")
    tickers = get_tickers_arg(None)  # None means use group/default

    # Get scoring parameters
    pop_weight = get_float_arg("--pop-weight")
    ror_weight = get_float_arg("--ror-weight")
    min_score = get_int_arg("--min-score")
    min_consistency = get_int_arg("--min-consistency")

    # Get DTE parameters
    dte_min = get_int_arg("--dte-min") or config.get("dte_min", 20)
    dte_max = get_int_arg("--dte-max") or config.get("dte_max", 35)

    return {
        "profile_name": profile_name,
        "group_name": group_name,
        "tickers": tickers,
        "dte_min": dte_min,
        "dte_max": dte_max,
        "min_score": min_score,
        "min_consistency": min_consistency,
        "pop_weight": pop_weight,
        "ror_weight": ror_weight,
        "export_csv": EXPORT_CSV_MODE,
    }


def build_alerts_only_output(filtered):
    """Build alerts-only output format."""
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
    """Format a spread for compact output."""
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
    """Build compact output format."""
    lines = []

    summary = filtered.get("summary", {})
    top_overall = filtered.get("qualified", [None])[0] if filtered.get("qualified") else None

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
    """Format a spread for explain-score output."""
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
        f"Stability Boost: {spread.get('stability_boost', 0.0)}",
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
    """Build explain-score output format."""
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


def format_stability_line(spread):
    """Format stability information for a spread."""
    if not spread:
        return "None"

    return (
        f"{spread.get('ticker')} | {spread.get('strategy_type')} | "
        f"{spread.get('stability_level')} ({spread.get('stability_count')})"
    )


def format_summary_line(spread, index=None):
    """Format summary line for a spread."""
    if not spread:
        return ""

    prefix = f"{index}. " if index is not None else ""

    return (
        f"{prefix}{spread.get('ticker')} | "
        f"{spread.get('strategy_type')} | "
        f"Adjusted {spread.get('adjusted_score')}"
    )


def build_daily_summary_output(filtered):
    """Build daily summary output format."""
    lines = []

    summary = filtered.get("summary", {})
    alerts = filtered.get("alerts", [])
    qualified = filtered.get("qualified", [])
    top_overall = qualified[0] if qualified else summary.get("top_overall")
    dte_range = filtered.get("dte_range", {})
    profile = filtered.get("profile")
    ticker_group = filtered.get("ticker_group")
    execution_time = filtered.get("execution_time_seconds")

    stable_alerts = [s for s in alerts if s.get("stability_level") == "stable"]
    emerging_alerts = [s for s in alerts if s.get("stability_level") == "emerging"]
    new_alerts = [s for s in alerts if s.get("stability_level") == "new"]

    most_stable_alert = None
    if alerts:
        most_stable_alert = max(
            alerts,
            key=lambda s: s.get("stability_count", 0)
        )

    lines.append("DAILY SUMMARY")
    lines.append("")

    lines.append("Run Context")
    lines.append(f"- Profile: {profile}")
    lines.append(f"- Ticker Group: {ticker_group}")
    lines.append(f"- DTE Range: {dte_range.get('dte_min')}-{dte_range.get('dte_max')}")
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

    lines.append("Stability Snapshot")
    lines.append(f"- Stable Alerts: {len(stable_alerts)}")
    lines.append(f"- Emerging Alerts: {len(emerging_alerts)}")
    lines.append(f"- New Alerts: {len(new_alerts)}")

    if most_stable_alert:
        lines.append(f"- Most Stable Alert: {format_stability_line(most_stable_alert)}")
    else:
        lines.append("- Most Stable Alert: None")
    lines.append("")

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


def build_trend_insights_output():
    """Build trend insights output format."""
    insights = compute_trend_insights()

    lines = []
    lines.append("TREND INSIGHTS")
    lines.append("")
    lines.append(f"Runs analyzed: {insights.get('runs_analyzed', 0)}")
    lines.append("")

    lines.append("Top Tickers")
    top_tickers = insights.get("top_tickers", [])
    if top_tickers:
        for i, (ticker, count) in enumerate(top_tickers, start=1):
            lines.append(f"{i}. {ticker} — {count} appearances")
    else:
        lines.append("No ticker history yet")
    lines.append("")

    lines.append("Top Strategies")
    top_strategies = insights.get("top_strategies", [])
    if top_strategies:
        for i, (strategy, count) in enumerate(top_strategies, start=1):
            lines.append(f"{i}. {strategy} — {count} appearances")
    else:
        lines.append("No strategy history yet")
    lines.append("")

    lines.append("Recurring Alerts")
    recurring_alerts = insights.get("recurring_alerts", [])
    if recurring_alerts:
        for i, (name, count) in enumerate(recurring_alerts, start=1):
            lines.append(f"{i}. {name} — {count} times")
    else:
        lines.append("No recurring alerts yet")

    return "\n".join(lines)


def main():
    """Main CLI entry point."""
    # Handle special modes
    if TREND_INSIGHTS_MODE:
        print(build_trend_insights_output())
        return

    # Parse arguments
    args = parse_arguments()

    # Run scan engine
    result = run_scan_engine(**args)

    # Output based on mode
    if COMPACT_MODE and not DEBUG_MODE:
        print(build_compact_output(result))
    elif EXPLAIN_SCORE_MODE and not DEBUG_MODE:
        print(build_explain_score_output(result))
    elif DAILY_SUMMARY_MODE and not DEBUG_MODE:
        print(build_daily_summary_output(result))
    elif ALERTS_ONLY_MODE and not DEBUG_MODE:
        print(json.dumps(build_alerts_only_output(result), indent=2))
    else:
        if DEBUG_MODE:
            # In debug mode, we don't have the raw results anymore
            # since they're processed in the engine
            output = result
        else:
            output = result

        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()