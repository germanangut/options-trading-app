"""Reusable UI rendering components for Streamlit app."""

import streamlit as st


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


def render_trade_header(ticker, strategy_type, rank=None):
    """Display trade header with ticker and strategy.
    
    Args:
        ticker: Ticker symbol
        strategy_type: Trading strategy type
        rank: Optional rank number (e.g., 1, 2, 3)
    """
    if rank is not None:
        st.markdown(f"### {rank}. {ticker} | {strategy_type}")
    else:
        st.markdown(f"### {ticker} | {strategy_type}")


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
    st.markdown(
        f"**Decision:** {spread.get('decision_summary', 'No summary available.')}"
    )


def render_json_expander(data, label="More details"):
    """Display data as JSON in an expander.
    
    Args:
        data: Dictionary to display as JSON
        label: Label for the expander
    """
    with st.expander(label):
        st.json(data)
