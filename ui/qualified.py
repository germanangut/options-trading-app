"""Qualified trades UI rendering module."""

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


def render_qualified_trades(qualified, provider_errors=None, missing_tickers=None):
    """Render the qualified trades list with summary and detailed cards.
    
    Args:
        qualified: List of qualified trade dictionaries from engine
        provider_errors: Optional list of provider issues from the current run
        missing_tickers: Optional list of missing tickers from the current run
    """
    st.subheader("Qualified Trades")

    provider_errors = provider_errors or []
    missing_tickers = missing_tickers or []
    missing_count = len(missing_tickers)

    if qualified:
        if provider_errors:
            st.warning(
                "Qualified trades are shown below, but provider issues may have limited overall coverage."
            )
        elif missing_count > 0:
            st.info(
                f"Qualified trades are shown below, but {missing_count} ticker(s) were unavailable during the scan."
            )

    if not qualified:
        if provider_errors:
            st.warning(
                "No qualified trades were returned because provider issues affected the run. Review the Overview tab before acting on the absence of candidates."
            )
        elif missing_count > 0:
            st.warning(
                f"No qualified trades were returned and {missing_count} ticker(s) were unavailable, so coverage was partial."
            )
        else:
            st.info(
                "No trades qualified under the current filters. This can be a healthy outcome when market conditions are weak or premiums are not attractive."
            )
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

        strategy_counts = {}
        for spread in qualified:
            strategy_name = get_strategy_display_name(spread)
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

        if strategy_counts:
            st.markdown("#### By Strategy")
            strategy_cols = st.columns(len(strategy_counts))
            for col, (strategy_name, count) in zip(strategy_cols, strategy_counts.items()):
                col.metric(strategy_name, count)

    # Trade cards (respecting engine sort order)
    for i, spread in enumerate(qualified, start=1):
        with st.container(border=True):
            render_trade_header(
                spread.get('ticker'),
                spread.get('strategy_type'),
                rank=i,
                spread=spread,
            )

            render_strategy_context_row(spread)
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
                strategy_name = get_strategy_display_name(spread)
                st.markdown(f"**Why {strategy_name} qualified:** {spread.get('status_reason')}")

            render_decision_summary(spread)
            render_json_expander(spread)