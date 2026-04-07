
from pathlib import Path
from engine import run_scan_engine
from history import compute_trend_insights, get_historical_intelligence_summary
from strategies import get_active_strategies
from ui.components import (
    render_metric_row,
    render_trade_header,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
    get_strategy_display_name,
)
from ui.qualified import render_qualified_trades
from ui.alerts import render_alerts
import streamlit as st


st.set_page_config(page_title="Options Trading App", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
MAIN_PY = BASE_DIR / "main.py"

st.title("Options Trading Dashboard")

st.sidebar.header("Run Configuration")

profile = st.sidebar.selectbox(
    "Profile",
    ["balanced", "aggressive", "conservative"],
    index=0,
)

ticker_group = st.sidebar.selectbox(
    "Ticker Group",
    ["tech", "index", "mixed"],
    index=0,
)

active_strategies = get_active_strategies()
active_strategy_keys = [strategy["key"] for strategy in active_strategies]
strategy_label_lookup = {
    strategy["key"]: strategy.get("display_label", strategy["key"]).replace("_", " ").title()
    for strategy in active_strategies
}

selected_strategy_keys = st.sidebar.multiselect(
    "Strategies",
    options=active_strategy_keys,
    default=active_strategy_keys,
    format_func=lambda key: strategy_label_lookup.get(key, key),
)

if not selected_strategy_keys:
    selected_strategy_keys = active_strategy_keys

st.sidebar.subheader("Advanced Controls")

dte_min = st.sidebar.number_input(
    "DTE Min",
    min_value=1,
    max_value=365,
    value=20,
    step=1,
)

dte_max = st.sidebar.number_input(
    "DTE Max",
    min_value=1,
    max_value=365,
    value=35,
    step=1,
)

min_score = st.sidebar.number_input(
    "Min Score",
    min_value=0,
    max_value=100,
    value=65,
    step=1,
)

min_consistency = st.sidebar.number_input(
    "Min Consistency",
    min_value=0,
    max_value=20,
    value=3,
    step=1,
)

run_button = st.sidebar.button("Run Scan")


def run_scan(
    profile,
    ticker_group,
    dte_min,
    dte_max,
    min_score,
    min_consistency,
    selected_strategy_keys,
):
    return run_scan_engine(
        profile_name=profile,
        group_name=ticker_group,
        dte_min=dte_min,
        dte_max=dte_max,
        min_score=min_score,
        min_consistency=min_consistency,
        export_csv=False,
        selected_strategy_keys=selected_strategy_keys,
    )


def get_trade_value(primary_spread, fallback_spread, key, default=None):
    """Prefer the summary trade value, then fall back to the top qualified trade."""
    if primary_spread and primary_spread.get(key) not in (None, ""):
        return primary_spread.get(key)

    if fallback_spread and fallback_spread.get(key) not in (None, ""):
        return fallback_spread.get(key)

    score_breakdown = (fallback_spread or {}).get("score_breakdown", {})
    if score_breakdown.get(key) not in (None, ""):
        return score_breakdown.get(key)

    return default


def get_opportunity_label(spread):
    """Return a lightweight presentation label based on the engine-provided score."""
    score = spread.get("adjusted_score") if spread else None

    if score is None:
        return "Opportunity available"
    if score >= 70:
        return "Strong opportunity"
    if score >= 60:
        return "Moderate opportunity"
    return "Weak opportunity"


def render_why_this_trade(primary_trade, detail_trade):
    """Render a concise explanation of why the highlighted trade surfaced."""
    adjusted_score = get_trade_value(primary_trade, detail_trade, "adjusted_score", "n/a")
    pop = get_trade_value(primary_trade, detail_trade, "POP", "n/a")
    ror = get_trade_value(primary_trade, detail_trade, "ROR", "n/a")
    stability_level = get_trade_value(primary_trade, detail_trade, "stability_level", "n/a")
    stability_count = get_trade_value(primary_trade, detail_trade, "stability_count", 0)
    volatility_context = get_trade_value(primary_trade, detail_trade, "volatility_context", "n/a")
    status_reason = get_trade_value(
        primary_trade,
        detail_trade,
        "status_reason",
        "No status reason provided.",
    )
    decision_summary = get_trade_value(
        primary_trade,
        detail_trade,
        "decision_summary",
        "No decision summary available.",
    )

    with st.container(border=True):
        st.markdown("#### Why This Trade")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Supportive Signals**")
            st.write(f"- Adjusted score: {adjusted_score}")
            st.write(f"- POP / ROR: {pop} / {ror}")
            st.write(f"- Stability: {stability_level} ({stability_count})")

        with col2:
            st.markdown("**Context to Watch**")
            st.write(f"- Premium context: {volatility_context}")
            st.write(f"- Qualification note: {status_reason}")

        st.markdown("**Decision View**")
        st.write(decision_summary)


def render_top_decision_panel(spread, qualified_count, fallback_spread=None):
    """Render a presentation-only summary for the best current trade."""
    st.subheader("Top Decision")

    if not spread and not fallback_spread:
        with st.container(border=True):
            st.info("No qualified trades were returned for this run.")
            st.caption(
                "Try widening the DTE range or lowering the minimum score/consistency thresholds."
            )
        return

    primary_trade = spread or fallback_spread or {}
    detail_trade = fallback_spread or primary_trade
    opportunity_label = get_opportunity_label(primary_trade)

    with st.container(border=True):
        st.markdown(
            f"### {get_trade_value(primary_trade, detail_trade, 'ticker', 'N/A')} | "
            f"{get_trade_value(primary_trade, detail_trade, 'strategy_type', 'Trade')}"
        )

        summary_text = (
            f"{qualified_count} qualified trade(s) identified in this run. "
            f"Current assessment under the active rules: {opportunity_label}."
        )

        if opportunity_label == "Strong opportunity":
            st.success(summary_text)
        elif opportunity_label == "Moderate opportunity":
            st.info(summary_text)
        else:
            st.warning(summary_text)

        render_metric_row(primary_trade)

        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Stability Level",
            get_trade_value(primary_trade, detail_trade, "stability_level", "n/a"),
        )
        col2.metric(
            "Stability Count",
            get_trade_value(primary_trade, detail_trade, "stability_count", 0),
        )
        col3.metric("Opportunity", opportunity_label)

        render_why_this_trade(primary_trade, detail_trade)


