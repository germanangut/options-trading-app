"""Reusable UI rendering components for Streamlit app."""

from html import escape

import streamlit as st
from strategies import get_strategy, get_strategy_label


_DIRECTION_TOKENS = {
    "bullish": {
        "accent": "#14b8a6",
        "soft": "rgba(20, 184, 166, 0.12)",
        "label": "Bullish",
    },
    "bearish": {
        "accent": "#f97316",
        "soft": "rgba(249, 115, 22, 0.12)",
        "label": "Bearish",
    },
    "neutral": {
        "accent": "#64748b",
        "soft": "rgba(100, 116, 139, 0.10)",
        "label": "Neutral",
    },
}


UI_TOKENS = {
    "color": {
        "surface": "rgba(255, 255, 255, 0.02)",
        "surface_alt": "var(--secondary-background-color, rgba(127, 127, 127, 0.08))",
        "border": "rgba(127, 127, 127, 0.20)",
        "muted": "rgba(100, 116, 139, 0.95)",
        "text": "var(--text-color, inherit)",
        "primary_button": "#0f766e",
        "primary_button_hover": "#115e59",
        "primary_button_soft": "rgba(15, 118, 110, 0.14)",
        "secondary_button_border": "rgba(100, 116, 139, 0.34)",
        "secondary_button_hover": "rgba(15, 23, 42, 0.05)",
        "bullish": "#14b8a6",
        "bearish": "#f97316",
        "warning": "#f59e0b",
        "info": "#64748b",
    },
    "radius": {
        "sm": "0.45rem",
        "md": "0.65rem",
        "lg": "0.85rem",
        "pill": "999px",
    },
    "space": {
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "0.75rem",
        "lg": "1rem",
    },
    "border": {
        "standard": "1px solid rgba(127, 127, 127, 0.20)",
        "strong": "1px solid rgba(100, 116, 139, 0.35)",
    },
}


