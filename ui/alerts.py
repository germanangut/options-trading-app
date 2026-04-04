"""Alerts UI rendering module."""

import streamlit as st
from ui.components import (
    render_metric_row,
    render_trade_header,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
)


def render_alerts(alerts):
    """Render the alerts list with detailed cards.
    
    Args:
        alerts: List of alert dictionaries from engine
    """
    st.subheader("Alerts")

    if not alerts:
        st.info("No alerts returned.")
        return

    for i, alert in enumerate(alerts, start=1):
        with st.container(border=True):
            render_trade_header(alert.get('ticker'), alert.get('strategy_type'), rank=i)
            render_metric_row(alert)

            st.markdown(
                f"**Premium Context:** {alert.get('volatility_context')}"
            )
            render_stability_block(alert)
            render_decision_summary(alert)

            render_json_expander(alert)