def render_system_signals(output):
    """Render compact system and scan-quality indicators from engine metadata."""
    st.subheader("System Signals")

    provider = output.get("provider") or "n/a"
    execution_time = output.get("execution_time_seconds")
    missing_tickers = output.get("missing_tickers") or []
    provider_errors = output.get("provider_errors") or []
    summary = output.get("summary", {})
    alerts = output.get("alerts") or []
    qualified = output.get("qualified") or []

    missing_count = len(missing_tickers)
    provider_error_count = len(provider_errors)
    qualified_count = summary.get("qualified_count", len(qualified))
    alerts_count = len(alerts)

    if provider_error_count > 0:
        health_message = "Provider issues detected. Treat this run as partially incomplete."
        health_type = "error"
    elif missing_count > 0:
        health_message = "Partial data coverage, interpret carefully."
        health_type = "warning"
    elif qualified_count > 0 or alerts_count > 0:
        health_message = "Healthy run with actionable candidates."
        health_type = "success"
    else:
        health_message = "Healthy run with no strong candidates."
        health_type = "info"

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Provider", provider)
        col2.metric(
            "Execution Time",
            f"{execution_time:.2f}s" if isinstance(execution_time, (int, float)) else "n/a",
        )
        col3.metric("Missing Tickers", missing_count)

        col4, col5, col6 = st.columns(3)
        col4.metric("Provider Errors", provider_error_count)
        col5.metric("Qualified Trades", qualified_count)
        col6.metric("Alerts", alerts_count)

        if health_type == "error":
            st.error(health_message)
        elif health_type == "warning":
            st.warning(health_message)
        elif health_type == "success":
            st.success(health_message)
        else:
            st.info(health_message)


