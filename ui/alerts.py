"""Alerts UI rendering module."""

import streamlit as st
from ui.components import (
    get_strategy_display_name,
    render_metric_row,
    render_trade_header,
    render_strategy_context_row,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
)


def render_alerts(alerts, provider_errors=None, missing_tickers=None, qualified_count=0):
    """Render the alerts list with detailed cards.
    
    Args:
        alerts: List of alert dictionaries from engine
        provider_errors: Optional list of provider issues from the current run
        missing_tickers: Optional list of missing tickers from the current run
        qualified_count: Number of qualified trades from the current run
    """
    st.subheader("Alerts")

    provider_errors = provider_errors or []
    missing_tickers = missing_tickers or []
    missing_count = len(missing_tickers)

    if alerts:
        if provider_errors:
            st.warning(
                "Some provider issues were detected during this run, so alert coverage may be incomplete."
            )
        elif missing_count > 0:
            st.info(
                f"{missing_count} ticker(s) were unavailable during the scan, so this alert list may be partial."
            )

    if not alerts:
        if provider_errors:
            st.warning(
                "No alerts were produced because provider issues affected the run. Review the Overview tab before treating this as a weak market signal."
            )
        elif missing_count > 0:
            st.warning(
                f"No alerts were produced and {missing_count} ticker(s) were unavailable, so this run may be incomplete."
            )
        elif qualified_count > 0:
            st.info(
                "No high-priority alerts fired in this run, but there are still qualified trades worth reviewing."
            )
        else:
            st.info(
                "No alerts this run. That usually means nothing cleared the strongest opportunity thresholds under the current settings."
            )
        return

    with st.container(border=True):
        st.markdown("### Alert Summary")

        stable_count = sum(1 for alert in alerts if alert.get("stability_level") == "stable")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Alerts", len(alerts))
        col2.metric("Stable Alerts", stable_count)
        col3.metric("Qualified Trades", qualified_count)

        strategy_counts = {}
        for alert in alerts:
            strategy_name = get_strategy_display_name(alert)
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

        if strategy_counts:
            st.markdown("#### By Strategy")
            strategy_cols = st.columns(len(strategy_counts))
            for col, (strategy_name, count) in zip(strategy_cols, strategy_counts.items()):
                col.metric(strategy_name, count)

    for i, alert in enumerate(alerts, start=1):
        with st.container(border=True):
            render_trade_header(
                alert.get('ticker'),
                alert.get('strategy_type'),
                rank=i,
                spread=alert,
            )
            render_strategy_context_row(alert)
            render_metric_row(alert)

            st.markdown(
                f"**Premium Context:** {alert.get('volatility_context')}"
            )
            render_stability_block(alert)
            render_decision_summary(alert)

            render_json_expander(alert)