
from pathlib import Path
from engine import run_scan_engine
from history import get_historical_intelligence_summary, load_all_history_runs
from strategies import get_active_strategies
from ui.components import (
    format_currency,
    format_value,
    inject_ui_system_styles,
    render_action_button_row,
    render_bordered_panel,
    render_kpi_metric_card,
    render_metric_row,
    render_page_header,
    render_semantic_chip,
    render_trade_header,
    render_stability_block,
    render_decision_summary,
    render_json_expander,
    get_strategy_display_name,
    render_detail_signal_groups,
    render_direction_chip,
    render_empty_state,
    render_metric_strip,
    render_risk_banner,
    render_section_header,
    render_spread_legs_table,
    render_spread_summary,
    render_subsection_card,
    render_warning_banner,
)
from ui.qualified import EXPANDED_TRADE_STATE_KEY, get_trade_row_key, render_qualified_trades
from ui.alerts import render_alerts
from ui.portfolio import render_portfolio_tab
import streamlit as st


st.set_page_config(page_title="Options Trading App", layout="wide")
inject_ui_system_styles()

if "last_scan_output" not in st.session_state:
    st.session_state["last_scan_output"] = None
if "previous_scan_snapshot" not in st.session_state:
    st.session_state["previous_scan_snapshot"] = None
if "reviewed_trade_keys" not in st.session_state:
    st.session_state["reviewed_trade_keys"] = []
if "selected_trade_key" not in st.session_state:
    st.session_state["selected_trade_key"] = None
if "active_view" not in st.session_state:
    st.session_state["active_view"] = "Overview"
if "scan_control_mode" not in st.session_state:
    st.session_state["scan_control_mode"] = "Expert Mode"
if "sidebar_render_mode" not in st.session_state:
    st.session_state["sidebar_render_mode"] = None
if "scan_profile" not in st.session_state:
    st.session_state["scan_profile"] = "balanced"
if "scan_ticker_group" not in st.session_state:
    st.session_state["scan_ticker_group"] = "tech"
if "scan_dte_min" not in st.session_state:
    st.session_state["scan_dte_min"] = 20
if "scan_dte_max" not in st.session_state:
    st.session_state["scan_dte_max"] = 35
if "scan_min_score" not in st.session_state:
    st.session_state["scan_min_score"] = 65
if "scan_min_consistency" not in st.session_state:
    st.session_state["scan_min_consistency"] = 3
if "scan_min_pop" not in st.session_state:
    st.session_state["scan_min_pop"] = 0
if "scan_min_ror" not in st.session_state:
    st.session_state["scan_min_ror"] = 0
if EXPANDED_TRADE_STATE_KEY not in st.session_state:
    st.session_state[EXPANDED_TRADE_STATE_KEY] = None

MAIN_VIEWS = [
    "Overview",
    "Portfolio",
    "Alerts",
    "Qualified Trades",
    "Trade Detail",
    "History",
    "Daily Summary",
    "Raw Output",
]

SIDEBAR_MODES = ["Expert Mode", "Guided Mode"]
GUIDED_APPROACH_OPTIONS = [
    ("Play it safe", "conservative"),
    ("Balanced", "balanced"),
    ("Go for bigger returns", "aggressive"),
]
GUIDED_MARKET_OPTIONS = [
    ("Big tech companies", "tech"),
    ("Broad market funds", "index"),
    ("A mix of both", "mixed"),
]
GUIDED_SELECTIVITY_OPTIONS = [
    ("Show me more ideas", 55),
    ("Use a balanced filter", 65),
    ("Only the stronger setups", 75),
]
GUIDED_CONSISTENCY_OPTIONS = [
    ("Seen often already", 5),
    ("Seen a few times", 3),
    ("I’m open to newer setups", 2),
]


def _label_for_value(options, target_value, default_label):
    for label, value in options:
        if value == target_value:
            return label
    return default_label


def _label_for_tuple_value(options, target_value, default_label):
    normalized_target = tuple(target_value or ())
    for label, value in options:
        if tuple(value) == normalized_target:
            return label
    return default_label


def _label_for_nearest_numeric(options, target_value, default_label):
    if target_value in (None, ""):
        return default_label

    try:
        numeric_target = float(target_value)
    except (TypeError, ValueError):
        return default_label

    return min(
        options,
        key=lambda item: abs(float(item[1]) - numeric_target),
        default=(default_label, None),
    )[0]


def _ensure_scan_strategy_state(active_strategy_keys):
    current_selection = st.session_state.get("scan_selected_strategy_keys")
    if not current_selection:
        st.session_state["scan_selected_strategy_keys"] = list(active_strategy_keys)
        return

    filtered_selection = [key for key in current_selection if key in active_strategy_keys]
    st.session_state["scan_selected_strategy_keys"] = filtered_selection or list(active_strategy_keys)


def _sync_expert_sidebar_state(active_strategy_keys):
    st.session_state["expert_profile_ui"] = st.session_state["scan_profile"]
    st.session_state["expert_ticker_group_ui"] = st.session_state["scan_ticker_group"]
    st.session_state["expert_strategy_ui"] = [
        key for key in st.session_state["scan_selected_strategy_keys"] if key in active_strategy_keys
    ] or list(active_strategy_keys)
    st.session_state["expert_dte_min_ui"] = st.session_state["scan_dte_min"]
    st.session_state["expert_dte_max_ui"] = st.session_state["scan_dte_max"]
    st.session_state["expert_min_score_ui"] = st.session_state["scan_min_score"]
    st.session_state["expert_min_pop_ui"] = st.session_state.get("scan_min_pop", 0)
    st.session_state["expert_min_ror_ui"] = st.session_state.get("scan_min_ror", 0)
    st.session_state["expert_min_consistency_ui"] = st.session_state["scan_min_consistency"]


def _sync_guided_sidebar_state(active_strategies, active_strategy_keys):
    st.session_state["guided_strategy_ui"] = [
        key for key in st.session_state["scan_selected_strategy_keys"] if key in active_strategy_keys
    ] or list(active_strategy_keys)
    st.session_state["guided_weeks_ui"] = (
        max(1, min(52, int(round(float(st.session_state["scan_dte_min"]) / 7.0)))),
        max(1, min(52, int(round(float(st.session_state["scan_dte_max"]) / 7.0)))),
    )
    if st.session_state["guided_weeks_ui"][0] > st.session_state["guided_weeks_ui"][1]:
        st.session_state["guided_weeks_ui"] = (
            st.session_state["guided_weeks_ui"][1],
            st.session_state["guided_weeks_ui"][0],
        )
    st.session_state["guided_selectivity_label"] = _label_for_nearest_numeric(
        GUIDED_SELECTIVITY_OPTIONS,
        st.session_state["scan_min_score"],
        GUIDED_SELECTIVITY_OPTIONS[1][0],
    )
    st.session_state["guided_consistency_label"] = _label_for_nearest_numeric(
        GUIDED_CONSISTENCY_OPTIONS,
        st.session_state["scan_min_consistency"],
        GUIDED_CONSISTENCY_OPTIONS[1][0],
    )
    st.session_state["guided_outlook_ui"] = _resolve_guided_outlook(
        st.session_state["guided_strategy_ui"],
        active_strategies,
        active_strategy_keys,
    )


def _get_directional_strategy_keys(active_strategies, direction):
    return [
        strategy["key"]
        for strategy in active_strategies
        if strategy.get("directional_bias") == direction
    ]


def _resolve_guided_outlook(selected_strategy_keys, active_strategies, active_strategy_keys):
    selected = set(selected_strategy_keys or [])
    if not selected:
        return "auto"

    bullish_keys = set(_get_directional_strategy_keys(active_strategies, "bullish"))
    bearish_keys = set(_get_directional_strategy_keys(active_strategies, "bearish"))
    active_set = set(active_strategy_keys)

    bullish_selected = bool(selected & bullish_keys)
    bearish_selected = bool(selected & bearish_keys)

    if bullish_selected and bearish_selected:
        return "either"
    if bullish_selected:
        return "up"
    if bearish_selected:
        return "down"
    if selected == active_set:
        return "auto"

    return "auto"


def _strategies_for_guided_outlook(outlook_value, active_strategies, active_strategy_keys):
    bullish_keys = _get_directional_strategy_keys(active_strategies, "bullish")
    bearish_keys = _get_directional_strategy_keys(active_strategies, "bearish")

    if outlook_value == "up":
        return bullish_keys or list(active_strategy_keys)
    if outlook_value == "down":
        return bearish_keys or list(active_strategy_keys)

    return list(active_strategy_keys)


def _escape_css_class_fragment(value):
    return "".join(character if character.isalnum() or character in "-_" else "-" for character in str(value))


def _render_guided_choice_card_styles(state_key_prefix, card_options, selected_value):
    style_rules = []

    for index, option in enumerate(card_options):
        option_value = option[1]
        is_selected = option_value == selected_value
        key_name = _escape_css_class_fragment(f"{state_key_prefix}_{index}")
        border_color = "rgba(22, 163, 74, 0.72)" if is_selected else "rgba(148, 163, 184, 0.26)"
        background_color = "rgba(34, 197, 94, 0.10)" if is_selected else "rgba(255, 255, 255, 0.02)"
        shadow_color = "rgba(22, 163, 74, 0.12)" if is_selected else "rgba(15, 23, 42, 0.04)"
        accent_color = "#16a34a" if is_selected else "rgba(148, 163, 184, 0.30)"
        indicator_opacity = "1" if is_selected else "0"

        style_rules.append(
            f"""
            .st-key-{key_name} {{
                position: relative;
                margin-bottom: 0.5rem;
            }}
            .st-key-{key_name} > div[data-testid="stButton"] {{
                position: relative;
            }}
            .st-key-{key_name} > div[data-testid="stButton"]::before {{
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 4px;
                border-radius: 0.85rem 0 0 0.85rem;
                background: {accent_color};
                pointer-events: none;
                z-index: 2;
            }}
            .st-key-{key_name} > div[data-testid="stButton"]::after {{
                content: '✓';
                position: absolute;
                top: 0.9rem;
                right: 0.9rem;
                width: 1.2rem;
                height: 1.2rem;
                border-radius: 999px;
                border: 1px solid rgba(22, 163, 74, 0.35);
                background: rgba(22, 163, 74, 0.14);
                color: #15803d;
                font-size: 0.78rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: {indicator_opacity};
                pointer-events: none;
                z-index: 2;
            }}
            .st-key-{key_name} button {{
                width: 100%;
                min-height: 5.35rem;
                padding: 0.85rem 2.5rem 0.85rem 1rem;
                border-radius: 0.85rem;
                border: 1px solid {border_color};
                background: {background_color};
                color: inherit;
                box-shadow: 0 10px 24px {shadow_color};
                text-align: left;
                white-space: pre-wrap;
                line-height: 1.35;
                font-weight: 600;
                transition: border-color 120ms ease, background 120ms ease, box-shadow 120ms ease, transform 120ms ease;
            }}
            .st-key-{key_name} button:hover {{
                border-color: rgba(22, 163, 74, 0.45);
                background: rgba(34, 197, 94, 0.08);
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
                transform: translateY(-1px);
            }}
            .st-key-{key_name} button:focus {{
                outline: none;
                border-color: rgba(22, 163, 74, 0.65);
                box-shadow: 0 0 0 0.18rem rgba(34, 197, 94, 0.18);
            }}
            .st-key-{key_name} button p {{
                margin: 0;
                text-align: left;
            }}
            """
        )

    st.sidebar.markdown(f"<style>{''.join(style_rules)}</style>", unsafe_allow_html=True)