def render_portfolio_signals(output):
    """Render a compact, descriptive summary of current-run exposure and concentration."""
    st.subheader("Portfolio Signals")

    exposure = output.get("portfolio_exposure_summary") or {}
    qualified_summary = exposure.get("qualified") or {}
    metadata = exposure.get("metadata") or {}

    qualified_count = metadata.get("qualified_trade_count", 0)
    if qualified_count == 0:
        with st.container(border=True):
            st.info("No qualified trades are available yet, so portfolio concentration signals are limited for this run.")
        return

    top_ticker = (qualified_summary.get("top_ticker_concentration") or [None])[0] or {}
    top_strategy = (qualified_summary.get("counts_by_strategy") or [None])[0] or {}
    top_direction = (qualified_summary.get("directional_exposure") or [None])[0] or {}

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Qualified Trades", qualified_count)
        col2.metric(
            "Top Ticker",
            top_ticker.get("ticker", "n/a"),
            f"{top_ticker.get('share_pct', 0)}%" if top_ticker else None,
        )
        col3.metric(
            "Top Strategy",
            top_strategy.get("strategy", "n/a"),
            f"{top_strategy.get('count', 0)} trade(s)" if top_strategy else None,
        )
        col4.metric(
            "Directional Tilt",
            str(top_direction.get("directional_bias", "n/a")).replace("_", " ").title(),
            f"{top_direction.get('share_pct', 0)}%" if top_direction else None,
        )

        notes = exposure.get("notes") or []
        if notes:
            for note in notes[:2]:
                st.write(f"- {note}")
        else:
            st.write("- Current qualified candidates look relatively diversified across the scanned set.")


def _normalize_history_value(value):
    return str(value or "").strip().replace("_", " ").lower()


def _find_history_row(rows, key_name, *candidates):
    normalized_candidates = {
        _normalize_history_value(candidate)
        for candidate in candidates
        if candidate not in (None, "")
    }

    if not normalized_candidates:
        return None

    for row in rows or []:
        if _normalize_history_value(row.get(key_name)) in normalized_candidates:
            return row

    return None


