"""Reusable UI rendering components for Streamlit app."""

import streamlit as st
from strategies import get_strategy, get_strategy_label


def _humanize_value(value, default="n/a"):
    if value in (None, ""):
        return default

    return str(value).replace("_", " ")


def get_strategy_display_name(spread_or_key, default="Trade"):
    """Resolve a consistent strategy display label using registry metadata when available."""
    if isinstance(spread_or_key, dict):
        strategy_key = (
            spread_or_key.get("strategy_key")
            or spread_or_key.get("strategy_label")
            or spread_or_key.get("strategy_type")
        )
        fallback = (
            spread_or_key.get("strategy_label")
            or spread_or_key.get("strategy_type")
            or default
        )
    else:
        strategy_key = spread_or_key
        fallback = spread_or_key or default

    label = get_strategy_label(strategy_key, default=fallback) or fallback
    return _humanize_value(label, default=default).title()


def get_strategy_context(spread):
    """Build a concise strategy context line from existing spread metadata."""
    strategy = get_strategy(
        spread.get("strategy_key")
        or spread.get("strategy_label")
        or spread.get("strategy_type")
    ) or {}

    bias = _humanize_value(
        strategy.get("directional_bias") or spread.get("directional_bias")
    ).title()
    family = _humanize_value(
        strategy.get("family") or spread.get("strategy_family")
    ).title()

    if bias == "N/A" and family == "N/A":
        return None
    if bias == "N/A":
        return family
    if family == "N/A":
        return bias
    return f"{bias} {family}"


def render_metric_row(spread):
    """Display metrics in a 4-column layout.
    
    Args:
        spread: Dictionary with keys "adjusted_score", "POP", "ROR", "DTE"
    """
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Adjusted Score", spread.get("adjusted_score"))
    col2.metric("POP", spread.get("POP"))
    col3.metric("ROR", spread.get("ROR"))
    col4.metric("DTE", spread.get("DTE"))


def render_trade_header(ticker, strategy_type, rank=None, spread=None):
    """Display trade header with ticker and strategy.
    
    Args:
        ticker: Ticker symbol
        strategy_type: Trading strategy type
        rank: Optional rank number (e.g., 1, 2, 3)
        spread: Optional spread dictionary for richer strategy context
    """
    strategy_name = get_strategy_display_name(spread or strategy_type, default=strategy_type or "Trade")

    if rank is not None:
        st.markdown(f"### {rank}. {ticker} | {strategy_name}")
    else:
        st.markdown(f"### {ticker} | {strategy_name}")

    if spread:
        strategy_context = get_strategy_context(spread)
        if strategy_context:
            st.caption(f"Strategy context: {strategy_context}")


def render_strategy_context_row(spread):
    """Display a compact row with strategy identity details."""
    strategy_name = get_strategy_display_name(spread)
    strategy = get_strategy(
        spread.get("strategy_key")
        or spread.get("strategy_label")
        or spread.get("strategy_type")
    ) or {}

    bias = _humanize_value(
        strategy.get("directional_bias") or spread.get("directional_bias")
    ).title()
    family = _humanize_value(
        strategy.get("family") or spread.get("strategy_family")
    ).title()

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"**Strategy:** {strategy_name}")
    col2.markdown(f"**Bias:** {bias}")
    col3.markdown(f"**Family:** {family}")


def render_stability_block(spread):
    """Display stability level and count.
    
    Args:
        spread: Dictionary with keys "stability_level", "stability_count"
    """
    st.markdown(
        f"**Stability:** {spread.get('stability_level', 'n/a')} "
        f"({spread.get('stability_count', 0)})"
    )


def render_decision_summary(spread):
    """Display decision summary.
    
    Args:
        spread: Dictionary with key "decision_summary"
    """
    strategy_name = get_strategy_display_name(spread)
    st.markdown(
        f"**Decision:** {strategy_name} view — {spread.get('decision_summary', 'No summary available.')}"
    )


def render_json_expander(data, label="More details"):
    """Display data as JSON in an expander.
    
    Args:
        data: Dictionary to display as JSON
        label: Label for the expander
    """
    with st.expander(label):
        st.json(data)
