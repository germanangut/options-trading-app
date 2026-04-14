"""Alerts UI rendering module."""

import streamlit as st
from ui.components import (
    render_action_button_row,
    render_bordered_panel,
    get_strategy_display_name,
    render_direction_chip,
    render_empty_state,
    render_json_expander,
    render_kpi_metric_card,
    render_metric_triplet,
    render_semantic_chip,
    render_signal_list,
    render_stability_block,
    render_warning_banner,
)


def _display_text(value, default="—"):
    text = str(value or "").strip()
    if not text:
        return default
    return text.replace("_", " ")


def _score_value(alert):
    score = alert.get("adjusted_score")
    if score in (None, ""):
        score = alert.get("score")
    return score


def _severity_from_alert(alert):
    stability_level = _display_text(alert.get("stability_level"), default="").lower()
    label_text = _display_text(alert.get("label"), default="").lower()

    if any(token in label_text for token in ("high", "strong", "top")) or stability_level == "stable":
        return ("high", "High")
    if stability_level == "emerging":
        return ("medium", "Medium")
    return ("low", "Info")


def _severity_rank(alert):
    severity_key, _ = _severity_from_alert(alert)
    return {"high": 0, "medium": 1, "low": 2}.get(severity_key, 2)


def _severity_tone(severity_key):
    return {
        "high": "bearish",
        "medium": "warning",
        "low": "info",
    }.get(severity_key, "info")


def _strategy_mix_text(alerts):
    counts = {}
    for alert in alerts:
        strategy_name = get_strategy_display_name(alert)
        counts[strategy_name] = counts.get(strategy_name, 0) + 1

    if not counts:
        return None

    return " • ".join(f"{name}: {count}" for name, count in counts.items())


def _coverage_message(provider_errors, missing_tickers):
    parts = []
    level = "info"

    if provider_errors:
        parts.append("Some provider issues were detected during this run, so alert coverage may be incomplete.")
        level = "warning"

    missing_count = len(missing_tickers or [])
    if missing_count > 0:
        parts.append(f"{missing_count} ticker(s) were unavailable during the scan, so this alert list may be partial.")

    return (" ".join(parts).strip(), level) if parts else (None, level)


def _render_alert_row(alert, rank, on_review_trade=None, on_open_detail=None, on_compare=None):
    strategy_name = get_strategy_display_name(alert)
    ticker = alert.get("ticker") or "N/A"
    expiration = _display_text(alert.get("expiration_date"))
    dte = _display_text(alert.get("DTE"))
    premium_context = _display_text(alert.get("volatility_context"))
    score = _score_value(alert)
    severity_key, severity_label = _severity_from_alert(alert)
    alert_label = _display_text(alert.get("label") or alert.get("stability_level"), default="Signal")
    why_it_matters = (
        alert.get("decision_summary")
        or alert.get("status_reason")
        or alert.get("explanation")
        or "No additional explanation is available for this signal yet."
    )

    with st.container(border=True):
        title_col, chip_col = st.columns([4.5, 1.1], gap="small")
        with title_col:
            st.markdown(f"### #{rank} {ticker} | {strategy_name}")
            st.caption(f"{alert_label} • Exp {expiration} • DTE {dte} • Premium {premium_context}")

        with chip_col:
            render_semantic_chip(severity_label, tone=_severity_tone(severity_key))
            render_direction_chip(alert)

        render_metric_triplet(
            alert.get("POP"),
            alert.get("ROR"),
            score,
            score_delta=alert_label,
        )

        st.caption(why_it_matters)

        actions = render_action_button_row(
            [
                {"label": "Review trade", "key": f"alert_review_{rank}", "type": "primary"},
                {"label": "Open detail", "key": f"alert_detail_{rank}", "type": "secondary"},
                {"label": "Compare", "key": f"alert_compare_{rank}", "type": "secondary"},
            ]
        )

        if actions.get(f"alert_review_{rank}") and callable(on_review_trade):
            on_review_trade(alert)
            st.rerun()

        if actions.get(f"alert_detail_{rank}") and callable(on_open_detail):
            on_open_detail(alert)
            st.rerun()

        if actions.get(f"alert_compare_{rank}") and callable(on_compare):
            on_compare(alert)
            st.rerun()

        with st.expander("Quick review", expanded=False):
            render_stability_block(alert)

            signals = [
                alert.get("status_reason"),
                alert.get("explanation"),
            ]
            if any(signal for signal in signals):
                render_signal_list(signals)

        render_json_expander(alert, label="Raw alert data (optional)")


def render_alerts(
    alerts,
    provider_errors=None,
    missing_tickers=None,
    qualified_count=0,
    on_review_trade=None,
    on_open_detail=None,
    on_compare=None,
):
    """Render the alerts list using the shared compact visual system."""
    provider_errors = provider_errors or []
    missing_tickers = missing_tickers or []
    missing_count = len(missing_tickers)

    if not alerts:
        if provider_errors:
            render_warning_banner(
                "No alerts were produced because provider issues affected the run. Review the Overview tab before treating this as a weak market signal.",
                level="warning",
            )
        elif missing_count > 0:
            render_warning_banner(
                f"No alerts were produced and {missing_count} ticker(s) were unavailable, so this run may be incomplete.",
                level="warning",
            )
        elif qualified_count > 0:
            render_warning_banner(
                "No high-priority alerts fired in this run, but there are still qualified trades worth reviewing.",
                level="info",
            )
        else:
            render_warning_banner(
                "No alerts this run. That usually means nothing cleared the strongest opportunity thresholds under the current settings.",
                level="info",
            )

        render_empty_state("Nothing needs attention", "No active alerts right now. Review Qualified Trades for broader candidate coverage if needed.")
        return

    prioritized_alerts = [
        alert
        for _, alert in sorted(
            enumerate(alerts),
            key=lambda item: (_severity_rank(item[1]), item[0]),
        )
    ]

    high_count = sum(1 for alert in prioritized_alerts if _severity_from_alert(alert)[0] == "high")
    medium_low_count = len(prioritized_alerts) - high_count
    headline_alert = prioritized_alerts[0] if prioritized_alerts else None

    summary_panel = render_bordered_panel(
        "Signal Center",
        "Prioritized alerts from the current run.",
    )
    with summary_panel:
        cols = st.columns(3, gap="small")
        render_kpi_metric_card(cols[0], "Total Alerts", len(prioritized_alerts), accent="warning")
        render_kpi_metric_card(cols[1], "High Priority", high_count, accent="bearish")
        render_kpi_metric_card(cols[2], "Med / Lower", medium_low_count, accent="info")

        if headline_alert:
            headline_strategy = get_strategy_display_name(headline_alert)
            st.caption(
                f"Top alert: {headline_alert.get('ticker', 'N/A')} | {headline_strategy}"
            )

    strategy_mix = _strategy_mix_text(alerts)
    if strategy_mix:
        st.caption(f"Strategy mix: {strategy_mix}")

    coverage_message, coverage_level = _coverage_message(provider_errors, missing_tickers)
    if coverage_message:
        render_warning_banner(coverage_message, level=coverage_level)

    for i, alert in enumerate(prioritized_alerts, start=1):
        _render_alert_row(
            alert,
            i,
            on_review_trade=on_review_trade,
            on_open_detail=on_open_detail,
            on_compare=on_compare,
        )