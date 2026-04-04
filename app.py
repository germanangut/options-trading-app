
from pathlib import Path
from engine import run_scan_engine
from history import compute_trend_insights
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


def render_metric_row(spread):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Adjusted Score", spread.get("adjusted_score"))
    col2.metric("POP", spread.get("POP"))
    col3.metric("ROR", spread.get("ROR"))
    col4.metric("DTE", spread.get("DTE"))


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
        st.markdown(
            f"**Stability:** {spread.get('stability_level', 'n/a')} "
            f"({spread.get('stability_count', 0)})"
        )
        st.markdown(
            f"**Decision Summary:** {spread.get('decision_summary', 'No summary available.')}"
        )


def render_alert_list(alerts):
    st.subheader("Alerts")

    if not alerts:
        st.info("No alerts returned.")
        return

    for i, alert in enumerate(alerts, start=1):
        with st.container(border=True):
            st.markdown(
                f"### {i}. {alert.get('ticker')} | {alert.get('strategy_type')}"
            )
            render_metric_row(alert)

            st.markdown(
                f"**Premium Context:** {alert.get('volatility_context')}"
            )
            st.markdown(
                f"**Stability:** {alert.get('stability_level', 'n/a')} "
                f"({alert.get('stability_count', 0)})"
            )
            st.markdown(
                f"**Decision Summary:** {alert.get('decision_summary', 'No summary available.')}"
            )

            with st.expander("More details"):
                st.json(alert)

def render_trend_insights():
    insights = compute_trend_insights()

    st.subheader("Trend Insights")

    st.markdown(f"**Runs analyzed:** {insights.get('runs_analyzed', 0)}")

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

def render_qualified_list(qualified):
    st.subheader("Qualified Trades")

    if not qualified:
        st.warning("No qualified trades matched the current settings.")
        st.caption("Try adjusting profile, DTE range, minimum score, or consistency threshold.")
        return

    # Qualified Summary section
    with st.container(border=True):
        st.markdown("### Qualified Summary")
        
        total_trades = len(qualified)
        stable_count = sum(1 for s in qualified if s.get("stability_level") == "stable")
        avg_score = sum(s.get("adjusted_score", 0) for s in qualified) / total_trades if total_trades > 0 else 0
        top_ticker = qualified[0].get("ticker") if qualified else "N/A"
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Qualified", total_trades)
        col2.metric("Stable Trades", stable_count)
        col3.metric("Avg Score", f"{avg_score:.1f}")
        col4.metric("Top Ticker", top_ticker)

    # Trade cards (respecting engine sort order)
    for i, spread in enumerate(qualified, start=1):
        with st.container(border=True):
            st.markdown(
                f"### {i}. {spread.get('ticker')} | {spread.get('strategy_type')}"
            )

            render_metric_row(spread)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f"**Strikes:** {spread.get('short_strike')} / {spread.get('long_strike')}"
                )
            with col2:
                if spread.get("expiration_date"):
                    st.markdown(f"**Expiration:** {spread.get('expiration_date')}")

            col3, col4 = st.columns(2)
            with col3:
                if spread.get("net_credit"):
                    st.markdown(f"**Net Credit:** {spread.get('net_credit')}")
            with col4:
                st.markdown(
                    f"**Premium Context:** {spread.get('volatility_context')}"
                )

            st.markdown(
                f"**Stability:** {spread.get('stability_level', 'n/a')} "
                f"({spread.get('stability_count', 0)})"
            )

            if spread.get("status_reason"):
                st.markdown(f"**Status:** {spread.get('status_reason')}")

            st.markdown(
                f"**Decision:** {spread.get('decision_summary', 'No summary available.')}"
            )

            with st.expander("More details"):
                st.json(spread)


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

        render_trade_card("Top Overall", top_overall)

    with tab_alerts:
        render_alert_list(alerts)

    with tab_qualified:
        render_qualified_list(qualified)

    with tab_history:
        render_trend_insights()

    with tab_summary:
        render_daily_summary(output)

    with tab_raw:
        st.json(output)