def render_historical_signal_context(primary_trade, fallback_trade=None):
    """Render concise, non-predictive context from stored signal history."""
    st.subheader("Historical Signal Context")

    if not primary_trade and not fallback_trade:
        with st.container(border=True):
            st.info("Historical context becomes available once a current top decision is present.")
        return

    detail_trade = fallback_trade or primary_trade or {}
    ticker = get_trade_value(primary_trade, detail_trade, "ticker", "N/A")
    raw_strategy = (
        get_trade_value(primary_trade, detail_trade, "strategy_label")
        or get_trade_value(primary_trade, detail_trade, "strategy_type")
        or get_trade_value(primary_trade, detail_trade, "strategy_key")
        or "Trade"
    )
    strategy_name = get_strategy_display_name(detail_trade or raw_strategy, default="Trade")
    volatility_context = get_trade_value(primary_trade, detail_trade, "volatility_context")
    stability_level = get_trade_value(primary_trade, detail_trade, "stability_level")

    intelligence_summary = get_historical_intelligence_summary(limit=25)
    metadata = intelligence_summary.get("metadata", {})
    history_summary = intelligence_summary.get("signal_quality_summary", {})
    feature_summary = intelligence_summary.get("feature_summary", {})
    runs_analyzed = metadata.get("runs_analyzed", history_summary.get("runs_analyzed", 0))
    signals_analyzed = metadata.get(
        "signals_analyzed",
        history_summary.get("signals_analyzed", 0),
    )

    if runs_analyzed == 0 or signals_analyzed == 0:
        with st.container(border=True):
            st.info(
                "Stored scan history is still limited. Run a few more scans to build additional context."
            )
        return

    ticker_row = _find_history_row(
        history_summary.get("most_frequent_qualified_tickers", []),
        "ticker",
        ticker,
    )
    strategy_row = _find_history_row(
        history_summary.get("most_frequent_qualified_strategies", []),
        "strategy",
        strategy_name,
        raw_strategy,
    )
    ticker_score_row = _find_history_row(
        history_summary.get("average_adjusted_score_by_ticker", []),
        "ticker",
        ticker,
    )
    strategy_score_row = _find_history_row(
        history_summary.get("average_adjusted_score_by_strategy", []),
        "strategy",
        strategy_name,
        raw_strategy,
    )
    pattern_row = _find_history_row(
        history_summary.get("recurring_high_quality_patterns", []),
        "pattern",
        f"{ticker} | {strategy_name}",
        f"{ticker} | {raw_strategy}",
    )
    pair_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_ticker_strategy_pair", []),
        "pair",
        f"{ticker} | {strategy_name}",
        f"{ticker} | {raw_strategy}",
    )
    volatility_row = _find_history_row(
        feature_summary.get("counts_by_volatility_context", []),
        "volatility_context",
        volatility_context,
    )
    volatility_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_volatility_context", []),
        "volatility_context",
        volatility_context,
    )
    stability_row = _find_history_row(
        feature_summary.get("counts_by_stability_level", []),
        "stability_level",
        stability_level,
    )
    stability_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_stability_level", []),
        "stability_level",
        stability_level,
    )

    with st.container(border=True):
        st.caption(
            "Uses stored scan history for context only. It does not estimate future outcomes or guarantee signal quality."
        )

        similar_signal_average = None
        if pair_score_row:
            similar_signal_average = pair_score_row.get("average_adjusted_score")
        elif ticker_score_row:
            similar_signal_average = ticker_score_row.get("average_adjusted_score")
        elif strategy_score_row:
            similar_signal_average = strategy_score_row.get("average_adjusted_score")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Runs Analyzed", runs_analyzed)
        col2.metric(
            "Pair Recurrence",
            pattern_row.get("count", "Limited") if pattern_row else "Limited",
        )
        col3.metric(
            "Similar Hist. Avg",
            similar_signal_average if similar_signal_average is not None else "Limited",
        )
        col4.metric(
            "Signals Logged",
            signals_analyzed,
        )

        context_notes = []

        if pattern_row:
            context_notes.append(
                f"**{ticker} | {strategy_name}** has appeared **{pattern_row.get('count', 0)}** time(s) in stored high-quality history."
            )
        else:
            context_notes.append(
                f"Direct history for **{ticker} | {strategy_name}** is still limited, so the current run should remain the primary input."
            )

        if volatility_context and volatility_row:
            volatility_average = None
            if volatility_score_row:
                volatility_average = volatility_score_row.get("average_adjusted_score")

            message = (
                f"The current premium context (**{volatility_context.replace('_', ' ')}**) appears in **{volatility_row.get('count', 0)}** stored signal(s)"
            )
            if volatility_average is not None:
                message += f", with an average adjusted score of **{volatility_average}**"
            message += "."
            context_notes.append(message)

        if stability_level and stability_row:
            stability_average = None
            if stability_score_row:
                stability_average = stability_score_row.get("average_adjusted_score")

            message = (
                f"Signals labeled **{stability_level}** appear **{stability_row.get('count', 0)}** time(s) in stored history"
            )
            if stability_average is not None:
                message += f", with an average adjusted score of **{stability_average}**"
            message += "."
            context_notes.append(message)

        for note in context_notes[:3]:
            st.write(f"- {note}")


def render_trade_lifecycle():
    """Show the user how to move through the existing app workflow."""
    st.subheader("Trade Lifecycle")

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 1. Scan")
            st.caption("Use **Alerts** to review fresh opportunities returned by the current run.")

        with col2:
            st.markdown("### 2. Select")
            st.caption("Use **Qualified Trades** to focus on the strongest current candidates.")

        with col3:
            st.markdown("### 3. Track")
            st.caption("Use **History** to understand recurring patterns and stability over time.")

        with col4:
            st.markdown("### 4. Outcome")
            st.caption("Use **Daily Summary** for the run-level interpretation and takeaways.")


