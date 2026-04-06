
from pathlib import Path
from engine import run_scan_engine
from history import compute_trend_insights
from ui.components import (
    render_metric_row,
    render_trade_header,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
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


def run_scan(profile, ticker_group, dte_min, dte_max, min_score, min_consistency):
    return run_scan_engine(
        profile_name=profile,
        group_name=ticker_group,
        dte_min=dte_min,
        dte_max=dte_max,
        min_score=min_score,
        min_consistency=min_consistency,
        export_csv=False,
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
            f"Current assessment: {opportunity_label}."
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
        render_top_decision_panel(
            top_overall,
            summary.get("qualified_count", len(qualified)),
            qualified[0] if qualified else None,
        )
        render_system_signals(output)
        render_trade_lifecycle()

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