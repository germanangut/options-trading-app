"""Qualified trades UI rendering module."""

from html import escape

import streamlit as st
from decisions import POP_THRESHOLD, ROR_THRESHOLD
from ui.components import (
    direction_color,
    format_currency,
    format_value,
    get_strategy_display_name,
    render_empty_state,
    render_section_header,
    render_subsection_card,
    render_summary_bar,
    render_warning_banner,
)


TRADE_ROW_COLUMN_RATIOS = [0.58, 0.12, 3.35, 0.95, 0.95, 1.05, 0.9]
EXPANDED_TRADE_STATE_KEY = "qualified_expanded_trade_key"


def get_trade_row_key(spread):
    if not isinstance(spread, dict):
        return None

    return "|".join(
        str(
            spread.get(field)
            or ""
        ).strip()
        for field in ("ticker", "strategy_type", "expiration_date", "short_strike", "long_strike")
    )


def _normalize_portfolio_value(value):
    return str(value or "").strip().replace("_", " ").lower()


def _display_text(value, default="—"):
    text = str(value or "").strip()
    if not text:
        return default
    return text.replace("_", " ")


def _score_value(spread):
    if not isinstance(spread, dict):
        return None

    score = spread.get("adjusted_score")
    if score in (None, ""):
        score = spread.get("score")
    return score


def _breakeven_value(spread):
    if not isinstance(spread, dict):
        return None

    for key in (
        "breakeven",
        "break_even",
        "breakeven_price",
        "break_even_price",
        "breakeven_short",
    ):
        value = spread.get(key)
        if value not in (None, ""):
            return value

    return None


def _threshold_delta_text(value, threshold):
    try:
        margin = float(value) - float(threshold)
    except (TypeError, ValueError):
        return None

    return f"{margin:+.1f} vs min"


def _find_context_row(rows, key_name, *candidates):
    normalized_candidates = {
        _normalize_portfolio_value(candidate)
        for candidate in candidates
        if candidate not in (None, "")
    }

    if not normalized_candidates:
        return None

    for row in rows or []:
        if _normalize_portfolio_value(row.get(key_name)) in normalized_candidates:
            return row

    return None


def _find_sizing_row(spread, position_sizing_summary=None):
    strategy_name = get_strategy_display_name(spread)

    return _find_context_row(
        (position_sizing_summary or {}).get("trade_sizing", []),
        "strategy",
        strategy_name,
        spread.get("strategy_type"),
        spread.get("strategy_label"),
    )


def _build_portfolio_notes(
    spread,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
):
    notes = []
    ticker = spread.get("ticker")
    direction = spread.get("directional_bias")

    ticker_row = _find_context_row(
        ((portfolio_exposure_summary or {}).get("qualified") or {}).get("counts_by_ticker", []),
        "ticker",
        ticker,
    )
    if ticker_row and ticker_row.get("share_pct", 0) >= 30:
        notes.append(
            f"{ticker} represents **{ticker_row.get('share_pct')}%** of the current qualified set."
        )

    sizing_row = _find_sizing_row(spread, position_sizing_summary=position_sizing_summary)
    if sizing_row:
        estimated_risk = sizing_row.get("estimated_max_risk_dollars")
        fits_budget = sizing_row.get("fits_risk_budget")
        contracts = sizing_row.get("approx_contracts_within_budget")

        if estimated_risk is not None:
            if fits_budget is True:
                contract_note = (
                    f"fits the sample risk budget (up to {contracts} contract(s))"
                    if contracts is not None
                    else "fits the sample risk budget"
                )
                notes.append(
                    f"Est. max risk **${estimated_risk}** and {contract_note}."
                )
            elif fits_budget is False:
                notes.append(
                    f"Est. max risk **${estimated_risk}** and it sits above the sample per-trade risk budget."
                )
            else:
                notes.append(f"Est. max risk **${estimated_risk}**.")

    overlap_row = _find_context_row(
        (exposure_overlap_summary or {}).get("repeated_ticker_direction_combinations", []),
        "ticker_direction",
        f"{ticker} | {direction}",
    )
    if overlap_row:
        direction_label = _display_text(direction, default="unknown")
        notes.append(
            f"Overlap note: **{ticker} | {direction_label}** appears **{overlap_row.get('count', 0)}** time(s) in the current qualified set."
        )

    return notes[:3]


def render_portfolio_trade_context(
    spread,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
):
    """Render compact, secondary portfolio-aware notes for an individual trade."""
    notes = _build_portfolio_notes(
        spread,
        portfolio_exposure_summary=portfolio_exposure_summary,
        position_sizing_summary=position_sizing_summary,
        exposure_overlap_summary=exposure_overlap_summary,
    )

    if not notes:
        return

    render_subsection_card(
        "Portfolio Context",
        notes,
        subtitle="Sizing and overlap notes from the current run.",
        accent="#64748b",
    )