def inject_ui_system_styles():
    """Inject one shared style block to keep page spacing and UI primitives consistent."""
    st.markdown(
        f"""
        <style>
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border: 1px solid rgba(127, 127, 127, 0.20) !important;
            border-radius: 0.85rem !important;
            background: rgba(255, 255, 255, 0.02);
        }}
        div[data-testid="stMetric"] {{
            border: 1px solid rgba(127, 127, 127, 0.20);
            border-radius: 0.65rem;
            background: rgba(255, 255, 255, 0.02);
            padding: 0.45rem 0.5rem;
            min-height: 5.1rem;
        }}
        div[data-testid="stMetricLabel"] {{
            font-size: 0.72rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            font-weight: 700;
            opacity: 0.72;
        }}
        div[data-testid="stMetricValue"] {{
            font-size: 1.35rem;
            font-weight: 760;
        }}
        div[data-testid="stButton"] > button {{
            border-radius: 0.65rem;
            min-height: 2.35rem;
            padding: 0.46rem 0.82rem;
            border: 1px solid rgba(127, 127, 127, 0.24);
            box-shadow: none;
            transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease, transform 120ms ease;
        }}
        div[data-testid="stButton"] > button:hover {{
            transform: translateY(-1px);
        }}
        div[data-testid="stButton"] > button:focus {{
            box-shadow: 0 0 0 0.18rem rgba(20, 184, 166, 0.16) !important;
            outline: none !important;
        }}
        div[data-testid="stButton"] > button[kind="primary"] {{
            background: {UI_TOKENS['color']['primary_button']} !important;
            color: white !important;
            border: 1px solid {UI_TOKENS['color']['primary_button']} !important;
        }}
        div[data-testid="stButton"] > button[kind="primary"]:hover {{
            background: {UI_TOKENS['color']['primary_button_hover']} !important;
            border-color: {UI_TOKENS['color']['primary_button_hover']} !important;
            color: white !important;
        }}
        div[data-testid="stButton"] > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.02) !important;
            color: var(--text-color, inherit) !important;
            border: 1px solid {UI_TOKENS['color']['secondary_button_border']} !important;
        }}
        div[data-testid="stButton"] > button[kind="secondary"]:hover {{
            background: {UI_TOKENS['color']['secondary_button_hover']} !important;
            border-color: {UI_TOKENS['color']['primary_button']} !important;
            color: var(--text-color, inherit) !important;
        }}
        div[data-testid="stButton"] > button[kind="tertiary"] {{
            background: transparent !important;
            color: {UI_TOKENS['color']['info']} !important;
            border: 1px solid transparent !important;
        }}
        div[data-testid="stButton"] > button[kind="tertiary"]:hover {{
            background: rgba(100, 116, 139, 0.08) !important;
            color: {UI_TOKENS['color']['primary_button']} !important;
        }}
        div[data-testid="stSegmentedControl"] {{
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(127, 127, 127, 0.20);
            border-radius: 0.85rem;
            padding: 0.18rem;
        }}
        div[data-testid="stSegmentedControl"] button {{
            min-height: 2.2rem;
            border-radius: 0.62rem !important;
            border: 1px solid transparent !important;
            color: var(--text-color, inherit) !important;
            background: transparent !important;
            transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease;
        }}
        div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
            background: {UI_TOKENS['color']['primary_button_soft']} !important;
            border-color: rgba(15, 118, 110, 0.32) !important;
            color: {UI_TOKENS['color']['primary_button']} !important;
            font-weight: 700 !important;
        }}
        div[data-testid="stSegmentedControl"] button[aria-pressed="false"]:hover {{
            background: rgba(100, 116, 139, 0.08) !important;
            color: var(--text-color, inherit) !important;
        }}
        div[role="radiogroup"] {{
            gap: 0.35rem;
        }}
        div[role="radiogroup"] label[data-baseweb="radio"] {{
            border: 1px solid {UI_TOKENS['color']['secondary_button_border']};
            border-radius: 999px;
            padding: 0.24rem 0.7rem;
            background: rgba(255, 255, 255, 0.02);
            transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease;
        }}
        div[role="radiogroup"] label[data-baseweb="radio"]:hover {{
            background: rgba(100, 116, 139, 0.08);
            border-color: {UI_TOKENS['color']['primary_button']};
        }}
        div[role="radiogroup"] label[data-baseweb="radio"] input:checked + div {{
            color: {UI_TOKENS['color']['primary_button']} !important;
            font-weight: 700 !important;
        }}
        div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {{
            background: {UI_TOKENS['color']['primary_button_soft']};
            border-color: rgba(15, 118, 110, 0.34);
        }}
        div[data-baseweb="select"] > div {{
            border-radius: 0.7rem !important;
            border-color: rgba(100, 116, 139, 0.28) !important;
        }}
        div[data-baseweb="select"] > div:hover {{
            border-color: {UI_TOKENS['color']['primary_button']} !important;
        }}
        div[data-baseweb="tag"] {{
            border-radius: 999px !important;
            background: {UI_TOKENS['color']['primary_button_soft']} !important;
            border: 1px solid rgba(15, 118, 110, 0.28) !important;
            color: {UI_TOKENS['color']['primary_button']} !important;
            padding: 0.1rem 0.38rem !important;
        }}
        div[data-baseweb="tag"] span {{
            color: {UI_TOKENS['color']['primary_button']} !important;
        }}
        div[data-baseweb="tag"]:hover {{
            background: rgba(15, 118, 110, 0.18) !important;
        }}
        div[data-testid="stExpander"] {{
            border-radius: 0.65rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title, purpose, helper=None):
    """Render a consistent page-level header: title, purpose, optional helper line."""
    st.markdown(f"## {title}")
    st.caption(purpose)
    if helper:
        st.caption(helper)


def render_kpi_metric_card(container, label, value, accent="info", delta=None, emphasis="standard"):
    """Public wrapper for standardized KPI cards."""
    accent_value = UI_TOKENS["color"].get(accent, accent)
    _render_metric_card(container, label, value, accent=accent_value, delta=delta, emphasis=emphasis)


def render_semantic_chip(label, tone="info"):
    """Render a reusable semantic chip for status and direction labels."""
    accent = UI_TOKENS["color"].get(tone, UI_TOKENS["color"]["info"])
    st.markdown(
        f"""
        <span style="
            display:inline-flex;
            align-items:center;
            padding:0.17rem 0.5rem;
            border-radius:{UI_TOKENS['radius']['pill']};
            border:1px solid rgba(127, 127, 127, 0.20);
            background:rgba(255, 255, 255, 0.03);
            color:{UI_TOKENS['color']['text']};
            font-size:0.74rem;
            font-weight:700;
            gap:0.35rem;
        ">
            <span style="display:inline-block;width:0.48rem;height:0.48rem;border-radius:{UI_TOKENS['radius']['pill']};background:{accent};"></span>
            {escape(str(label))}
        </span>
        """,
        unsafe_allow_html=True,
    )


def render_bordered_panel(title=None, subtitle=None):
    """Render a bordered panel shell and return a container for content composition."""
    panel = st.container(border=True)
    with panel:
        if title:
            st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
    return panel


def render_action_button_row(button_specs):
    """Render a compact, consistent horizontal row of action buttons."""
    specs = [spec for spec in (button_specs or []) if isinstance(spec, dict) and spec.get("label")]
    if not specs:
        return {}

    columns = st.columns(len(specs), gap="small")
    results = {}
    for column, spec in zip(columns, specs):
        with column:
            results[spec.get("key", spec["label"])] = st.button(
                spec["label"],
                key=spec.get("key"),
                use_container_width=True,
                type=spec.get("type", "secondary"),
            )
    return results


def _humanize_value(value, default="n/a"):
    if value in (None, ""):
        return default

    return str(value).replace("_", " ")


def format_value(value, default="—", decimals=2):
    """Format a general display value with safe fallbacks."""
    if value in (None, ""):
        return default

    if isinstance(value, int):
        return f"{value}"

    if isinstance(value, float):
        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")

    return str(value)


def format_percentage(value, default="—", decimals=1, include_symbol=True, assume_fraction=False):
    """Format a percentage-like value safely for UI display."""
    if value in (None, ""):
        return default

    if isinstance(value, str) and "%" in value:
        return value

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)

    if assume_fraction or abs(numeric) <= 1:
        numeric *= 100

    formatted = f"{numeric:.{decimals}f}".rstrip("0").rstrip(".")
    return f"{formatted}%" if include_symbol else formatted


def format_currency(value, default="—", decimals=2, currency="$"):
    """Format a currency value safely for UI display."""
    if value in (None, ""):
        return default

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)

    formatted = f"{numeric:,.{decimals}f}".rstrip("0").rstrip(".")
    return f"{currency}{formatted}"


def _normalize_direction(trade_or_direction):
    if isinstance(trade_or_direction, dict):
        candidates = [
            trade_or_direction.get("directional_bias"),
            trade_or_direction.get("strategy_label"),
            trade_or_direction.get("strategy_type"),
            trade_or_direction.get("strategy_key"),
        ]
    else:
        candidates = [trade_or_direction]

    for candidate in candidates:
        normalized = _humanize_value(candidate, default="").lower()
        if "bull" in normalized:
            return "bullish"
        if "bear" in normalized:
            return "bearish"

    return "neutral"


def _get_direction_tokens(trade_or_direction):
    return _DIRECTION_TOKENS.get(
        _normalize_direction(trade_or_direction),
        _DIRECTION_TOKENS["neutral"],
    )


def direction_color(trade_or_direction):
    """Return a semantic accent color for bullish/bearish/neutral states."""
    return _get_direction_tokens(trade_or_direction)["accent"]


def _render_metric_card(container, label, value, accent, delta=None, emphasis="standard"):
    """Render a compact metric card using theme-friendly neutral surfaces and accent cues."""
    font_sizes = {
        "high": "1.9rem",
        "medium": "1.7rem",
        "standard": "1.45rem",
        "compact": "1.18rem",
    }
    font_size = font_sizes.get(emphasis, font_sizes["standard"])

    delta_html = ""
    if delta not in (None, ""):
        delta_html = (
            f"<div style='margin-top:0.25rem;font-size:0.76rem;color:{accent};font-weight:600;'>"
            f"{escape(str(delta))}"
            "</div>"
        )

    container.markdown(
        f"""
        <div style="
            border-left: 4px solid {accent};
            border-radius: 0.55rem;
            padding: 0.6rem 0.75rem;
            background: var(--secondary-background-color, rgba(127, 127, 127, 0.06));
            border-top: 1px solid rgba(127, 127, 127, 0.12);
            border-right: 1px solid rgba(127, 127, 127, 0.12);
            border-bottom: 1px solid rgba(127, 127, 127, 0.12);
            min-height: 82px;
            color: var(--text-color, inherit);
        ">
            <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.03em;font-weight:700;opacity:0.72;">
                {escape(str(label))}
            </div>
            <div style="font-size:{font_size};font-weight:700;line-height:1.1;margin-top:0.2rem;color:var(--text-color, inherit);">
                {escape(str(value))}
            </div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_triplet(pop, ror, score, pop_delta=None, ror_delta=None, score_delta=None):
    """Render a compact fixed metrics row with POP emphasized."""
    col1, col2, col3 = st.columns([1.2, 1, 1], gap="small")

    _render_metric_card(
        col1,
        "POP",
        format_value(pop, decimals=1),
        accent="#14b8a6",
        delta=pop_delta,
        emphasis="high",
    )
    _render_metric_card(
        col2,
        "ROR",
        format_value(ror, decimals=1),
        accent="#f59e0b",
        delta=ror_delta,
        emphasis="medium",
    )
    _render_metric_card(
        col3,
        "Score",
        format_value(score, decimals=2),
        accent="#64748b",
        delta=score_delta,
        emphasis="standard",
    )


def render_summary_bar(summary_items):
    """Render a reusable compact summary strip from input items."""
    items = [item for item in (summary_items or []) if isinstance(item, dict)]
    if not items:
        return

    visible_items = items[:5]
    columns = st.columns(len(visible_items), gap="small")

    for column, item in zip(columns, visible_items):
        value = item.get("value")
        format_type = item.get("format")

        if format_type == "currency":
            rendered_value = format_currency(value)
        elif format_type == "percent":
            rendered_value = format_percentage(
                value,
                include_symbol=item.get("include_symbol", True),
                assume_fraction=item.get("assume_fraction", False),
            )
        else:
            rendered_value = format_value(value)

        accent = item.get("accent") or direction_color(item.get("direction"))
        _render_metric_card(
            column,
            item.get("label", "Item"),
            rendered_value,
            accent=accent,
            delta=item.get("delta"),
            emphasis="compact",
        )


def render_warning_banner(message, level="warning"):
    """Render a reusable warning/info/success banner with safe fallbacks."""
    if not message:
        return

    normalized_level = str(level or "warning").lower()
    if normalized_level in {"error", "danger", "risk"}:
        st.error(message)
    elif normalized_level in {"success", "ok", "healthy"}:
        st.success(message)
    elif normalized_level == "info":
        st.info(message)
    else:
        st.warning(message)


def render_direction_chip(direction):
    """Render a compact bullish/bearish directional chip that remains readable across themes."""
    tokens = _get_direction_tokens(direction)
    tone_map = {
        "Bullish": "bullish",
        "Bearish": "bearish",
        "Neutral": "info",
    }
    render_semantic_chip(tokens["label"], tone=tone_map.get(tokens["label"], "info"))


def _compact_signal_text(signal, max_chars=140):
    text = _humanize_value(signal, default="").strip()
    if not text:
        return None

    text = " ".join(text.split())
    if ". " in text:
        text = text.split(". ", 1)[0].strip() + "."

    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"

    return text


def render_signal_list(signals, title=None):
    """Render short, scannable one-line decision signals only."""
    cleaned_signals = [
        _compact_signal_text(signal)
        for signal in (signals or [])
        if _compact_signal_text(signal)
    ]

    if title:
        render_section_header(title)

    if not cleaned_signals:
        render_empty_state("No active signals", "No short-form signals are available for this section yet.")
        return

    with st.container(border=True):
        for signal in cleaned_signals[:6]:
            st.write(f"- {signal}")


def render_section_header(title, subtitle=None):
    """Render a consistent section heading block."""
    st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def render_empty_state(title, message):
    """Render a consistent empty-state block."""
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.caption(message)


def render_metric_strip(items, columns=3):
    """Render a compact metric strip for detail and execution-prep views."""
    visible_items = [
        item for item in (items or [])
        if isinstance(item, dict) and item.get("label")
    ]
    if not visible_items:
        return

    try:
        column_count = max(1, min(int(columns or 3), 5))
    except (TypeError, ValueError):
        column_count = 3

    for start in range(0, len(visible_items), column_count):
        row_items = visible_items[start:start + column_count]
        row_columns = st.columns(len(row_items), gap="small")

        for container, item in zip(row_columns, row_items):
            value = item.get("value")
            format_type = item.get("format")

            if format_type == "currency":
                rendered_value = format_currency(
                    value,
                    decimals=item.get("decimals", 2),
                    currency=item.get("currency", "$"),
                )
            elif format_type == "percent":
                rendered_value = format_percentage(
                    value,
                    decimals=item.get("decimals", 1),
                    include_symbol=item.get("include_symbol", True),
                    assume_fraction=item.get("assume_fraction", False),
                )
            else:
                rendered_value = format_value(
                    value,
                    decimals=item.get("decimals", 2),
                )

            accent = item.get("accent") or direction_color(item.get("direction"))
            _render_metric_card(
                container,
                item.get("label", "Item"),
                rendered_value,
                accent=accent,
                delta=item.get("delta"),
                emphasis=item.get("emphasis", "compact"),
            )


def render_risk_banner(
    message=None,
    level="warning",
    estimated_risk=None,
    max_loss=None,
    risk_budget=None,
    fits_budget=None,
):
    """Render a concise trader-readable risk banner using passed-in risk context only."""
    if message:
        render_warning_banner(message, level=level)
        return

    parts = []
    banner_level = level or "warning"

    if estimated_risk not in (None, ""):
        parts.append(f"Est. risk {format_currency(estimated_risk)}")
    if max_loss not in (None, ""):
        parts.append(f"Max loss {format_currency(max_loss)}")
    if risk_budget not in (None, ""):
        parts.append(f"Budget {format_currency(risk_budget)}")

    if fits_budget is True:
        parts.append("Fits current risk budget")
        banner_level = "success"
    elif fits_budget is False:
        parts.append("Above current risk budget")
        banner_level = "warning"

    if parts:
        render_warning_banner(" • ".join(parts), level=banner_level)


def render_subsection_card(title, content_callback_or_pattern=None, subtitle=None, accent=None):
    """Render a reusable bordered subsection card from a callback or simple content pattern."""
    accent_color = accent or "#64748b"

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="border-left:4px solid {accent_color};padding-left:0.65rem;margin-bottom:0.2rem;color:var(--text-color, inherit);">
                <div style="font-size:0.96rem;font-weight:700;">{escape(str(title))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if subtitle:
            st.caption(subtitle)

        content = content_callback_or_pattern
        if callable(content):
            content()
            return

        if isinstance(content, dict):
            if not content:
                st.caption("No additional detail available.")
                return
            for key, value in content.items():
                st.markdown(f"- **{_humanize_value(key).title()}:** {format_value(value)}")
            return

        if isinstance(content, (list, tuple)):
            has_items = False
            for item in content:
                if item in (None, "", [], {}):
                    continue
                has_items = True
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or "Item"
                    value = item.get("value") if "value" in item else item.get("text")
                    if value not in (None, ""):
                        st.markdown(f"- **{label}:** {value}")
                else:
                    st.write(f"- {item}")
            if not has_items:
                st.caption("No additional detail available.")
            return

        if content not in (None, ""):
            st.write(content)
        else:
            st.caption("No additional detail available.")


def render_spread_legs_table(spread=None, legs=None, title="Spread Legs"):
    """Render a trader-readable spread legs table from existing spread metadata."""
    rows = []

    if isinstance(legs, list) and legs:
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            rows.append(
                {
                    "Leg": leg.get("leg_type") or leg.get("type") or "Leg",
                    "Strike": format_value(leg.get("strike")),
                    "Mid": format_currency(leg.get("mid"), decimals=3),
                    "Delta": format_value(leg.get("delta"), decimals=3),
                    "Bid": format_currency(leg.get("bid"), decimals=3),
                    "Ask": format_currency(leg.get("ask"), decimals=3),
                    "OI": format_value(leg.get("open_interest")),
                }
            )
    elif isinstance(spread, dict) and spread:
        rows = [
            {
                "Leg": "Short",
                "Strike": format_value(spread.get("short_strike")),
                "Mid": format_currency(spread.get("short_mid"), decimals=3),
                "Delta": format_value(spread.get("short_delta"), decimals=3),
                "Bid": format_currency(spread.get("short_bid"), decimals=3),
                "Ask": format_currency(spread.get("short_ask"), decimals=3),
                "OI": format_value(spread.get("short_open_interest")),
            },
            {
                "Leg": "Long",
                "Strike": format_value(spread.get("long_strike")),
                "Mid": format_currency(spread.get("long_mid"), decimals=3),
                "Delta": format_value(spread.get("long_delta"), decimals=3),
                "Bid": format_currency(spread.get("long_bid"), decimals=3),
                "Ask": format_currency(spread.get("long_ask"), decimals=3),
                "OI": format_value(spread.get("long_open_interest")),
            },
        ]

    def _render_table():
        if not rows:
            st.caption("No leg data is available for this trade.")
            return

        st.table(rows)
        if isinstance(spread, dict) and spread.get("net_credit") not in (None, ""):
            st.caption(f"Net credit: {format_currency(spread.get('net_credit'), decimals=3)}")

    render_subsection_card(title, _render_table, accent=direction_color(spread or legs))


def render_spread_summary(spread, title="Spread Summary"):
    """Render a compact execution-prep summary from existing spread fields only."""
    if not isinstance(spread, dict) or not spread:
        render_empty_state(title, "No spread summary is available for this trade.")
        return

    summary_items = [
        {"label": "Underlying", "value": spread.get("underlying_price"), "format": "currency", "direction": spread},
        {"label": "Net Credit", "value": spread.get("net_credit"), "format": "currency", "accent": "#14b8a6"},
        {"label": "Max Risk", "value": spread.get("max_risk"), "format": "currency", "accent": "#f97316"},
        {"label": "Width", "value": spread.get("spread_width"), "accent": "#64748b"},
        {"label": "Expiration", "value": spread.get("expiration_date"), "accent": "#64748b"},
        {"label": "DTE", "value": spread.get("DTE"), "accent": "#64748b"},
    ]

    render_subsection_card(
        title,
        lambda: render_metric_strip(summary_items, columns=3),
        subtitle=f"{spread.get('ticker', 'Trade')} • {get_strategy_display_name(spread)}",
        accent=direction_color(spread),
    )


def render_detail_signal_groups(strengths=None, cautions=None, risks=None):
    """Render grouped trader-readable strengths, cautions, and risk notes."""
    groups = [
        ("Strengths", strengths or [], "#14b8a6"),
        ("Cautions", cautions or [], "#f59e0b"),
        ("Risks", risks or [], "#f97316"),
    ]

    visible_groups = []
    for title, items, accent in groups:
        cleaned_items = [
            _compact_signal_text(item, max_chars=180) if isinstance(item, str) else item
            for item in items
            if item not in (None, "", [], {})
        ]
        cleaned_items = [item for item in cleaned_items if item not in (None, "", [], {})]
        if cleaned_items:
            visible_groups.append((title, cleaned_items, accent))

    if not visible_groups:
        render_empty_state("No detail signals", "No grouped strengths, cautions, or risks were provided.")
        return

    columns = st.columns(len(visible_groups), gap="small")
    for column, (title, items, accent) in zip(columns, visible_groups):
        with column:
            render_subsection_card(title, items, accent=accent)


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
    """Display a compact 4-column row prioritizing POP, ROR, Score, then DTE."""
    pop = spread.get("POP") if isinstance(spread, dict) else None
    ror = spread.get("ROR") if isinstance(spread, dict) else None
    score = None
    dte = None

    if isinstance(spread, dict):
        score = spread.get("adjusted_score")
        if score in (None, ""):
            score = spread.get("score")
        dte = spread.get("DTE")

    col1, col2, col3, col4 = st.columns([1.2, 1, 1, 0.8], gap="small")
    _render_metric_card(col1, "POP", format_value(pop, decimals=1), "#14b8a6", emphasis="high")
    _render_metric_card(col2, "ROR", format_value(ror, decimals=1), "#f59e0b", emphasis="medium")
    _render_metric_card(col3, "Score", format_value(score, decimals=2), direction_color(spread), emphasis="standard")
    col4.metric("DTE", format_value(dte))


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
