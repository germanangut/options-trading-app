"""Qualified trades UI rendering module."""

import streamlit as st
from ui.components import (
    render_metric_row,
    render_trade_header,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
)


def render_qualified_trades(qualified):
    """Render the qualified trades list with summary and detailed cards.
    
    Args:
        qualified: List of qualified trade dictionaries from engine
    """
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
            render_trade_header(spread.get('ticker'), spread.get('strategy_type'), rank=i)

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

            render_stability_block(spread)

            if spread.get("status_reason"):
                st.markdown(f"**Status:** {spread.get('status_reason')}")

            render_decision_summary(spread)

            render_json_expander(spread)