def render_system_boundaries():
    """Communicate the app's analytical role and practical limits."""
    st.subheader("System Boundaries")

    with st.container(border=True):
        st.caption(
            "This app evaluates options opportunities using the current rules and available market data. "
            "Its outputs are intended for decision support, not automatic execution. Data/provider coverage can affect results, "
            "so final trade decisions should always use your own judgment."
        )


def render_trade_card(title, spread):
    if not spread:
        st.info(f"No {title.lower()} available.")
        return

    with st.container(border=True):
        st.subheader(title)
        st.markdown(
            f"**{spread.get('ticker')}** | {spread.get('strategy_type')} | "
            f"Premium: {spread.get('volatility_context')}"
        )
        render_metric_row(spread)

        st.markdown(
            f"**Strikes:** {spread.get('short_strike')} / {spread.get('long_strike')}"
        )
        render_stability_block(spread)
        render_decision_summary(spread)


def render_trend_insights():
    insights = compute_trend_insights()

    st.subheader("Trend Insights")

    runs_analyzed = insights.get('runs_analyzed', 0)
    st.markdown(f"**Runs analyzed:** {runs_analyzed}")

    if runs_analyzed == 0:
        with st.container(border=True):
            st.info(
                "No history yet. Run a few scans to start building recurring-pattern and stability context."
            )
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Top Tickers")
        top_tickers = insights.get("top_tickers", [])
        if top_tickers:
            for ticker, count in top_tickers:
                st.write(f"- {ticker} — {count}")
        else:
            st.info("No ticker history yet.")

    with col2:
        st.markdown("### Top Strategies")
        top_strategies = insights.get("top_strategies", [])
        if top_strategies:
            for strategy, count in top_strategies:
                st.write(f"- {strategy} — {count}")
        else:
            st.info("No strategy history yet.")

    with col3:
        st.markdown("### Recurring Alerts")
        recurring_alerts = insights.get("recurring_alerts", [])
        if recurring_alerts:
            for name, count in recurring_alerts:
                st.write(f"- {name} — {count}")
        else:
            st.info("No recurring alerts yet.")

def render_daily_summary(output):
    summary = output.get("summary", {})
    alerts = output.get("alerts", [])
    qualified = output.get("qualified", [])
    top_overall = summary.get("top_overall") or (qualified[0] if qualified else None)
    dte_range = output.get("dte_range", {})
    profile = output.get("profile")
    ticker_group = output.get("ticker_group")
    execution_time = output.get("execution_time_seconds")
    provider_errors = output.get("provider_errors", []) or []
    missing_tickers = output.get("missing_tickers", []) or []
    qualified_count = summary.get("qualified_count", len(qualified))
    alerts_count = len(alerts)

    stable_alerts = [s for s in alerts if s.get("stability_level") == "stable"]
    emerging_alerts = [s for s in alerts if s.get("stability_level") == "emerging"]
    new_alerts = [s for s in alerts if s.get("stability_level") == "new"]

    most_stable_alert = None
    if alerts:
        most_stable_alert = max(
            alerts,
            key=lambda s: s.get("stability_count", 0)
        )

    st.subheader("Daily Summary")

    summary_notice = None
    notice_type = None
    if provider_errors:
        summary_notice = (
            "This summary reflects a run with provider issues, so missing opportunities may be data-related."
        )
        notice_type = "warning"
    elif missing_tickers:
        summary_notice = (
            f"This summary reflects partial coverage: {len(missing_tickers)} ticker(s) were unavailable during the scan."
        )
        notice_type = "info"
    elif qualified_count == 0 and alerts_count == 0:
        summary_notice = (
            "This was a healthy run, but no strong opportunities cleared the current thresholds."
        )
        notice_type = "info"

    if summary_notice:
        with st.container(border=True):
            if notice_type == "warning":
                st.warning(summary_notice)
            else:
                st.info(summary_notice)

    with st.container(border=True):
        st.markdown("### Run Context")
        st.write(f"**Profile:** {profile}")
        st.write(f"**Ticker Group:** {ticker_group}")
        st.write(
            f"**DTE Range:** {dte_range.get('dte_min', '-')}-{dte_range.get('dte_max', '-')}"
        )
        st.write(f"**Execution Time:** {execution_time}s")

    with st.container(border=True):
        st.markdown("### Scan Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Qualified Trades", summary.get("qualified_count", 0))
        col2.metric("Near Misses", summary.get("near_miss_count", 0))
        col3.metric("Alerts", len(alerts))

    render_trade_card("Top Overall", top_overall)

    with st.container(border=True):
        st.markdown("### Stability Snapshot")
        st.write(f"**Stable Alerts:** {len(stable_alerts)}")
        st.write(f"**Emerging Alerts:** {len(emerging_alerts)}")
        st.write(f"**New Alerts:** {len(new_alerts)}")

        if most_stable_alert:
            st.write(
                "**Most Stable Alert:** "
                f"{most_stable_alert.get('ticker')} | "
                f"{most_stable_alert.get('strategy_type')} | "
                f"{most_stable_alert.get('stability_level')} "
                f"({most_stable_alert.get('stability_count')})"
            )
        else:
            st.write("**Most Stable Alert:** None")

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

    with st.container(border=True):
        st.markdown("### Takeaway")
        st.write(takeaway)