def _render_guided_choice_cards(question, card_options, selected_value, state_key_prefix):
    st.sidebar.markdown(f"**{question}**")
    current_value = selected_value

    _render_guided_choice_card_styles(state_key_prefix, card_options, current_value)

    for index, option in enumerate(card_options):
        label = option[0]
        value = option[1]
        helper_text = option[2] if len(option) > 2 else ""
        is_selected = value == current_value
        helper_line = f"\n{helper_text}" if helper_text else ""
        card_label = f"{label}{helper_line}"

        if st.sidebar.button(
            card_label,
            key=f"{state_key_prefix}_{index}",
            use_container_width=True,
            type="secondary",
        ):
            if not is_selected:
                current_value = value

    return current_value


def _render_guided_strategy_chips(active_strategy_keys, strategy_label_lookup):
    st.sidebar.markdown("**What strategies should PRIS look for?**")
    st.sidebar.caption("Select one or more strategy chips.")

    selected_set = set(st.session_state.get("guided_strategy_ui") or st.session_state.get("scan_selected_strategy_keys") or [])
    if not selected_set:
        selected_set = set(active_strategy_keys)

    columns = st.sidebar.columns(2, gap="small")
    for index, key in enumerate(active_strategy_keys):
        column = columns[index % 2]
        selected = key in selected_set

        with column:
            if st.button(
                strategy_label_lookup.get(key, key),
                key=f"guided_strategy_chip_{key}",
                type="primary" if selected else "secondary",
                use_container_width=True,
            ):
                if selected and len(selected_set) > 1:
                    selected_set.remove(key)
                elif not selected:
                    selected_set.add(key)
                st.session_state["guided_strategy_ui"] = [
                    strategy_key for strategy_key in active_strategy_keys if strategy_key in selected_set
                ]
                st.rerun()

    ordered_selection = [key for key in active_strategy_keys if key in selected_set]
    st.session_state["guided_strategy_ui"] = ordered_selection
    return ordered_selection


def _render_sidebar_mode_toggle():
    if hasattr(st.sidebar, "segmented_control"):
        selected_mode = st.sidebar.segmented_control(
            "Mode",
            options=SIDEBAR_MODES,
            default=st.session_state.get("scan_control_mode", SIDEBAR_MODES[0]),
        )
    else:
        selected_mode = st.sidebar.radio(
            "Mode",
            options=SIDEBAR_MODES,
            index=SIDEBAR_MODES.index(st.session_state.get("scan_control_mode", SIDEBAR_MODES[0])),
        )

    st.session_state["scan_control_mode"] = selected_mode or SIDEBAR_MODES[0]
    return st.session_state["scan_control_mode"]





def _render_expert_sidebar(active_strategy_keys, strategy_label_lookup, last_output):
    st.sidebar.markdown("#### Primary Controls")
    st.sidebar.caption("Core scan inputs.")

    profile = st.sidebar.selectbox(
        "Profile",
        ["balanced", "aggressive", "conservative"],
        key="expert_profile_ui",
    )
    ticker_group = st.sidebar.selectbox(
        "Ticker Group",
        ["tech", "index", "mixed"],
        key="expert_ticker_group_ui",
    )

    st.sidebar.markdown("#### Strategies")
    selected_strategy_keys = st.sidebar.multiselect(
        "Strategies to scan",
        options=active_strategy_keys,
        format_func=lambda key: strategy_label_lookup.get(key, key),
        key="expert_strategy_ui",
    )
    if not selected_strategy_keys:
        selected_strategy_keys = list(active_strategy_keys)

    with st.sidebar.expander("Advanced Controls", expanded=False):
        dte_min = st.number_input(
            "DTE Min",
            min_value=1,
            max_value=365,
            step=1,
            key="expert_dte_min_ui",
        )
        dte_max = st.number_input(
            "DTE Max",
            min_value=1,
            max_value=365,
            step=1,
            key="expert_dte_max_ui",
        )
        min_score = st.number_input(
            "Min Score",
            min_value=0,
            max_value=100,
            step=1,
            key="expert_min_score_ui",
        )
        st.number_input(
            "Min POP",
            min_value=0,
            max_value=100,
            step=1,
            key="expert_min_pop_ui",
        )
        st.number_input(
            "Min ROR",
            min_value=0,
            max_value=100,
            step=1,
            key="expert_min_ror_ui",
        )
        min_consistency = st.number_input(
            "Min Stability Appearances",
            min_value=0,
            max_value=20,
            step=1,
            key="expert_min_consistency_ui",
        )

    st.session_state["scan_profile"] = profile
    st.session_state["scan_ticker_group"] = ticker_group
    st.session_state["scan_selected_strategy_keys"] = list(selected_strategy_keys)
    st.session_state["scan_dte_min"] = dte_min
    st.session_state["scan_dte_max"] = dte_max
    st.session_state["scan_min_score"] = min_score
    st.session_state["scan_min_pop"] = st.session_state.get("expert_min_pop_ui", 0)
    st.session_state["scan_min_ror"] = st.session_state.get("expert_min_ror_ui", 0)
    st.session_state["scan_min_consistency"] = min_consistency

    return "Run Scan"


def _render_sidebar_state_prescan(mode):
    """Render pre-scan readiness state at the top of the sidebar."""
    if mode == "Expert Mode":
        message = "Configuration ready"
        caption = "Click to run the scan with your current settings."
    else:
        message = "PRIS is ready"
        caption = "Answer the questions below, then click to find opportunities."

    with st.sidebar.container(border=True):
        st.markdown(f"**{message}**")
        st.caption(caption)


def _render_sidebar_state_loading(mode):
    """Render loading state during scan execution."""
    if mode == "Expert Mode":
        st.sidebar.info("Scan is running...")
    else:
        st.sidebar.info("PRIS is searching for opportunities...")


def _render_sidebar_state_postscan(output, mode):
    """Render unified latest scan summary at the top of the sidebar."""
    if not output:
        return

    summary = output.get("summary", {})
    qualified_count = summary.get("qualified_count", 0)
    alerts_count = len(output.get("alerts", []) or [])
    exec_time = output.get("execution_time_seconds", "n/a")
    qualified = output.get("qualified", [])
    top_overall = summary.get("top_overall") or (qualified[0] if qualified else None)
    profile = output.get("profile", "n/a")
    ticker_group = output.get("ticker_group", "n/a")

    if mode == "Expert Mode":
        top_label = "Top:" if top_overall else ""
    else:
        top_label = "Best match:" if top_overall else ""

    with st.sidebar.container(border=True):
        st.markdown("**Latest Scan**")
        col1, col2 = st.columns(2)
        col1.metric("Qualified", qualified_count)
        col2.metric("Alerts", alerts_count)

        if top_overall:
            ticker = top_overall.get("ticker", "N/A")
            strategy = get_strategy_display_name(top_overall, default="Trade")
            st.caption(f"{top_label} {ticker} | {strategy}")

        st.caption(f"Profile: {profile} | Tickers: {ticker_group}")

        if isinstance(exec_time, (int, float)):
            st.caption(f"Scan time: {exec_time:.2f}s")