def _summary_items(qualified, portfolio_exposure_summary=None):
    total_trades = len(qualified)
    stable_count = sum(1 for spread in qualified if spread.get("stability_level") == "stable")
    scores = [score for score in (_score_value(spread) for spread in qualified) if score not in (None, "")]
    avg_score = round(sum(scores) / len(scores), 1) if scores else None
    top_ticker = qualified[0].get("ticker") if qualified else "N/A"

    concentration_delta = None
    ticker_row = _find_context_row(
        ((portfolio_exposure_summary or {}).get("qualified") or {}).get("counts_by_ticker", []),
        "ticker",
        top_ticker,
    )
    if ticker_row and ticker_row.get("share_pct") not in (None, ""):
        concentration_delta = f"{ticker_row.get('share_pct')}% of set"

    return [
        {"label": "Qualified", "value": total_trades, "accent": "#14b8a6"},
        {"label": "Stable", "value": stable_count, "accent": "#64748b"},
        {"label": "Avg Score", "value": avg_score, "accent": "#f59e0b"},
        {
            "label": "Top Ticker",
            "value": top_ticker or "N/A",
            "direction": qualified[0] if qualified else None,
            "delta": concentration_delta,
        },
    ]


def _consolidated_board_message(provider_errors, missing_tickers, portfolio_exposure_summary=None):
    parts = []
    level = "info"

    if provider_errors:
        parts.append("Provider issues may have limited overall scan coverage.")
        level = "warning"

    missing_count = len(missing_tickers or [])
    if missing_count > 0:
        parts.append(f"{missing_count} ticker(s) were unavailable during the current run.")
        if level != "warning":
            level = "info"

    qualified_counts = ((portfolio_exposure_summary or {}).get("qualified") or {}).get("counts_by_ticker", [])
    if qualified_counts:
        top_row = max(qualified_counts, key=lambda row: row.get("share_pct", 0), default=None)
        if top_row and top_row.get("share_pct", 0) >= 30:
            parts.append(
                f"Concentration note: {top_row.get('ticker', 'Top ticker')} represents {top_row.get('share_pct')}% of the current qualified set."
            )

    return (" ".join(parts).strip(), level) if parts else (None, level)


def _score_bar_width(score):
    try:
        numeric = abs(float(score))
    except (TypeError, ValueError):
        return 0

    if numeric <= 1:
        width = numeric * 100
    elif numeric <= 10:
        width = numeric * 10
    else:
        width = numeric

    return max(8, min(100, width))


