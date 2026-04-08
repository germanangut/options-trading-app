"""Portfolio tab UI rendering module."""

import streamlit as st


def _render_count_rows(rows, key_name):
    if not rows:
        st.info("Limited context for this section in the current run.")
        return

    for row in rows:
        label = row.get(key_name, "n/a")
        count = row.get("count", 0)
        share_pct = row.get("share_pct")

        if share_pct is not None:
            st.write(f"- {label} — {count} ({share_pct}%)")
        else:
            st.write(f"- {label} — {count}")


def render_portfolio_tab(output):
    """Render a dedicated portfolio view using existing portfolio-aware summaries."""
    st.subheader("Portfolio")

    exposure = output.get("portfolio_exposure_summary") or {}
    sizing = output.get("position_sizing_summary") or {}
    overlap = output.get("exposure_overlap_summary") or {}
    decision = output.get("portfolio_decision_summary") or {}

    metadata = exposure.get("metadata") or {}
    qualified_summary = exposure.get("qualified") or {}
    qualified_count = metadata.get("qualified_trade_count", 0)

    if qualified_count == 0:
        with st.container(border=True):
            st.info(
                "No qualified trades are available in this run, so portfolio-level signals are limited."
            )
        return

    top_ticker = (qualified_summary.get("top_ticker_concentration") or [None])[0] or {}
    top_direction = (qualified_summary.get("directional_exposure") or [None])[0] or {}
    sizing_core = sizing.get("summary") or {}

    with st.container(border=True):
        posture_label = decision.get("posture_label", "Portfolio View")
        st.markdown(f"### {posture_label}")

        for message in (decision.get("interpretation") or [])[:2]:
            st.write(message)

        key_signals = decision.get("key_portfolio_signals") or []
        if key_signals:
            st.markdown("**Key Signals**")
            for signal in key_signals[:3]:
                st.write(f"- {signal}")

        cautions = decision.get("cautions") or []
        if cautions:
            st.markdown("**Cautions**")
            for caution in cautions[:3]:
                st.write(f"- {caution}")

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Qualified Trades", qualified_count)
        col2.metric("Unique Tickers", metadata.get("unique_qualified_ticker_count", 0))
        col3.metric(
            "Top Ticker",
            top_ticker.get("ticker", "n/a"),
            f"{top_ticker.get('share_pct', 0)}%" if top_ticker else None,
        )
        col4.metric(
            "Directional Tilt",
            str(top_direction.get("directional_bias", "n/a")).replace("_", " ").title(),
            f"{top_direction.get('share_pct', 0)}%" if top_direction else None,
        )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### Exposure by Ticker")
            _render_count_rows(qualified_summary.get("counts_by_ticker") or [], "ticker")

            st.markdown("### Exposure by Strategy")
            _render_count_rows(qualified_summary.get("counts_by_strategy") or [], "strategy")

    with col2:
        with st.container(border=True):
            st.markdown("### Overlap & Direction")
            st.markdown("**By Direction**")
            _render_count_rows(overlap.get("counts_by_direction") or [], "direction")

            st.markdown("**By Strategy Family**")
            _render_count_rows(
                overlap.get("counts_by_strategy_family") or [],
                "strategy_family",
            )

            repeated = overlap.get("repeated_ticker_direction_combinations") or []
            if repeated:
                st.markdown("**Repeated Overlap**")
                for row in repeated[:3]:
                    st.write(
                        f"- {row.get('ticker_direction', 'n/a')} — {row.get('count', 0)}"
                    )

    with st.container(border=True):
        st.markdown("### Sizing Context")
        inputs = sizing.get("inputs") or {}

        average_risk = sizing_core.get("average_estimated_max_risk_dollars")
        avg_risk_display = f"${average_risk}" if average_risk is not None else "Limited"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Risk Budget", f"${inputs.get('max_risk_dollars', 'n/a')}")
        col2.metric("Avg Est. Risk", avg_risk_display)
        col3.metric("Fits Budget", sizing_core.get("fits_budget_count", 0))
        col4.metric("Oversized", sizing_core.get("oversized_count", 0))

        for warning in (sizing.get("warnings") or [])[:2]:
            st.write(f"- {warning}")