if run_button:
    with st.spinner("Running scan..."):
        output = run_scan(
            profile,
            ticker_group,
            dte_min,
            dte_max,
            min_score,
            min_consistency,
            selected_strategy_keys,
        )

    st.subheader("Execution Status")
    #st.write(f"Return code: {result.returncode}")

    summary = output.get("summary", {})
    alerts = output.get("alerts", [])
    qualified = output.get("qualified", [])
    top_overall = summary.get("top_overall") or (qualified[0] if qualified else None)

    st.success("Scan completed successfully.")

    tab_overview, tab_alerts, tab_qualified, tab_history, tab_summary, tab_raw = st.tabs(
            ["Overview", "Alerts", "Qualified Trades", "History", "Daily Summary", "Raw Output"]
        )

    with tab_overview:
        
        render_trade_lifecycle()
        render_portfolio_signals(output)
        render_top_decision_panel(
            top_overall,
            summary.get("qualified_count", len(qualified)), 
            qualified[0] if qualified else None,
        )
        render_historical_signal_context(
            top_overall,
            qualified[0] if qualified else None,
        )
        
        render_system_boundaries()
        render_system_signals(output)

        with st.expander("Run Metadata", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Execution Time", output.get("execution_time_seconds"))
            col2.metric("Profile", output.get("profile"))
            col3.metric("Ticker Group", output.get("ticker_group"))

            col4, col5, col6 = st.columns(3)
            dte_range = output.get("dte_range", {})
            alert_thresholds = output.get("alert_thresholds", {})
            scoring_weights = output.get("scoring_weights", {})

            col4.metric(
                "DTE Range",
                f"{dte_range.get('dte_min', '-')}-{dte_range.get('dte_max', '-')}"
            )
            col5.metric("Min Score", alert_thresholds.get("min_score"))
            col6.metric("POP Weight", scoring_weights.get("pop_weight"))

    with tab_alerts:
        render_alerts(
            alerts,
            provider_errors=output.get("provider_errors"),
            missing_tickers=output.get("missing_tickers"),
            qualified_count=summary.get("qualified_count", len(qualified)),
        )

    with tab_qualified:
        render_qualified_trades(
            qualified,
            provider_errors=output.get("provider_errors"),
            missing_tickers=output.get("missing_tickers"),
        )

    with tab_history:
        render_trend_insights()

    with tab_summary:
        render_daily_summary(output)

    with tab_raw:
        st.json(output)