def _render_inline_metric(
    column,
    label,
    value,
    accent,
    emphasis="standard",
    subtext=None,
    bar_width=None,
    value_color=None,
    subtext_color="#14b8a6",
):
    font_sizes = {
        "high": "1.45rem",
        "medium": "1.1rem",
        "standard": "0.86rem",
        "compact": "0.78rem",
    }
    font_weights = {
        "high": "800",
        "medium": "740",
        "standard": "680",
        "compact": "640",
    }
    font_size = font_sizes.get(emphasis, font_sizes["standard"])
    font_weight = font_weights.get(emphasis, font_weights["standard"])
    resolved_value_color = value_color or "var(--text-color, inherit)"

    subtext_html = ""
    if subtext:
        subtext_html = (
            f"<div style='margin-top:0.05rem;font-size:0.63rem;color:{subtext_color};font-weight:700;line-height:1.05;'>"
            f"{escape(str(subtext))}"
            "</div>"
        )

    bar_html = ""
    if bar_width:
        bar_html = f"""
        <div style="margin-top:0.14rem;height:0.36rem;border-radius:999px;background:rgba(127, 127, 127, 0.24);overflow:hidden;max-width:3.9rem;">
            <div style="width:{bar_width:.0f}%;height:100%;background:{accent};border-radius:999px;opacity:0.98;"></div>
        </div>
        """

    column.markdown(
        f"""
        <div style="padding-top:0.01rem;min-height:3.45rem;display:flex;flex-direction:column;justify-content:flex-start;">
            <div style="font-size:0.62rem;text-transform:uppercase;letter-spacing:0.04em;font-weight:700;opacity:0.68;line-height:1;">
                {escape(str(label))}
            </div>
            <div style="font-size:{font_size};font-weight:{font_weight};line-height:1.0;margin-top:0.05rem;color:{resolved_value_color};">
                {escape(str(value))}
            </div>
            {subtext_html}
            {bar_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_trade_board_header():
    header_cols = st.columns(TRADE_ROW_COLUMN_RATIOS, gap="small")
    header_labels = ["Rank", "", "Trade", "POP", "ROR", "Score", "Action"]

    for column, label in zip(header_cols, header_labels):
        if not label:
            column.markdown("&nbsp;", unsafe_allow_html=True)
            continue

        column.markdown(
            f"""
            <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.04em;font-weight:700;opacity:0.66;padding-bottom:0.18rem;">
                {escape(label)}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_quick_review_metrics(spread, breakeven):
    items = [
        ("Short Strike", format_value(spread.get("short_strike"))),
        ("Long Strike", format_value(spread.get("long_strike"))),
        ("Net Credit", format_currency(spread.get("net_credit"), decimals=3)),
        ("Max Risk", format_currency(spread.get("max_risk"))),
        ("Breakeven", format_currency(breakeven) if breakeven not in (None, "") else "—"),
    ]

    columns = st.columns(len(items), gap="small")
    for column, (label, value) in zip(columns, items):
        column.markdown(
            f"""
            <div style="padding:0.02rem 0 0.06rem 0;">
                <div style="font-size:0.63rem;text-transform:uppercase;letter-spacing:0.04em;font-weight:750;opacity:0.7;">
                    {escape(str(label))}
                </div>
                <div style="margin-top:0.08rem;font-size:0.9rem;font-weight:700;line-height:1.04;color:var(--text-color, inherit);">
                    {escape(str(value))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_expanded_trade_review(spread):
    breakeven = _breakeven_value(spread)
    quick_summary = (
        spread.get("decision_summary")
        or spread.get("status_reason")
        or spread.get("explanation")
    )
    accent = direction_color(spread)
    left_offset = TRADE_ROW_COLUMN_RATIOS[0] + TRADE_ROW_COLUMN_RATIOS[1]
    content_width = sum(TRADE_ROW_COLUMN_RATIOS[2:])

    _, content_col = st.columns([left_offset, content_width], gap="small")
    with content_col:
        st.markdown(
            f"""
            <div style="margin:0.0rem 0 0.08rem 0;padding:0.08rem 0 0 0;border-top:1px solid rgba(127, 127, 127, 0.22);">
                <div style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.04em;font-weight:700;color:{accent};opacity:0.96;line-height:1;">Quick review</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _render_quick_review_metrics(spread, breakeven)

        if quick_summary:
            st.markdown(
                f"<div style='margin-top:0.1rem;font-size:0.79rem;line-height:1.32;opacity:0.88;'>Decision summary: {escape(str(quick_summary))}</div>",
                unsafe_allow_html=True,
            )

        if spread.get("price_context_warning"):
            st.markdown("<div style='height:0.05rem;'></div>", unsafe_allow_html=True)
            render_warning_banner(
                spread.get("price_context_reason") or "Price context warning is active for this setup.",
                level="warning",
            )


def _render_trade_row(
    spread,
    rank,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
    on_detail_select=None,
    selected_detail_key=None,
):
    accent = direction_color(spread)
    ticker = escape(str(spread.get("ticker") or "N/A"))
    strategy_name = escape(get_strategy_display_name(spread))
    expiration = escape(_display_text(spread.get("expiration_date")))
    dte = escape(format_value(spread.get("DTE"), decimals=0))
    premium_context = escape(_display_text(spread.get("volatility_context")))
    strikes = escape(
        f"{format_value(spread.get('short_strike'))} / {format_value(spread.get('long_strike'))}"
    )
    score = _score_value(spread)
    score_display = format_value(score, decimals=2)
    score_label = _display_text(spread.get("label") or spread.get("stability_level"), default="")

    quality_label = spread.get("label") or ("Top Ranked" if rank == 1 else None)
    quality_html = ""
    if quality_label:
        quality_html = (
            "<span style=\"display:inline-block;padding:0.08rem 0.42rem;border-radius:999px;"
            "background:rgba(127, 127, 127, 0.10);border:1px solid rgba(127, 127, 127, 0.16);"
            "color:inherit;font-size:0.68rem;font-weight:700;\">"
            f"{escape(_display_text(quality_label).title())}</span>"
        )

    row_key = get_trade_row_key(spread)
    button_state_key = f"qualified_trade_actions_{rank}_{spread.get('ticker', 'na')}_{spread.get('expiration_date', 'na')}"
    button_key = f"{button_state_key}_expand"
    detail_button_key = f"{button_state_key}_details"
    expanded = bool(row_key and st.session_state.get(EXPANDED_TRADE_STATE_KEY) == row_key)

    with st.container(border=True):
        rank_col, bar_col, identity_col, pop_col, ror_col, score_col, action_col = st.columns(
            TRADE_ROW_COLUMN_RATIOS,
            gap="small",
        )

        rank_col.markdown(
            f"""
            <div style="padding-top:0.04rem;text-align:center;">
                <div style="font-size:1.24rem;font-weight:800;line-height:1;color:var(--text-color, inherit);">#{rank}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        bar_height = "3.9rem"
        bar_col.markdown(
            f"""
            <div style="display:flex;justify-content:center;padding-top:0.02rem;">
                <div style="width:0.28rem;height:{bar_height};border-radius:999px;background:{accent};"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        identity_col.markdown(
            f"""
            <div style="padding-top:0.0rem;">
                <div style="display:flex;align-items:center;gap:0.24rem;flex-wrap:wrap;line-height:1;">
                    <span style="font-size:1.06rem;font-weight:760;color:var(--text-color, inherit);">{ticker}</span>
                    <span style="font-size:0.78rem;opacity:0.68;">{strategy_name}</span>
                    {quality_html}
                </div>
                <div style="margin-top:0.06rem;font-size:0.74rem;opacity:0.64;line-height:1.05;">Exp {expiration} • {dte} DTE</div>
                <div style="margin-top:0.04rem;font-size:0.74rem;opacity:0.64;line-height:1.05;">Strikes {strikes}</div>
                <div style="margin-top:0.04rem;font-size:0.73rem;opacity:0.66;line-height:1.05;">Premium context: {premium_context}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        _render_inline_metric(
            pop_col,
            "POP",
            format_value(spread.get("POP"), decimals=1),
            accent="#14b8a6",
            emphasis="high",
            subtext=_threshold_delta_text(spread.get("POP"), POP_THRESHOLD),
            value_color="#14b8a6",
            subtext_color="#14b8a6",
        )
        _render_inline_metric(
            ror_col,
            "ROR",
            format_value(spread.get("ROR"), decimals=1),
            accent="#f59e0b",
            emphasis="medium",
            subtext=_threshold_delta_text(spread.get("ROR"), ROR_THRESHOLD),
            value_color="#b45309",
            subtext_color="#14b8a6",
        )
        _render_inline_metric(
            score_col,
            "Score",
            score_display,
            accent=accent,
            emphasis="standard",
            subtext=score_label,
            bar_width=_score_bar_width(score),
            subtext_color="#64748b",
        )

        with action_col:
            st.markdown("<div style='height:0.08rem;'></div>", unsafe_allow_html=True)
            if st.button(
                "Hide" if expanded else "Expand",
                key=button_key,
                use_container_width=True,
                type="primary",
            ):
                st.session_state[EXPANDED_TRADE_STATE_KEY] = None if expanded else row_key
                st.rerun()

            st.markdown("<div style='height:0.07rem;'></div>", unsafe_allow_html=True)
            if st.button(
                "Details",
                key=detail_button_key,
                use_container_width=True,
                type="secondary",
            ) and callable(on_detail_select):
                st.session_state[EXPANDED_TRADE_STATE_KEY] = None
                on_detail_select(spread)
                st.rerun()

            if selected_detail_key and row_key == selected_detail_key:
                st.caption("Selected")

        if expanded:
            _render_expanded_trade_review(spread)

    st.markdown("<div style='height:0.22rem;'></div>", unsafe_allow_html=True)


def render_qualified_trades(
    qualified,
    provider_errors=None,
    missing_tickers=None,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
    on_detail_select=None,
    selected_detail_key=None,
):
    """Render the ranked qualified trades board using the engine-provided order."""
    provider_errors = provider_errors or []
    missing_tickers = missing_tickers or []

    render_section_header(
        "Qualified Trades",
        "Primary ranked decision board — current engine order is preserved. Expand a row only when you need second-layer detail.",
    )

    if not qualified:
        if provider_errors:
            render_warning_banner(
                "No qualified trades were returned because provider issues affected the run. Review the Overview tab before acting on the absence of candidates.",
                level="warning",
            )
        elif missing_tickers:
            render_warning_banner(
                f"No qualified trades were returned and {len(missing_tickers)} ticker(s) were unavailable, so coverage was partial.",
                level="warning",
            )
        else:
            render_warning_banner(
                "No trades qualified under the current filters. This can be a healthy outcome when market conditions are weak or premiums are not attractive.",
                level="info",
            )

        render_empty_state(
            "No qualified trades",
            "Try adjusting profile, DTE range, minimum score, or consistency threshold.",
        )
        return

    render_summary_bar(_summary_items(qualified, portfolio_exposure_summary=portfolio_exposure_summary))

    banner_message, banner_level = _consolidated_board_message(
        provider_errors,
        missing_tickers,
        portfolio_exposure_summary=portfolio_exposure_summary,
    )
    if banner_message:
        render_warning_banner(banner_message, level=banner_level)

    _render_trade_board_header()

    for rank, spread in enumerate(qualified, start=1):
        _render_trade_row(
            spread,
            rank,
            portfolio_exposure_summary=portfolio_exposure_summary,
            position_sizing_summary=position_sizing_summary,
            exposure_overlap_summary=exposure_overlap_summary,
            on_detail_select=on_detail_select,
            selected_detail_key=selected_detail_key,
        )