def _render_guided_sidebar(active_strategy_keys, strategy_label_lookup):
    st.sidebar.markdown("#### Primary Controls")
    st.sidebar.markdown(
        """
        <div style="
            padding:0.55rem 0.6rem;
            border-radius:0.5rem;
            border:1px solid rgba(34, 197, 94, 0.28);
            background:rgba(34, 197, 94, 0.08);
            margin-bottom:0.55rem;
        ">
            <div style="font-size:0.92rem;font-weight:700;color:var(--text-color, inherit);">PRIS Assistant</div>
            <div style="font-size:0.78rem;opacity:0.84;margin-top:0.16rem;">Answer a few simple questions and PRIS will set up the scan for you.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    approach_value = _render_guided_choice_cards(
        "How much risk are you comfortable with?",
        [
            ("Play it safe", "conservative", "I prefer smaller, more consistent results."),
            ("Balanced", "balanced", "A mix of safety and opportunity."),
            ("Go for bigger returns", "aggressive", "I’m okay taking more risk for better upside."),
        ],
        st.session_state.get("scan_profile", "balanced"),
        "guided_approach_card",
    )

    market_value = _render_guided_choice_cards(
        "What do you want to trade?",
        [
            ("Big tech companies", "tech", "Apple, Microsoft, Nvidia, and similar names."),
            ("Broad market funds", "index", "Index-style names like the S&P 500."),
            ("A mix of both", "mixed", "A blend of tech names and broad market exposure."),
        ],
        st.session_state.get("scan_ticker_group", "tech"),
        "guided_market_card",
    )

    st.sidebar.markdown("**How long do you want to stay in the trade?**")
    label_left, label_right = st.sidebar.columns(2)
    label_left.caption("Sooner")
    label_right.caption("Later")

    default_weeks = tuple(st.session_state.get("guided_weeks_ui", (3, 5)))
    if len(default_weeks) != 2:
        default_weeks = (3, 5)
    min_week = max(2, min(8, int(default_weeks[0])))
    max_week = max(min_week, min(8, int(default_weeks[1])))
    weeks_range = st.sidebar.slider(
        "Time window",
        min_value=2,
        max_value=8,
        value=(min_week, max_week),
        step=1,
        key="guided_weeks_slider",
    )
    interpreted_window = f"{weeks_range[0]}-{weeks_range[1]} weeks"
    st.sidebar.caption(f"I will look for trades that usually play out over about {interpreted_window}.")

    active_strategies = get_active_strategies()
    outlook_value = _render_guided_choice_cards(
        "What’s your market outlook?",
        [
            ("Let PRIS decide for me", "auto", "Use both bullish and bearish ideas if needed."),
            ("I think markets will go up", "up", "Focus on setups that benefit from strength."),
            ("I think markets will go down", "down", "Focus on setups that benefit from weakness."),
            ("Either direction is fine", "either", "Show me opportunities on either side."),
        ],
        st.session_state.get(
            "guided_outlook_ui",
            _resolve_guided_outlook(
                st.session_state.get("scan_selected_strategy_keys"),
                active_strategies,
                active_strategy_keys,
            ),
        ),
        "guided_outlook_card",
    )
    selected_strategy_keys = _strategies_for_guided_outlook(
        outlook_value,
        active_strategies,
        active_strategy_keys,
    )

    selectivity_value = _render_guided_choice_cards(
        "How picky should we be?",
        [
            ("Show me more ideas", 55, "Cast a wider net and include more possibilities."),
            ("Use a balanced filter", 65, "A practical middle ground between quality and volume."),
            ("Only the stronger setups", 75, "Focus on a smaller set of higher-quality ideas."),
        ],
        st.session_state.get("scan_min_score", 65),
        "guided_selectivity_card",
    )

    consistency_value = _render_guided_choice_cards(
        "How many prior appearances should the trade have?",
        [
            ("Seen often already", 5, "Prioritize trades that have appeared repeatedly across runs."),
            ("Seen a few times", 3, "Use a balanced historical appearance threshold."),
            ("I’m open to newer setups", 2, "Allow newer ideas that have appeared fewer times so far."),
        ],
        st.session_state.get("scan_min_consistency", 3),
        "guided_consistency_card",
    )

    dte_min = int(weeks_range[0] * 7)
    dte_max = int(weeks_range[1] * 7)

    st.session_state["guided_weeks_ui"] = weeks_range
    st.session_state["guided_outlook_ui"] = outlook_value
    st.session_state["scan_profile"] = approach_value
    st.session_state["scan_ticker_group"] = market_value
    st.session_state["scan_selected_strategy_keys"] = list(selected_strategy_keys)
    st.session_state["scan_dte_min"] = dte_min
    st.session_state["scan_dte_max"] = dte_max
    st.session_state["scan_min_score"] = int(selectivity_value)
    st.session_state["scan_min_consistency"] = int(consistency_value)

    profile_summary_lookup = {
        "conservative": "safer",
        "balanced": "balanced",
        "aggressive": "higher-upside",
    }
    market_summary_lookup = {
        "tech": "big tech names",
        "index": "broad market funds",
        "mixed": "a mix of tech and broad market names",
    }
    outlook_summary_lookup = {
        "auto": "I can look both up and down based on what the market is doing",
        "up": "I will focus on ideas that benefit when markets rise",
        "down": "I will focus on ideas that benefit when markets fall",
        "either": "I will include opportunities in either direction",
    }
    strictness_summary_lookup = {
        55: "I will include more possible ideas",
        65: "I will keep a balanced quality bar",
        75: "I will focus on stronger setups only",
    }
    confidence_summary_lookup = {
        5: "that have appeared repeatedly across runs",
        3: "with a balanced historical appearance requirement",
        2: "including some newer setups",
    }

    with st.sidebar.container(border=True):
        st.markdown("#### Your plan")
        st.caption(
            f"You’re looking for {profile_summary_lookup.get(approach_value, 'balanced')} opportunities in {market_summary_lookup.get(market_value, 'your selected market')} over the next {interpreted_window}."
        )
        st.write(outlook_summary_lookup.get(outlook_value, "I will consider both market directions."))
        st.write(strictness_summary_lookup.get(int(selectivity_value), "I will use your selected quality filter."))
        st.write(
            f"I will prioritize opportunities {confidence_summary_lookup.get(int(consistency_value), 'based on your selected confidence setting')}."
        )

    return "Find Opportunities"

BASE_DIR = Path(__file__).resolve().parent
MAIN_PY = BASE_DIR / "main.py"

st.title("Options Trading Dashboard")
st.caption(
    "Decision-support dashboard for reviewing credit spread opportunities, run quality, and historical context."
)

with st.container(border=True):
    st.markdown("#### How to use this dashboard")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**1. Configure & run**")
        st.caption("Use the sidebar to choose the profile, ticker group, and strategies for the current scan.")

    with col2:
        st.markdown("**2. Start in Overview**")
        st.caption("Review the Top Decision, system signals, and portfolio context to understand the run quickly.")

    with col3:
        st.markdown("**3. Validate in detail**")
        st.caption("Use Alerts, Qualified Trades, History, and Daily Summary to confirm and compare candidates.")

    st.caption(
        "Analytical use only — the dashboard supports review and prioritization; final trade decisions remain manual."
    )

active_strategies = get_active_strategies()
active_strategy_keys = [strategy["key"] for strategy in active_strategies]
strategy_label_lookup = {
    strategy["key"]: strategy.get("display_label", strategy["key"]).replace("_", " ").title()
    for strategy in active_strategies
}

_ensure_scan_strategy_state(active_strategy_keys)

st.sidebar.header("Scan Control Panel")
st.sidebar.caption("Choose how you want to configure the same scan engine inputs.")
st.sidebar.markdown("#### Mode + Latest Scan")

sidebar_mode = _render_sidebar_mode_toggle()
if st.session_state.get("sidebar_render_mode") != sidebar_mode:
    if sidebar_mode == "Expert Mode":
        _sync_expert_sidebar_state(active_strategy_keys)
    else:
        _sync_guided_sidebar_state(active_strategies, active_strategy_keys)
    st.session_state["sidebar_render_mode"] = sidebar_mode

current_output = st.session_state.get("last_scan_output")
if current_output:
    _render_sidebar_state_postscan(current_output, sidebar_mode)
else:
    _render_sidebar_state_prescan(sidebar_mode)

st.sidebar.markdown("---")

if sidebar_mode == "Expert Mode":
    cta_label = _render_expert_sidebar(
        active_strategy_keys,
        strategy_label_lookup,
        st.session_state.get("last_scan_output"),
    )
else:
    cta_label = _render_guided_sidebar(
        active_strategy_keys,
        strategy_label_lookup,
    )

with st.sidebar.expander("Quick guide", expanded=False):
    st.markdown(
        "- **Overview:** Start here for the headline view.\n"
        "- **Qualified Trades:** Review the strongest current candidates.\n"
        "- **History:** Use recurring context from prior runs."
    )

    st.sidebar.markdown("---")

profile = st.session_state["scan_profile"]
ticker_group = st.session_state["scan_ticker_group"]
selected_strategy_keys = st.session_state["scan_selected_strategy_keys"]
dte_min = st.session_state["scan_dte_min"]
dte_max = st.session_state["scan_dte_max"]
min_score = st.session_state["scan_min_score"]
min_consistency = st.session_state["scan_min_consistency"]

run_button = st.sidebar.button(cta_label, use_container_width=True)

if run_button:
    _render_sidebar_state_loading(sidebar_mode)


def run_scan(
    profile,
    ticker_group,
    dte_min,
    dte_max,
    min_score,
    min_consistency,
    selected_strategy_keys,
):
    return run_scan_engine(
        profile_name=profile,
        group_name=ticker_group,
        dte_min=dte_min,
        dte_max=dte_max,
        min_score=min_score,
        min_consistency=min_consistency,
        export_csv=False,
        selected_strategy_keys=selected_strategy_keys,
    )


def get_trade_value(primary_spread, fallback_spread, key, default=None):
    """Prefer the summary trade value, then fall back to the top qualified trade."""
    if primary_spread and primary_spread.get(key) not in (None, ""):
        return primary_spread.get(key)

    if fallback_spread and fallback_spread.get(key) not in (None, ""):
        return fallback_spread.get(key)

    score_breakdown = (fallback_spread or {}).get("score_breakdown", {})
    if score_breakdown.get(key) not in (None, ""):
        return score_breakdown.get(key)

    return default


def get_opportunity_label(spread):
    """Return a lightweight presentation label based on the engine-provided score."""
    score = spread.get("adjusted_score") if spread else None

    if score is None:
        return "Opportunity available"
    if score >= 70:
        return "Strong opportunity"
    if score >= 60:
        return "Moderate opportunity"
    return "Weak opportunity"


def set_selected_trade_for_detail(spread):
    """Persist the currently selected trade and route the user to the detail view."""
    trade_key = get_trade_row_key(spread)
    if trade_key:
        st.session_state["selected_trade_key"] = trade_key
    st.session_state["active_view"] = "Trade Detail"


def set_selected_trade_for_compare(spread):
    """Persist the selected trade and route the user back to the qualified board for comparison."""
    trade_key = get_trade_row_key(spread)
    if trade_key:
        st.session_state["selected_trade_key"] = trade_key
    st.session_state["active_view"] = "Qualified Trades"


def render_main_view_selector():
    """Render a controllable main-view selector backed by session state."""
    current_view = st.session_state.get("active_view", "Overview")
    if current_view not in MAIN_VIEWS:
        current_view = "Overview"
        st.session_state["active_view"] = current_view

    if hasattr(st, "segmented_control"):
        selected_view = st.segmented_control(
            "View",
            options=MAIN_VIEWS,
            default=current_view,
        )
    else:
        selected_view = st.radio(
            "View",
            options=MAIN_VIEWS,
            index=MAIN_VIEWS.index(current_view),
            horizontal=True,
        )

    if selected_view:
        st.session_state["active_view"] = selected_view

    return st.session_state["active_view"]


def find_selected_trade(qualified, fallback_trade=None):
    """Resolve the user-selected detail trade from the current qualified set."""
    selected_key = st.session_state.get("selected_trade_key")

    if selected_key:
        for spread in qualified or []:
            if get_trade_row_key(spread) == selected_key:
                return spread

        if fallback_trade and get_trade_row_key(fallback_trade) == selected_key:
            return fallback_trade

    return fallback_trade or (qualified[0] if qualified else None)


def _score_from_trade(spread):
    if not isinstance(spread, dict):
        return None

    value = spread.get("adjusted_score")
    if value in (None, ""):
        value = spread.get("score")

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _breakeven_from_trade(spread):
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


def _build_scan_snapshot(output):
    if not output:
        return None

    summary = output.get("summary", {})
    qualified = output.get("qualified", []) or []
    alerts = output.get("alerts", []) or []
    score_values = [value for value in (_score_from_trade(spread) for spread in qualified) if value is not None]
    top_trade = summary.get("top_overall") or (qualified[0] if qualified else None)

    return {
        "qualified_count": summary.get("qualified_count", len(qualified)),
        "alerts_count": len(alerts),
        "average_score": round(sum(score_values) / len(score_values), 1) if score_values else None,
        "top_trade_key": get_trade_row_key(top_trade) if top_trade else None,
        "top_trade_label": (
            f"{top_trade.get('ticker', 'N/A')} | {get_strategy_display_name(top_trade, default='Trade')}"
            if isinstance(top_trade, dict) and top_trade
            else None
        ),
        "qualified_keys": [
            get_trade_row_key(spread)
            for spread in qualified
            if get_trade_row_key(spread)
        ],
    }


def render_overview_snapshot(output, summary, qualified, alerts, top_overall):
    qualified_count = summary.get("qualified_count", len(qualified))
    alerts_count = len(alerts)
    strategy_name = get_strategy_display_name(top_overall, default="No trade") if top_overall else "No trade"
    ticker = (top_overall or {}).get("ticker", "N/A")

    stable_count = sum(1 for spread in qualified if spread.get("stability_level") == "stable")
    score_values = [value for value in (_score_from_trade(spread) for spread in qualified) if value is not None]
    average_score = round(sum(score_values) / len(score_values), 1) if score_values else "n/a"

    panel = render_bordered_panel(
        "Decision Snapshot",
        "Quick scan summary for immediate triage.",
    )
    with panel:
        meta_col, chip_col = st.columns([4, 1], gap="small")
        with meta_col:
            st.markdown(f"### {ticker} | {strategy_name}")
            st.caption("Top candidate from the current run.")
        with chip_col:
            if top_overall:
                render_direction_chip(top_overall)
            else:
                render_semantic_chip("No Top Trade", tone="info")

        metric_cols = st.columns(4, gap="small")
        render_kpi_metric_card(metric_cols[0], "Qualified Trades", qualified_count, accent="bullish")
        render_kpi_metric_card(metric_cols[1], "Alerts", alerts_count, accent="warning")
        render_kpi_metric_card(metric_cols[2], "Stable Trades", stable_count, accent="info")
        render_kpi_metric_card(metric_cols[3], "Average Score", average_score, accent="bearish")

    preview_panel = render_bordered_panel(
        "Top Trade Preview",
        "Most actionable candidate under current filters.",
    )
    with preview_panel:
        if not top_overall:
            render_empty_state(
                "No Top Trade",
                "No trade currently leads this run. Review alerts and qualified views for broader context.",
            )
        else:
            render_metric_strip(
                [
                    {"label": "POP", "value": top_overall.get("POP"), "format": "percent", "accent": "#14b8a6", "emphasis": "high"},
                    {"label": "ROR", "value": top_overall.get("ROR"), "format": "percent", "accent": "#f59e0b", "emphasis": "medium"},
                    {"label": "Score", "value": _score_from_trade(top_overall), "accent": "#64748b"},
                ],
                columns=3,
            )

            explanation = (
                top_overall.get("decision_summary")
                or top_overall.get("status_reason")
                or "No short explanation is available for this trade yet."
            )
            st.caption(explanation)

            if st.button("Review trade", key="overview_review_trade", use_container_width=True, type="primary"):
                set_selected_trade_for_detail(top_overall)
                st.rerun()

    previous_snapshot = st.session_state.get("previous_scan_snapshot")
    if previous_snapshot:
        previous_qualified = previous_snapshot.get("qualified_count", 0)
        previous_alerts = previous_snapshot.get("alerts_count", 0)
        qualified_delta = qualified_count - previous_qualified
        alerts_delta = alerts_count - previous_alerts

        previous_keys = set(previous_snapshot.get("qualified_keys") or [])
        current_keys = {
            get_trade_row_key(spread)
            for spread in qualified
            if get_trade_row_key(spread)
        }
        new_trades_count = len(current_keys - previous_keys)
        stable_ratio = f"{round((stable_count / qualified_count) * 100)}%" if qualified_count else "n/a"

        trend_panel = render_bordered_panel(
            "Activity Since Last Run",
            "Quick trend signals from the latest run-over-run comparison.",
        )
        with trend_panel:
            trend_cols = st.columns(4, gap="small")
            render_kpi_metric_card(trend_cols[0], "Qualified Delta", f"{qualified_delta:+d}", accent="info")
            render_kpi_metric_card(trend_cols[1], "Alerts Delta", f"{alerts_delta:+d}", accent="warning")
            render_kpi_metric_card(trend_cols[2], "New Trades", new_trades_count, accent="bullish")
            render_kpi_metric_card(trend_cols[3], "Stable Ratio", stable_ratio, accent="bearish")

    action_panel = render_bordered_panel("Next Actions", "Move directly to deeper review screens.")
    with action_panel:
        actions = render_action_button_row(
            [
                {"label": "View Qualified Trades", "key": "overview_to_qualified", "type": "secondary"},
                {"label": "View Alerts", "key": "overview_to_alerts", "type": "secondary"},
                {"label": "Run New Scan", "key": "overview_run_new_scan", "type": "primary"},
            ]
        )

        if actions.get("overview_to_qualified"):
            st.session_state["active_view"] = "Qualified Trades"
            st.rerun()
        if actions.get("overview_to_alerts"):
            st.session_state["active_view"] = "Alerts"
            st.rerun()
        if actions.get("overview_run_new_scan"):
            st.info("Use the sidebar Run button to launch a new scan with your current settings.")


def _compact_text_line(text, max_chars=180):
    raw = str(text or "").strip()
    if not raw:
        return ""

    clean = " ".join(raw.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 1].rstrip() + "..."


def render_trade_detail_execution_view(selected_trade, summary, qualified, output):
    if not isinstance(selected_trade, dict) or not selected_trade:
        render_empty_state(
            "No trade selected",
            "Choose a trade from Qualified Trades to open this execution view.",
        )
        return

    ticker = selected_trade.get("ticker", "N/A")
    strategy_name = get_strategy_display_name(selected_trade, default="Trade")
    score_value = _score_from_trade(selected_trade)
    score_display = format_value(score_value, decimals=2)
    reviewed_keys = set(st.session_state.get("reviewed_trade_keys") or [])
    row_key = get_trade_row_key(selected_trade)

    header_panel = render_bordered_panel(
        "Decision Header",
        "Primary execution snapshot for the selected trade.",
    )
    with header_panel:
        title_col, chip_col = st.columns([4.6, 1], gap="small")
        with title_col:
            st.markdown(f"### {ticker} | {strategy_name}")
            st.caption("Quick decision inputs: score, POP, and ROR.")
        with chip_col:
            render_direction_chip(selected_trade)

        render_metric_strip(
            [
                {"label": "Score", "value": score_display, "accent": "#64748b", "emphasis": "high"},
                {"label": "POP", "value": selected_trade.get("POP"), "format": "percent", "accent": "#14b8a6", "emphasis": "medium"},
                {"label": "ROR", "value": selected_trade.get("ROR"), "format": "percent", "accent": "#f59e0b", "emphasis": "medium"},
            ],
            columns=3,
        )

    verdict_panel = render_bordered_panel(
        "Quick Verdict",
        "1-2 line readout from current run explanations.",
    )
    with verdict_panel:
        verdict_text = (
            selected_trade.get("decision_summary")
            or selected_trade.get("status_reason")
            or selected_trade.get("explanation")
            or "No concise explanation is available for this trade yet."
        )
        st.write(_compact_text_line(verdict_text, max_chars=220))

    construction_panel = render_bordered_panel(
        "Trade Construction",
        "Execution structure and contract shape.",
    )
    with construction_panel:
        render_metric_strip(
            [
                {"label": "Short Strike", "value": format_value(selected_trade.get("short_strike"))},
                {"label": "Long Strike", "value": format_value(selected_trade.get("long_strike"))},
                {"label": "Expiration", "value": format_value(selected_trade.get("expiration_date"))},
                {"label": "Premium", "value": selected_trade.get("net_credit"), "format": "currency", "accent": "#14b8a6"},
                {"label": "Width", "value": format_value(selected_trade.get("spread_width"))},
            ],
            columns=5,
        )

    sizing_row = _find_top_decision_sizing_row(
        selected_trade,
        position_sizing_summary=output.get("position_sizing_summary"),
    )
    capital_required = (
        sizing_row.get("estimated_max_risk_dollars")
        if sizing_row and sizing_row.get("estimated_max_risk_dollars") not in (None, "")
        else selected_trade.get("max_risk")
    )
    risk_panel = render_bordered_panel(
        "Risk & Reward",
        "Capital and downside/upside context for execution planning.",
    )
    with risk_panel:
        render_metric_strip(
            [
                {"label": "Max Risk", "value": selected_trade.get("max_risk"), "format": "currency", "accent": "#f97316"},
                {"label": "Max Profit", "value": selected_trade.get("max_profit"), "format": "currency", "accent": "#14b8a6"},
                {"label": "Breakeven", "value": _breakeven_from_trade(selected_trade), "format": "currency", "accent": "#64748b"},
                {"label": "Capital Required", "value": capital_required, "format": "currency", "accent": "#64748b"},
            ],
            columns=4,
        )

    why_panel = render_bordered_panel(
        "Why This Trade",
        "Signals and quality drivers supporting the rank.",
    )
    with why_panel:
        reasons = [
            selected_trade.get("status_reason"),
            selected_trade.get("decision_summary"),
            selected_trade.get("explanation"),
        ]
        rendered = [
            _compact_text_line(reason, max_chars=180)
            for reason in reasons
            if str(reason or "").strip()
        ]
        if not rendered:
            st.caption("No additional rank rationale is available for this trade.")
        else:
            for line in rendered[:3]:
                st.write(f"- {line}")

    stability_panel = render_bordered_panel(
        "Stability & History",
        "Historical appearance and stability cues from available run fields.",
    )
    with stability_panel:
        consistency_value = (
            (selected_trade.get("score_breakdown") or {}).get("consistency_score")
            or selected_trade.get("consistency_score")
            or selected_trade.get("stability_count")
        )
        recent_behavior = selected_trade.get("stability_level") or selected_trade.get("volatility_context")
        render_metric_strip(
            [
                {"label": "Times Seen", "value": selected_trade.get("stability_count", "n/a"), "accent": "#64748b"},
                {"label": "Stability Appearances", "value": consistency_value if consistency_value not in (None, "") else "n/a", "accent": "#14b8a6"},
                {"label": "Recent Behavior", "value": format_value(recent_behavior, default="n/a"), "accent": "#64748b"},
            ],
            columns=3,
        )

    action_panel = render_bordered_panel(
        "Actions",
        "Complete your review or navigate to comparison screens.",
    )
    with action_panel:
        actions = render_action_button_row(
            [
                {"label": "Mark as reviewed", "key": "trade_detail_mark_reviewed", "type": "primary"},
                {"label": "Compare with other trades", "key": "trade_detail_compare", "type": "secondary"},
                {"label": "Back to Qualified Trades", "key": "trade_detail_back", "type": "secondary"},
            ]
        )

        if actions.get("trade_detail_mark_reviewed") and row_key:
            reviewed_keys.add(row_key)
            st.session_state["reviewed_trade_keys"] = sorted(reviewed_keys)
            st.success("Trade marked as reviewed.")

        if row_key in reviewed_keys:
            render_semantic_chip("Reviewed", tone="bullish")

        if actions.get("trade_detail_compare"):
            st.session_state["active_view"] = "Qualified Trades"
            st.rerun()

        if actions.get("trade_detail_back"):
            st.session_state["active_view"] = "Qualified Trades"
            st.rerun()


def _normalize_detail_context_value(value):
    return str(value or "").strip().replace("_", " ").lower()


def _find_detail_context_row(rows, key_name, *candidates):
    normalized_candidates = {
        _normalize_detail_context_value(candidate)
        for candidate in candidates
        if candidate not in (None, "")
    }

    if not normalized_candidates:
        return None

    for row in rows or []:
        if _normalize_detail_context_value(row.get(key_name)) in normalized_candidates:
            return row

    return None


def _find_top_decision_sizing_row(spread, position_sizing_summary=None):
    if not isinstance(spread, dict):
        return None

    strategy_name = get_strategy_display_name(spread)
    return _find_detail_context_row(
        (position_sizing_summary or {}).get("trade_sizing", []),
        "strategy",
        strategy_name,
        spread.get("strategy_type"),
        spread.get("strategy_label"),
    )


def render_portfolio_impact_section(
    spread,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
):
    """Render compact portfolio impact notes for the current trade using existing run summaries."""
    if not isinstance(spread, dict) or not spread:
        return

    ticker = spread.get("ticker")
    direction = spread.get("directional_bias")
    qualified_summary = ((portfolio_exposure_summary or {}).get("qualified") or {})
    sizing_inputs = (position_sizing_summary or {}).get("inputs") or {}
    sizing_row = _find_top_decision_sizing_row(
        spread,
        position_sizing_summary=position_sizing_summary,
    )
    ticker_row = _find_detail_context_row(
        qualified_summary.get("counts_by_ticker", []),
        "ticker",
        ticker,
    )
    overlap_row = _find_detail_context_row(
        (exposure_overlap_summary or {}).get("repeated_ticker_direction_combinations", []),
        "ticker_direction",
        f"{ticker} | {direction}",
    )

    metric_items = []
    notes = []

    risk_budget = sizing_inputs.get("max_risk_dollars")
    if risk_budget not in (None, ""):
        metric_items.append(
            {"label": "Risk Budget", "value": risk_budget, "format": "currency", "accent": "#64748b"}
        )

    if sizing_row:
        estimated_risk = sizing_row.get("estimated_max_risk_dollars")
        fits_budget = sizing_row.get("fits_risk_budget")
        contracts = sizing_row.get("approx_contracts_within_budget")

        if estimated_risk not in (None, ""):
            metric_items.append(
                {"label": "Est Risk", "value": estimated_risk, "format": "currency", "accent": "#f97316"}
            )

        if contracts not in (None, ""):
            metric_items.append(
                {
                    "label": "Contracts",
                    "value": contracts,
                    "accent": "#14b8a6" if fits_budget is True else "#f59e0b",
                }
            )

        if estimated_risk not in (None, ""):
            if fits_budget is True:
                notes.append(
                    f"Estimated one-contract risk {format_currency(estimated_risk)} fits the current sample risk budget."
                )
            elif fits_budget is False:
                notes.append(
                    f"Estimated one-contract risk {format_currency(estimated_risk)} sits above the current sample risk budget."
                )

    if ticker_row and ticker_row.get("share_pct") not in (None, ""):
        share_pct = ticker_row.get("share_pct")
        metric_items.append(
            {"label": "Ticker Share", "value": f"{share_pct}%", "accent": "#64748b"}
        )
        if share_pct >= 30:
            notes.append(
                f"{ticker} represents {share_pct}% of the current qualified set, so concentration is worth monitoring."
            )

    if overlap_row:
        notes.append(
            f"{overlap_row.get('ticker_direction', 'Current direction')} appears {overlap_row.get('count', 0)} time(s) in the qualified set."
        )

    if not metric_items and not notes:
        return

    def _render_content():
        if metric_items:
            render_metric_strip(metric_items[:4], columns=min(4, len(metric_items)))

        if notes:
            for note in notes[:3]:
                st.write(f"- {note}")
        elif not metric_items:
            st.caption("No additional portfolio impact notes are available for this trade yet.")

    render_subsection_card(
        "Portfolio Impact",
        _render_content,
        subtitle="Sizing and concentration context from the current run.",
        accent="#64748b",
    )


def render_why_this_trade(primary_trade, detail_trade):
    """Render concise decision signals for the highlighted trade."""
    adjusted_score = get_trade_value(primary_trade, detail_trade, "adjusted_score", "n/a")
    pop = get_trade_value(primary_trade, detail_trade, "POP", "n/a")
    ror = get_trade_value(primary_trade, detail_trade, "ROR", "n/a")
    stability_level = get_trade_value(primary_trade, detail_trade, "stability_level", "n/a")
    stability_count = get_trade_value(primary_trade, detail_trade, "stability_count", 0)
    volatility_context = get_trade_value(primary_trade, detail_trade, "volatility_context", "n/a")
    status_reason = get_trade_value(
        primary_trade,
        detail_trade,
        "status_reason",
        "No status reason provided.",
    )
    decision_summary = get_trade_value(
        primary_trade,
        detail_trade,
        "decision_summary",
        "No decision summary available.",
    )
    price_context_warning = get_trade_value(
        primary_trade,
        detail_trade,
        "price_context_warning",
        False,
    )
    price_context_reason = get_trade_value(
        primary_trade,
        detail_trade,
        "price_context_reason",
        None,
    )

    strengths = [
        f"Adjusted score {adjusted_score}.",
        f"POP {pop} and ROR {ror}.",
        f"Stability {stability_level} ({stability_count}).",
    ]

    cautions = [
        f"Premium context: {str(volatility_context).replace('_', ' ')}.",
        status_reason,
        decision_summary,
    ]

    risks = [price_context_reason] if price_context_warning and price_context_reason else []

    with st.container(border=True):
        render_section_header(
            "Why This Trade",
            "Quick execution-prep context for the current top candidate.",
        )
        render_detail_signal_groups(strengths=strengths, cautions=cautions, risks=risks)


def render_top_decision_panel(
    spread,
    qualified_count,
    fallback_spread=None,
    portfolio_exposure_summary=None,
    position_sizing_summary=None,
    exposure_overlap_summary=None,
    title="Top Decision",
    subtitle="Execution-prep view for the best current candidate under the active rules.",
):
    """Render a structured execution-prep view for the selected trade."""
    render_section_header(title, subtitle)

    if not spread and not fallback_spread:
        render_warning_banner("No qualified trades were returned for this run.", level="info")
        render_empty_state(
            "No top decision available",
            "Try widening the DTE range or lowering the minimum score/stability thresholds.",
        )
        return

    primary_trade = spread or fallback_spread or {}
    detail_trade = fallback_spread or primary_trade
    opportunity_label = get_opportunity_label(primary_trade)
    strategy_name = get_strategy_display_name(
        detail_trade or primary_trade,
        default=get_trade_value(primary_trade, detail_trade, "strategy_type", "Trade"),
    )

    expiration = format_value(get_trade_value(primary_trade, detail_trade, "expiration_date", "n/a"))
    dte = format_value(get_trade_value(primary_trade, detail_trade, "DTE", "n/a"))
    premium_context = str(
        get_trade_value(primary_trade, detail_trade, "volatility_context", "n/a") or "n/a"
    ).replace("_", " ")
    underlying_price = get_trade_value(primary_trade, detail_trade, "underlying_price")
    score_value = get_trade_value(
        primary_trade,
        detail_trade,
        "adjusted_score",
        get_trade_value(primary_trade, detail_trade, "score", "n/a"),
    )

    sizing_row = _find_top_decision_sizing_row(
        detail_trade,
        position_sizing_summary=position_sizing_summary,
    )
    sizing_inputs = (position_sizing_summary or {}).get("inputs") or {}
    estimated_risk = (
        sizing_row.get("estimated_max_risk_dollars")
        if sizing_row else get_trade_value(primary_trade, detail_trade, "max_risk")
    )
    fits_budget = sizing_row.get("fits_risk_budget") if sizing_row else None
    risk_budget = sizing_inputs.get("max_risk_dollars")

    with st.container(border=True):
        title_col, chip_col = st.columns([4.5, 1], gap="small")
        with title_col:
            st.markdown(
                f"### {get_trade_value(primary_trade, detail_trade, 'ticker', 'N/A')} | {strategy_name}"
            )
            st.caption(
                f"{opportunity_label} • Exp {expiration} • DTE {dte} • Premium {premium_context}"
            )
        with chip_col:
            render_direction_chip(primary_trade)

        summary_text = (
            f"{qualified_count} qualified trade(s) identified in this run. "
            f"Current assessment under the active rules: {opportunity_label}."
        )

        if opportunity_label == "Strong opportunity":
            render_warning_banner(summary_text, level="success")
        elif opportunity_label == "Moderate opportunity":
            render_warning_banner(summary_text, level="info")
        else:
            render_warning_banner(summary_text, level="warning")

        render_metric_strip(
            [
                {"label": "POP", "value": get_trade_value(primary_trade, detail_trade, "POP"), "format": "percent", "accent": "#14b8a6", "emphasis": "high"},
                {"label": "ROR", "value": get_trade_value(primary_trade, detail_trade, "ROR"), "format": "percent", "accent": "#f59e0b", "emphasis": "medium"},
                {"label": "Adj Score", "value": score_value, "accent": "#64748b"},
                {"label": "Underlying", "value": underlying_price, "format": "currency", "accent": "#64748b"},
            ],
            columns=4,
        )

        render_risk_banner(
            estimated_risk=estimated_risk,
            max_loss=get_trade_value(primary_trade, detail_trade, "max_risk"),
            risk_budget=risk_budget,
            fits_budget=fits_budget,
            level="info",
        )

        price_context_warning = get_trade_value(
            primary_trade,
            detail_trade,
            "price_context_warning",
            False,
        )
        price_context_reason = get_trade_value(
            primary_trade,
            detail_trade,
            "price_context_reason",
            None,
        )
        if price_context_warning and price_context_reason:
            render_warning_banner(price_context_reason, level="warning")

        render_why_this_trade(primary_trade, detail_trade)

        left_col, right_col = st.columns([1.25, 0.95], gap="large")
        with left_col:
            render_spread_summary(detail_trade, title="Spread Summary")
            render_spread_legs_table(detail_trade, title="Spread Legs")

        with right_col:
            render_portfolio_impact_section(
                detail_trade,
                portfolio_exposure_summary=portfolio_exposure_summary,
                position_sizing_summary=position_sizing_summary,
                exposure_overlap_summary=exposure_overlap_summary,
            )

        render_json_expander(detail_trade, label="Raw trade data (optional)")


def render_system_signals(output):
    """Render compact system and scan-quality indicators from engine metadata."""
    st.subheader("System Signals")

    provider = output.get("provider") or "n/a"
    execution_time = output.get("execution_time_seconds")
    missing_tickers = output.get("missing_tickers") or []
    provider_errors = output.get("provider_errors") or []
    summary = output.get("summary", {})
    alerts = output.get("alerts") or []
    qualified = output.get("qualified") or []

    missing_count = len(missing_tickers)
    provider_error_count = len(provider_errors)
    qualified_count = summary.get("qualified_count", len(qualified))
    alerts_count = len(alerts)

    if provider_error_count > 0:
        health_message = "Provider issues detected. Treat this run as partially incomplete."
        health_type = "error"
    elif missing_count > 0:
        health_message = "Partial data coverage, interpret carefully."
        health_type = "warning"
    elif qualified_count > 0 or alerts_count > 0:
        health_message = "Healthy run with actionable candidates."
        health_type = "success"
    else:
        health_message = "Healthy run with no strong candidates."
        health_type = "info"

    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Provider", provider)
        col2.metric(
            "Execution Time",
            f"{execution_time:.2f}s" if isinstance(execution_time, (int, float)) else "n/a",
        )
        col3.metric("Missing Tickers", missing_count)

        col4, col5, col6 = st.columns(3)
        col4.metric("Provider Errors", provider_error_count)
        col5.metric("Qualified Trades", qualified_count)
        col6.metric("Alerts", alerts_count)

        if health_type == "error":
            st.error(health_message)
        elif health_type == "warning":
            st.warning(health_message)
        elif health_type == "success":
            st.success(health_message)
        else:
            st.info(health_message)


def render_portfolio_signals(output):
    """Render a compact, descriptive summary of current-run exposure and concentration."""
    st.subheader("Portfolio Signals")

    exposure = output.get("portfolio_exposure_summary") or {}
    qualified_summary = exposure.get("qualified") or {}
    metadata = exposure.get("metadata") or {}

    qualified_count = metadata.get("qualified_trade_count", 0)
    if qualified_count == 0:
        with st.container(border=True):
            st.info("No qualified trades are available yet, so portfolio concentration signals are limited for this run.")
        return

    top_ticker = (qualified_summary.get("top_ticker_concentration") or [None])[0] or {}
    top_strategy = (qualified_summary.get("counts_by_strategy") or [None])[0] or {}
    top_direction = (qualified_summary.get("directional_exposure") or [None])[0] or {}

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Qualified Trades", qualified_count)
        col2.metric(
            "Top Ticker",
            top_ticker.get("ticker", "n/a"),
            f"{top_ticker.get('share_pct', 0)}%" if top_ticker else None,
        )
        col3.metric(
            "Top Strategy",
            top_strategy.get("strategy", "n/a"),
            f"{top_strategy.get('count', 0)} trade(s)" if top_strategy else None,
        )
        col4.metric(
            "Directional Tilt",
            str(top_direction.get("directional_bias", "n/a")).replace("_", " ").title(),
            f"{top_direction.get('share_pct', 0)}%" if top_direction else None,
        )

        notes = exposure.get("notes") or []
        if notes:
            for note in notes[:2]:
                st.write(f"- {note}")
        else:
            st.write("- Current qualified candidates look relatively diversified across the scanned set.")


def render_portfolio_decision(output):
    """Render a compact portfolio-level interpretation using existing summary outputs."""
    st.subheader("Portfolio Decision")

    decision_summary = output.get("portfolio_decision_summary") or {}
    posture_label = decision_summary.get("posture_label")
    key_signals = decision_summary.get("key_portfolio_signals") or []
    interpretation = decision_summary.get("interpretation") or []
    cautions = decision_summary.get("cautions") or []

    if not posture_label and not key_signals and not interpretation:
        with st.container(border=True):
            st.info("Portfolio-level interpretation is limited for this run because there is not enough current portfolio context yet.")
        return

    with st.container(border=True):
        if posture_label:
            st.markdown(f"### {posture_label}")

        for message in interpretation[:2]:
            st.write(message)

        if key_signals:
            st.markdown("**Key Signals**")
            for signal in key_signals[:3]:
                st.write(f"- {signal}")

        if cautions:
            st.markdown("**Cautions**")
            for caution in cautions[:3]:
                st.write(f"- {caution}")


def _normalize_history_value(value):
    return str(value or "").strip().replace("_", " ").lower()


def _find_history_row(rows, key_name, *candidates):
    normalized_candidates = {
        _normalize_history_value(candidate)
        for candidate in candidates
        if candidate not in (None, "")
    }

    if not normalized_candidates:
        return None

    for row in rows or []:
        if _normalize_history_value(row.get(key_name)) in normalized_candidates:
            return row

    return None


def render_historical_signal_context(primary_trade, fallback_trade=None):
    """Render concise, non-predictive context from stored signal history."""
    st.subheader("Historical Signal Context")

    if not primary_trade and not fallback_trade:
        with st.container(border=True):
            st.info("Historical context becomes available once a current top decision is present.")
        return

    detail_trade = fallback_trade or primary_trade or {}
    ticker = get_trade_value(primary_trade, detail_trade, "ticker", "N/A")
    raw_strategy = (
        get_trade_value(primary_trade, detail_trade, "strategy_label")
        or get_trade_value(primary_trade, detail_trade, "strategy_type")
        or get_trade_value(primary_trade, detail_trade, "strategy_key")
        or "Trade"
    )
    strategy_name = get_strategy_display_name(detail_trade or raw_strategy, default="Trade")
    volatility_context = get_trade_value(primary_trade, detail_trade, "volatility_context")
    stability_level = get_trade_value(primary_trade, detail_trade, "stability_level")

    intelligence_summary = get_historical_intelligence_summary(limit=25)
    metadata = intelligence_summary.get("metadata", {})
    history_summary = intelligence_summary.get("signal_quality_summary", {})
    feature_summary = intelligence_summary.get("feature_summary", {})
    runs_analyzed = metadata.get("runs_analyzed", history_summary.get("runs_analyzed", 0))
    signals_analyzed = metadata.get(
        "signals_analyzed",
        history_summary.get("signals_analyzed", 0),
    )

    if runs_analyzed == 0 or signals_analyzed == 0:
        with st.container(border=True):
            st.info(
                "Stored scan history is still limited. Run a few more scans to build additional context."
            )
        return

    ticker_row = _find_history_row(
        history_summary.get("most_frequent_qualified_tickers", []),
        "ticker",
        ticker,
    )
    strategy_row = _find_history_row(
        history_summary.get("most_frequent_qualified_strategies", []),
        "strategy",
        strategy_name,
        raw_strategy,
    )
    ticker_score_row = _find_history_row(
        history_summary.get("average_adjusted_score_by_ticker", []),
        "ticker",
        ticker,
    )
    strategy_score_row = _find_history_row(
        history_summary.get("average_adjusted_score_by_strategy", []),
        "strategy",
        strategy_name,
        raw_strategy,
    )
    pattern_row = _find_history_row(
        history_summary.get("recurring_high_quality_patterns", []),
        "pattern",
        f"{ticker} | {strategy_name}",
        f"{ticker} | {raw_strategy}",
    )
    pair_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_ticker_strategy_pair", []),
        "pair",
        f"{ticker} | {strategy_name}",
        f"{ticker} | {raw_strategy}",
    )
    volatility_row = _find_history_row(
        feature_summary.get("counts_by_volatility_context", []),
        "volatility_context",
        volatility_context,
    )
    volatility_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_volatility_context", []),
        "volatility_context",
        volatility_context,
    )
    stability_row = _find_history_row(
        feature_summary.get("counts_by_stability_level", []),
        "stability_level",
        stability_level,
    )
    stability_score_row = _find_history_row(
        feature_summary.get("average_adjusted_score_by_stability_level", []),
        "stability_level",
        stability_level,
    )

    with st.container(border=True):
        st.caption(
            "Uses stored scan history for context only. It does not estimate future outcomes or guarantee signal quality."
        )

        similar_signal_average = None
        if pair_score_row:
            similar_signal_average = pair_score_row.get("average_adjusted_score")
        elif ticker_score_row:
            similar_signal_average = ticker_score_row.get("average_adjusted_score")
        elif strategy_score_row:
            similar_signal_average = strategy_score_row.get("average_adjusted_score")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Runs Analyzed", runs_analyzed)
        col2.metric(
            "Pair Recurrence",
            pattern_row.get("count", "Limited") if pattern_row else "Limited",
        )
        col3.metric(
            "Similar Hist. Avg",
            similar_signal_average if similar_signal_average is not None else "Limited",
        )
        col4.metric(
            "Signals Logged",
            signals_analyzed,
        )

        context_notes = []

        if pattern_row:
            context_notes.append(
                f"**{ticker} | {strategy_name}** has appeared **{pattern_row.get('count', 0)}** time(s) in stored high-quality history."
            )
        else:
            context_notes.append(
                f"Direct history for **{ticker} | {strategy_name}** is still limited, so the current run should remain the primary input."
            )

        if volatility_context and volatility_row:
            volatility_average = None
            if volatility_score_row:
                volatility_average = volatility_score_row.get("average_adjusted_score")

            message = (
                f"The current premium context (**{volatility_context.replace('_', ' ')}**) appears in **{volatility_row.get('count', 0)}** stored signal(s)"
            )
            if volatility_average is not None:
                message += f", with an average adjusted score of **{volatility_average}**"
            message += "."
            context_notes.append(message)

        if stability_level and stability_row:
            stability_average = None
            if stability_score_row:
                stability_average = stability_score_row.get("average_adjusted_score")

            message = (
                f"Signals labeled **{stability_level}** appear **{stability_row.get('count', 0)}** time(s) in stored history"
            )
            if stability_average is not None:
                message += f", with an average adjusted score of **{stability_average}**"
            message += "."
            context_notes.append(message)

        for note in context_notes[:3]:
            st.write(f"- {note}")


def render_trade_lifecycle():
    """Show the user how to move through the existing app workflow."""
    st.subheader("Trade Lifecycle")

    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("### 1. Scan")
            st.caption("Use **Alerts** to review fresh opportunities returned by the current run.")

        with col2:
            st.markdown("### 2. Select")
            st.caption("Use **Qualified Trades** to focus on the strongest current candidates.")

        with col3:
            st.markdown("### 3. Track")
            st.caption("Use **History** to understand recurring patterns and stability over time.")

        with col4:
            st.markdown("### 4. Outcome")
            st.caption("Use **Daily Summary** for the run-level interpretation and takeaways.")


def render_system_boundaries():
    """Communicate the app's analytical role and practical limits."""
    st.subheader("System Boundaries")

    with st.container(border=True):
        st.caption(
            "This app evaluates options opportunities using the current rules and available market data. "
            "Its outputs are intended for decision support, not automatic execution. Data/provider coverage can affect results, "
            "so final trade decisions should always use your own judgment."
        )


def render_trade_card(title, spread):
    if not spread:
        st.info(f"No {title.lower()} available.")
        return

    with st.container(border=True):
        st.subheader(title)
        st.markdown(
            f"**{spread.get('ticker')}** | {spread.get('strategy_type')} | "
            f"Premium: {spread.get('volatility_context')}"
        )
        render_metric_row(spread)

        st.markdown(
            f"**Strikes:** {spread.get('short_strike')} / {spread.get('long_strike')}"
        )
        render_stability_block(spread)
        render_decision_summary(spread)


def render_trend_insights():
    runs = load_all_history_runs(include_fallback_dirs=True)

    if not runs:
        render_empty_state(
            "No history yet",
            "No history yet — run your first scan to start tracking performance",
        )
        return

    intelligence = get_historical_intelligence_summary(limit=5)
    signal_quality_summary = intelligence.get("signal_quality_summary", {})
    feature_summary = intelligence.get("feature_summary", {})

    qualified_counts = [run.get("qualified_count", 0) for run in runs]
    alert_counts = [run.get("alerts_count", 0) for run in runs]
    average_qualified = round(sum(qualified_counts) / len(qualified_counts), 1) if qualified_counts else 0

    all_scores = []
    for run in runs:
        for spread in run.get("qualified", []) or []:
            score_value = spread.get("adjusted_score", spread.get("score"))
            if isinstance(score_value, (int, float)):
                all_scores.append(float(score_value))
    average_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else "n/a"

    trend_indicator = "Stable"
    if len(qualified_counts) >= 2:
        if qualified_counts[0] > qualified_counts[-1]:
            trend_indicator = "Improving"
        elif qualified_counts[0] < qualified_counts[-1]:
            trend_indicator = "Cooling"

    summary_panel = render_bordered_panel(
        "History Summary",
        "Stored run history used as a confidence and stability layer.",
    )
    with summary_panel:
        cols = st.columns(4, gap="small")
        render_kpi_metric_card(cols[0], "Total Runs", len(runs), accent="info")
        render_kpi_metric_card(cols[1], "Avg Qualified", average_qualified, accent="bullish")
        render_kpi_metric_card(cols[2], "Avg Score", average_score, accent="warning")
        render_kpi_metric_card(cols[3], "Trend", trend_indicator, accent="bearish")

    recent_panel = render_bordered_panel(
        "Recent Runs",
        "Latest stored runs with compact operational details.",
    )
    with recent_panel:
        recent_rows = []
        for run in reversed(runs[-6:]):
            top_trade = run.get("top_overall") or {}
            top_label = "—"
            if top_trade:
                top_label = f"{top_trade.get('ticker', 'N/A')} | {get_strategy_display_name(top_trade, default='Trade')}"

            timestamp = str(run.get("timestamp", ""))
            timestamp_display = timestamp.replace("T", " ")[:19] if timestamp else "—"
            execution_time = run.get("execution_time")
            execution_display = f"{execution_time:.2f}s" if isinstance(execution_time, (int, float)) else "—"

            recent_rows.append(
                {
                    "Timestamp": timestamp_display,
                    "Profile": run.get("profile", "—"),
                    "Qualified": run.get("qualified_count", 0),
                    "Alerts": run.get("alerts_count", 0),
                    "Top Trade": top_label,
                    "Execution": execution_display,
                }
            )

        st.table(recent_rows)

    stability_panel = render_bordered_panel(
        "Stability Insights",
        "Repeated appearances and consistent names across stored runs.",
    )
    with stability_panel:
        recurring_patterns = signal_quality_summary.get("recurring_high_quality_patterns", [])
        frequent_tickers = signal_quality_summary.get("most_frequent_qualified_tickers", [])
        top_pairs = feature_summary.get("average_adjusted_score_by_ticker_strategy_pair", [])

        col1, col2, col3 = st.columns(3, gap="small")
        with col1:
            st.markdown("**Repeated Trades**")
            if recurring_patterns:
                for row in recurring_patterns[:4]:
                    st.write(f"- {row.get('pattern', 'n/a')} — {row.get('count', 0)} runs")
            else:
                st.caption("No repeated trades yet.")

        with col2:
            st.markdown("**Consistent Tickers**")
            if frequent_tickers:
                for row in frequent_tickers[:4]:
                    st.write(f"- {row.get('ticker', 'n/a')} — {row.get('count', 0)} times")
            else:
                st.caption("No consistent tickers yet.")

        with col3:
            st.markdown("**Frequent Top Names**")
            if top_pairs:
                for row in top_pairs[:4]:
                    st.write(
                        f"- {row.get('pair', 'n/a')} — avg score {row.get('average_adjusted_score', 'n/a')}"
                    )
            else:
                st.caption("No repeated top-ranked names yet.")

    if len(runs) >= 2:
        latest_run = runs[-1]
        previous_run = runs[-2]
        qualified_delta = latest_run.get("qualified_count", 0) - previous_run.get("qualified_count", 0)
        alerts_delta = latest_run.get("alerts_count", 0) - previous_run.get("alerts_count", 0)

        latest_scores = [
            spread.get("adjusted_score", spread.get("score"))
            for spread in latest_run.get("qualified", []) or []
            if isinstance(spread.get("adjusted_score", spread.get("score")), (int, float))
        ]
        previous_scores = [
            spread.get("adjusted_score", spread.get("score"))
            for spread in previous_run.get("qualified", []) or []
            if isinstance(spread.get("adjusted_score", spread.get("score")), (int, float))
        ]
        latest_avg = round(sum(latest_scores) / len(latest_scores), 1) if latest_scores else 0
        previous_avg = round(sum(previous_scores) / len(previous_scores), 1) if previous_scores else 0
        score_delta = latest_avg - previous_avg

        trend_panel = render_bordered_panel(
            "Trend Signals",
            "Simple run-over-run changes from the most recent scans.",
        )
        with trend_panel:
            cols = st.columns(3, gap="small")
            render_kpi_metric_card(cols[0], "Qualified Change", f"{qualified_delta:+d}", accent="bullish")
            render_kpi_metric_card(cols[1], "Score Change", f"{score_delta:+.1f}", accent="warning")
            render_kpi_metric_card(cols[2], "Alert Change", f"{alerts_delta:+d}", accent="info")

def render_daily_summary(output):
    summary = output.get("summary", {})
    alerts = output.get("alerts", [])
    qualified = output.get("qualified", [])
    top_overall = summary.get("top_overall") or (qualified[0] if qualified else None)
    dte_range = output.get("dte_range", {})
    profile = output.get("profile")
    ticker_group = output.get("ticker_group")
    execution_time = output.get("execution_time_seconds")
    provider_errors = output.get("provider_errors", []) or []
    missing_tickers = output.get("missing_tickers", []) or []
    qualified_count = summary.get("qualified_count", len(qualified))
    alerts_count = len(alerts)
    near_miss_count = summary.get("near_miss_count", 0)

    stable_alerts = [s for s in alerts if s.get("stability_level") == "stable"]
    emerging_alerts = [s for s in alerts if s.get("stability_level") == "emerging"]
    new_alerts = [s for s in alerts if s.get("stability_level") == "new"]
    score_values = [value for value in (_score_from_trade(spread) for spread in qualified) if value is not None]
    average_score = round(sum(score_values) / len(score_values), 1) if score_values else None

    most_stable_alert = None
    if alerts:
        most_stable_alert = max(
            alerts,
            key=lambda s: s.get("stability_count", 0)
        )

    if not summary and not alerts and not qualified:
        render_empty_state(
            "No summary yet",
            "Run a scan first to generate a daily summary.",
        )
        return

    summary_notice = None
    notice_type = None
    if provider_errors:
        summary_notice = (
            "This summary reflects a run with provider issues, so missing opportunities may be data-related."
        )
        notice_type = "warning"
    elif missing_tickers:
        summary_notice = (
            f"This summary reflects partial coverage: {len(missing_tickers)} ticker(s) were unavailable during the scan."
        )
        notice_type = "info"
    elif qualified_count == 0 and alerts_count == 0:
        summary_notice = (
            "This was a healthy run, but no strong opportunities cleared the current thresholds."
        )
        notice_type = "info"

    headline_panel = render_bordered_panel(
        "Executive Brief",
        "Fast plain-language recap of the latest run.",
    )
    with headline_panel:
        cols = st.columns(3, gap="small")
        render_kpi_metric_card(cols[0], "Qualified Trades", qualified_count, accent="bullish")
        render_kpi_metric_card(cols[1], "Alerts", alerts_count, accent="warning")
        top_label = (
            f"{top_overall.get('ticker', 'N/A')} | {get_strategy_display_name(top_overall, default='Trade')}"
            if isinstance(top_overall, dict) and top_overall
            else "No top opportunity"
        )
        render_kpi_metric_card(cols[2], "Top Opportunity", top_label, accent="info", emphasis="compact")

        overall_statement = summary_notice
        if not overall_statement:
            if qualified_count > 0:
                overall_statement = f"{qualified_count} trade(s) qualified with {alerts_count} alert(s) worth review in the current run."
            elif alerts_count > 0:
                overall_statement = f"No fully qualified trades, but {alerts_count} alert(s) still deserve attention."
            else:
                overall_statement = "Nothing stood out strongly in this run under the current settings."
        st.write(overall_statement)

        context_bits = [
            f"Profile: {profile}",
            f"Ticker group: {ticker_group}",
            f"Window: {dte_range.get('dte_min', '-')}-{dte_range.get('dte_max', '-')} DTE",
        ]
        if isinstance(execution_time, (int, float)):
            context_bits.append(f"Run time: {execution_time:.2f}s")
        st.caption(" • ".join(context_bits))

    rich_count = sum(
        1 for spread in alerts if spread.get("volatility_context") == "rich_premium"
    )
    balanced_count = sum(
        1 for spread in alerts if spread.get("volatility_context") == "balanced_premium"
    )

    if rich_count > 0:
        takeaway = (
            f"The strongest current opportunities include {rich_count} rich-premium "
            f"alert(s), suggesting unusually attractive pricing in this run."
        )
    elif balanced_count > 0:
        takeaway = (
            "The strongest current opportunities are balanced-premium setups with "
            "solid POP and manageable friction. No rich-premium setups were identified "
            "in this run."
        )
    else:
        takeaway = (
            "No high-priority opportunities were identified in this run. The market may "
            "not be offering attractive premium conditions right now."
        )

    takeaways_panel = render_bordered_panel(
        "Key Takeaways",
        "Main signals worth carrying into the next decision.",
    )
    with takeaways_panel:
        takeaway_lines = []
        if top_overall:
            takeaway_lines.append(
                f"Strongest ticker: {top_overall.get('ticker', 'N/A')} in {get_strategy_display_name(top_overall, default='Trade')}."
            )
        if average_score is not None:
            takeaway_lines.append(f"Average qualified score landed at {average_score} across this run.")
        if stable_alerts:
            takeaway_lines.append(f"{len(stable_alerts)} alert(s) showed stable behavior, suggesting better follow-through quality.")
        elif emerging_alerts or new_alerts:
            takeaway_lines.append("Most alert activity came from newer or emerging setups rather than stable repeats.")
        if most_stable_alert:
            takeaway_lines.append(
                f"Key alert insight: {most_stable_alert.get('ticker', 'N/A')} appeared as the most stable alert with {most_stable_alert.get('stability_count', 0)} sightings."
            )
        if near_miss_count:
            takeaway_lines.append(f"{near_miss_count} near-miss candidate(s) came close but did not fully qualify.")
        takeaway_lines.append(takeaway)

        for line in takeaway_lines[:4]:
            st.write(f"- {line}")

    top_panel = render_bordered_panel(
        "Top Opportunities",
        "Best 1-3 ideas from the current run.",
    )
    with top_panel:
        top_candidates = qualified[:3] if qualified else ([top_overall] if top_overall else [])
        if not top_candidates:
            st.caption("No top opportunities are available in this run.")
        for idx, spread in enumerate(top_candidates, start=1):
            if not isinstance(spread, dict):
                continue
            candidate_panel = st.container(border=True)
            with candidate_panel:
                st.markdown(f"### #{idx} {spread.get('ticker', 'N/A')} | {get_strategy_display_name(spread, default='Trade')}")
                render_metric_strip(
                    [
                        {"label": "Score", "value": _score_from_trade(spread), "accent": "#64748b"},
                        {"label": "POP", "value": spread.get("POP"), "format": "percent", "accent": "#14b8a6"},
                        {"label": "ROR", "value": spread.get("ROR"), "format": "percent", "accent": "#f59e0b"},
                    ],
                    columns=3,
                )
                rationale = spread.get("decision_summary") or spread.get("status_reason") or "No short rationale provided."
                st.caption(_compact_text_line(rationale, max_chars=180))

    previous_snapshot = st.session_state.get("previous_scan_snapshot")
    if previous_snapshot:
        qualified_delta = qualified_count - previous_snapshot.get("qualified_count", 0)
        alerts_delta = alerts_count - previous_snapshot.get("alerts_count", 0)
        previous_avg_score = previous_snapshot.get("average_score")
        score_delta = None
        if average_score is not None and previous_avg_score is not None:
            score_delta = average_score - previous_avg_score

        recurring_trade = False
        current_top_key = get_trade_row_key(top_overall) if isinstance(top_overall, dict) else None
        if current_top_key and current_top_key == previous_snapshot.get("top_trade_key"):
            recurring_trade = True

        change_panel = render_bordered_panel(
            "What Changed",
            "Comparison with the previous run when available.",
        )
        with change_panel:
            change_lines = [
                f"Qualified trades: {qualified_delta:+d} versus the previous run.",
                f"Alerts: {alerts_delta:+d} versus the previous run.",
            ]
            if score_delta is not None:
                change_lines.append(f"Average score moved {score_delta:+.1f} points.")
            if recurring_trade:
                change_lines.append("The same top opportunity carried over from the previous run.")
            elif previous_snapshot.get("top_trade_label"):
                change_lines.append(
                    f"Top opportunity shifted from {previous_snapshot.get('top_trade_label')} to {top_label}."
                )

            for line in change_lines[:4]:
                st.write(f"- {line}")

    action_panel = render_bordered_panel(
        "Next Actions",
        "Move directly to the screen that best matches your next step.",
    )
    with action_panel:
        actions = render_action_button_row(
            [
                {"label": "View Qualified Trades", "key": "daily_summary_to_qualified", "type": "secondary"},
                {"label": "View Alerts", "key": "daily_summary_to_alerts", "type": "secondary"},
                {"label": "Run New Scan", "key": "daily_summary_run_scan", "type": "primary"},
            ]
        )

        if actions.get("daily_summary_to_qualified"):
            st.session_state["active_view"] = "Qualified Trades"
            st.rerun()
        if actions.get("daily_summary_to_alerts"):
            st.session_state["active_view"] = "Alerts"
            st.rerun()
        if actions.get("daily_summary_run_scan"):
            st.info("Use the sidebar Run button to launch a new scan with your current settings.")


if run_button:
    st.session_state["previous_scan_snapshot"] = _build_scan_snapshot(
        st.session_state.get("last_scan_output")
    )
    with st.spinner("Running scan..."):
        output = run_scan(
            profile,
            ticker_group,
            dte_min,
            dte_max,
            min_score,
            min_consistency,
            selected_strategy_keys,
        )  

    st.session_state["last_scan_output"] = output

    latest_summary = output.get("summary", {})
    latest_qualified = output.get("qualified", [])
    latest_top_overall = latest_summary.get("top_overall") or (latest_qualified[0] if latest_qualified else None)
    st.session_state["selected_trade_key"] = get_trade_row_key(latest_top_overall) if latest_top_overall else None
    st.session_state["active_view"] = "Overview"
    st.session_state[EXPANDED_TRADE_STATE_KEY] = None

output = st.session_state.get("last_scan_output")

if output:
    st.subheader("Execution Status")

    summary = output.get("summary", {})
    alerts = output.get("alerts", [])
    qualified = output.get("qualified", [])
    top_overall = summary.get("top_overall") or (qualified[0] if qualified else None)
    selected_trade = find_selected_trade(qualified, top_overall)

    if run_button:
        st.success("Scan completed successfully.")
    else:
        st.caption("Showing the most recent scan results. Use **Run Scan** to refresh the board.")

    active_view = render_main_view_selector()

    if active_view == "Overview":
        render_page_header(
            "Overview",
            "Headline view of current scan quality, portfolio context, and top candidate.",
            "Start here, then drill into trade-level views when needed.",
        )

        render_overview_snapshot(
            output,
            summary,
            qualified,
            alerts,
            top_overall,
        )

        with st.expander("Run Metadata", expanded=True):
            col1, col2, col3 = st.columns(3)
            col1.metric("Execution Time", output.get("execution_time_seconds"))
            col2.metric("Profile", output.get("profile"))
            col3.metric("Ticker Group", output.get("ticker_group"))

            col4, col5, col6 = st.columns(3)
            dte_range = output.get("dte_range", {})
            alert_thresholds = output.get("alert_thresholds", {})
            scoring_weights = output.get("scoring_weights", {})

            col4.metric(
                "DTE Range",
                f"{dte_range.get('dte_min', '-')}-{dte_range.get('dte_max', '-')}"
            )
            col5.metric("Min Score", alert_thresholds.get("min_score"))
            col6.metric("POP Weight", scoring_weights.get("pop_weight"))

    elif active_view == "Portfolio":
        render_portfolio_tab(output)

    elif active_view == "Alerts":
        render_page_header(
            "Alerts",
            "Prioritized signal center for the current run.",
            "Review urgent alerts first, then compare them against the full qualified board.",
        )
        render_alerts(
            alerts,
            provider_errors=output.get("provider_errors"),
            missing_tickers=output.get("missing_tickers"),
            qualified_count=summary.get("qualified_count", len(qualified)),
            on_review_trade=set_selected_trade_for_compare,
            on_open_detail=set_selected_trade_for_detail,
            on_compare=set_selected_trade_for_compare,
        )

    elif active_view == "Qualified Trades":
        st.caption("Use **Expand** for quick review and **Details** to open full trade context.")
        render_qualified_trades(
            qualified,
            provider_errors=output.get("provider_errors"),
            missing_tickers=output.get("missing_tickers"),
            portfolio_exposure_summary=output.get("portfolio_exposure_summary"),
            position_sizing_summary=output.get("position_sizing_summary"),
            exposure_overlap_summary=output.get("exposure_overlap_summary"),
            on_detail_select=set_selected_trade_for_detail,
            selected_detail_key=get_trade_row_key(selected_trade),
        )

    elif active_view == "Trade Detail":
        render_page_header(
            "Trade Detail",
            "Execution-prep view for the currently selected candidate.",
            "Use this screen to validate risk, structure, and supporting signals.",
        )
        render_trade_detail_execution_view(
            selected_trade,
            summary,
            qualified,
            output,
        )

    elif active_view == "History":
        render_page_header(
            "History",
            "Historical context from prior runs to support current decisions.",
            "Use recurring patterns as context only, not prediction.",
        )
        render_trend_insights()

    elif active_view == "Daily Summary":
        render_page_header(
            "Daily Summary",
            "Run-level recap of quality, coverage, and key takeaways.",
            "Use this as a quick end-of-run review.",
        )
        render_daily_summary(output)

    elif active_view == "Raw Output":
        st.json(output)
else:
    with st.container(border=True):
        st.markdown("### Start Here")
        st.write(
            "Choose a profile, ticker group, and strategy set in the sidebar, then click **Run Scan** to generate the current decision view."
        )
        st.caption(
            "For first-time walkthroughs, begin in **Overview**, then move to **Qualified Trades** and **History** for deeper review."
        )