"""Portfolio tab UI rendering module."""

import streamlit as st

from ui.components import (
    get_strategy_display_name,
    render_bordered_panel,
    render_empty_state,
    render_kpi_metric_card,
    render_metric_strip,
    render_semantic_chip,
)


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


def _estimate_trade_risk_dollars(spread):
    if not isinstance(spread, dict):
        return None

    max_risk = spread.get("max_risk")
    try:
        if max_risk not in (None, ""):
            return round(float(max_risk) * 100, 2)
    except (TypeError, ValueError):
        pass

    try:
        spread_width = float(spread.get("spread_width"))
        net_credit = float(spread.get("net_credit"))
        return round(max(spread_width - net_credit, 0) * 100, 2)
    except (TypeError, ValueError):
        return None


def _format_status(spread):
    stability = str(spread.get("stability_level") or "").strip().lower()
    if stability == "stable":
        return ("Stable", "bullish")
    if stability == "emerging":
        return ("Emerging", "warning")
    if stability == "new":
        return ("New", "info")
    return ("Watch", "info")


def _direction_distribution_rows(rows):
    mapped = []
    for row in rows or []:
        label = str(row.get("directional_bias", "n/a")).replace("_", " ").title()
        mapped.append(
            {
                "label": label,
                "value": f"{row.get('count', 0)} ({row.get('share_pct', 0)}%)",
            }
        )
    return mapped


def _build_position_rows(qualified_spreads):
    rows = []
    for spread in qualified_spreads or []:
        rows.append(
            {
                "Ticker": spread.get("ticker", "n/a"),
                "Strategy": get_strategy_display_name(spread, default="Trade"),
                "Strikes": f"{spread.get('short_strike', '—')} / {spread.get('long_strike', '—')}",
                "Expiration": spread.get("expiration_date", "—"),
                "Premium": spread.get("net_credit", "—"),
                "Max Risk": _estimate_trade_risk_dollars(spread),
                "Status": _format_status(spread)[0],
            }
        )
    return rows


def render_portfolio_tab(output):
    """Render a dedicated portfolio view using existing portfolio-aware summaries."""
    qualified_spreads = output.get("qualified", []) or []
    exposure = output.get("portfolio_exposure_summary") or {}
    sizing = output.get("position_sizing_summary") or {}
    overlap = output.get("exposure_overlap_summary") or {}
    decision = output.get("portfolio_decision_summary") or {}

    metadata = exposure.get("metadata") or {}
    qualified_summary = exposure.get("qualified") or {}
    qualified_count = metadata.get("qualified_trade_count", 0)

    if qualified_count == 0:
        render_empty_state(
            "No open positions",
            "No open positions — your portfolio is currently flat",
        )
        return

    top_ticker = (qualified_summary.get("top_ticker_concentration") or [None])[0] or {}
    top_direction = (qualified_summary.get("directional_exposure") or [None])[0] or {}
    sizing_core = sizing.get("summary") or {}
    counts_by_direction = qualified_summary.get("directional_exposure") or []
    bullish_share = next((row.get("share_pct", 0) for row in counts_by_direction if row.get("directional_bias") == "bullish"), 0)
    bearish_share = next((row.get("share_pct", 0) for row in counts_by_direction if row.get("directional_bias") == "bearish"), 0)
    concentration_indicator = (
        f"{top_ticker.get('share_pct', 0)}% in {top_ticker.get('ticker', 'n/a')}"
        if top_ticker else "n/a"
    )

    estimated_risks = [value for value in (_estimate_trade_risk_dollars(spread) for spread in qualified_spreads) if value is not None]
    total_capital_at_risk = round(sum(estimated_risks), 2) if estimated_risks else None

    snapshot_panel = render_bordered_panel(
        "Portfolio Snapshot",
        "Current exposure and risk overview from this run.",
    )
    with snapshot_panel:
        cols = st.columns(4, gap="small")
        render_kpi_metric_card(cols[0], "Total Positions", qualified_count, accent="info")
        render_kpi_metric_card(cols[1], "Capital At Risk", f"${total_capital_at_risk:,.0f}" if total_capital_at_risk is not None else "Limited", accent="bearish")
        render_kpi_metric_card(cols[2], "Directional Exposure", f"Bull {bullish_share}% / Bear {bearish_share}%", accent="warning", emphasis="compact")
        render_kpi_metric_card(cols[3], "Concentration", concentration_indicator, accent="bullish", emphasis="compact")

    with render_bordered_panel("Portfolio Readout", "Portfolio interpretation using current run summaries."):
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

    col1, col2 = st.columns(2, gap="small")

    with col1:
        exposure_panel = render_bordered_panel(
            "Exposure Breakdown",
            "Directional, ticker, and strategy distribution.",
        )
        with exposure_panel:
            st.markdown("**Bullish vs Bearish**")
            direction_rows = _direction_distribution_rows(qualified_summary.get("directional_exposure") or [])
            if direction_rows:
                render_metric_strip(
                    [
                        {"label": row["label"], "value": row["value"], "accent": "#64748b"}
                        for row in direction_rows[:3]
                    ],
                    columns=min(3, len(direction_rows)),
                )
            else:
                st.caption("No directional breakdown available.")

            st.markdown("**Exposure by Ticker**")
            _render_count_rows(qualified_summary.get("counts_by_ticker") or [], "ticker")

            st.markdown("**Strategy Distribution**")
            _render_count_rows(qualified_summary.get("counts_by_strategy") or [], "strategy")

    with col2:
        risk_panel = render_bordered_panel(
            "Risk Signals",
            "Concentration, overlap, and sizing warnings worth reviewing.",
        )
        with risk_panel:
            high_risk_count = sizing_core.get("oversized_count", 0)
            if high_risk_count:
                render_semantic_chip(f"{high_risk_count} High-Risk Position(s)", tone="bearish")
            else:
                render_semantic_chip("No oversized positions", tone="bullish")

            notes = []
            if top_ticker and top_ticker.get("share_pct", 0) >= 30:
                notes.append(
                    f"Concentration risk: {top_ticker.get('ticker', 'n/a')} represents {top_ticker.get('share_pct', 0)}% of current exposure."
                )

            repeated = overlap.get("repeated_ticker_direction_combinations") or []
            if repeated:
                for row in repeated[:3]:
                    notes.append(
                        f"Overlapping exposure: {row.get('ticker_direction', 'n/a')} appears {row.get('count', 0)} time(s)."
                    )

            for warning in (sizing.get("warnings") or [])[:2]:
                notes.append(warning)

            if notes:
                for note in notes[:4]:
                    st.write(f"- {note}")
            else:
                st.caption("No major risk signals are standing out in this run.")

    positions_panel = render_bordered_panel(
        "Positions",
        "Current candidate list formatted as a clean exposure table.",
    )
    with positions_panel:
        position_rows = _build_position_rows(qualified_spreads)
        table_rows = []
        for row in position_rows:
            table_rows.append(
                {
                    "Ticker": row["Ticker"],
                    "Strategy": row["Strategy"],
                    "Strikes": row["Strikes"],
                    "Expiration": row["Expiration"],
                    "Premium": row["Premium"],
                    "Max Risk": row["Max Risk"],
                    "Status": row["Status"],
                }
            )
        st.table(table_rows)

    with render_bordered_panel("Sizing Context", "Budget fit and estimated risk across current candidates."):
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
