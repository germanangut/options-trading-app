"""Backend-owned shaping helpers for frontend-safe screen payloads."""

from __future__ import annotations

from typing import Any

from history import get_historical_intelligence_summary, load_all_history_runs


def _direction_label(direction: str | None) -> str | None:
    normalized = str(direction or "").strip().lower()
    if not normalized:
        return None

    if normalized == "bullish":
        return "Bullish"
    if normalized == "bearish":
        return "Bearish"
    return normalized.replace("_", " ").title()


def _first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _breakeven_value(trade: dict[str, Any]) -> float | int | None:
    for key in (
        "breakeven",
        "break_even",
        "breakeven_price",
        "break_even_price",
        "breakeven_short",
    ):
        value = trade.get(key)
        if value not in (None, ""):
            return value
    return None


def _build_pair_label(trade: dict[str, Any]) -> str | None:
    ticker = trade.get("ticker")
    strategy = trade.get("strategy_label") or trade.get("strategy_type") or trade.get("strategy_key")
    if not ticker or not strategy:
        return None
    return f"{ticker} | {strategy}"


def _find_recent_trade_history_context(
    trade: dict[str, Any],
    *,
    user_id: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    pair_label = _build_pair_label(trade)
    recent_runs = load_all_history_runs(include_fallback_dirs=True, user_id=user_id)[:limit]

    if not recent_runs or not pair_label:
        return {
            "has_history": False,
            "runs_analyzed": len(recent_runs),
            "recent_appearance_count": 0,
            "ticker_strategy_pair": pair_label,
            "appeared_recently": False,
            "latest_seen_at": None,
            "recent_continuity": "Historical context is limited for this trade.",
            "stability_note": None,
            "notes": [],
        }

    appearances = []
    for run in recent_runs:
        for candidate in run.get("qualified", []) or []:
            if _build_pair_label(candidate) == pair_label:
                appearances.append(run)
                break

    recent_appearance_count = len(appearances)
    latest_seen_at = appearances[0].get("timestamp") if appearances else None
    runs_analyzed = len(recent_runs)
    notes = []

    if recent_appearance_count > 0:
        notes.append(
            f"{pair_label} appeared in {recent_appearance_count} of the last {runs_analyzed} stored run(s)."
        )
    else:
        notes.append(
            f"{pair_label} does not appear in the last {runs_analyzed} stored run(s)."
        )

    stability_level = trade.get("stability_level")
    stability_count = trade.get("stability_count")
    stability_note = None
    if stability_level or stability_count not in (None, ""):
        stability_note = (
            f"Current signal is labeled {str(stability_level or 'unspecified').replace('_', ' ')}"
            f" with stability count {stability_count if stability_count not in (None, '') else 'n/a'}."
        )

    if recent_appearance_count >= 3:
        recent_continuity = "This ticker/strategy combination has shown recent continuity across stored scans."
    elif recent_appearance_count >= 1:
        recent_continuity = "This ticker/strategy combination has appeared recently, but continuity is still limited."
    else:
        recent_continuity = "No recent continuity was found for this ticker/strategy combination in stored scans."

    return {
        "has_history": True,
        "runs_analyzed": runs_analyzed,
        "recent_appearance_count": recent_appearance_count,
        "ticker_strategy_pair": pair_label,
        "appeared_recently": recent_appearance_count > 0,
        "latest_seen_at": latest_seen_at,
        "recent_continuity": recent_continuity,
        "stability_note": stability_note,
        "notes": notes,
    }


def _find_portfolio_fit_summary(trade: dict[str, Any], scan_result: dict[str, Any]) -> dict[str, Any] | None:
    position_sizing = ((scan_result.get("portfolio_summary") or {}).get("position_sizing") or {})
    trade_sizing_rows = position_sizing.get("trade_sizing") or []
    strategy_candidates = {
        value
        for value in (
            trade.get("strategy_label"),
            trade.get("strategy_type"),
            trade.get("strategy_key"),
        )
        if value not in (None, "")
    }

    matching_row = None
    for row in trade_sizing_rows:
        if row.get("ticker") != trade.get("ticker"):
            continue
        if strategy_candidates and row.get("strategy") not in strategy_candidates:
            continue
        matching_row = row
        break

    if not matching_row and not ((scan_result.get("portfolio_summary") or {}).get("decision") or {}).get("posture_label"):
        return None

    fits_budget = matching_row.get("fits_risk_budget") if matching_row else None
    estimated_risk = matching_row.get("estimated_max_risk_dollars") if matching_row else None
    contracts = matching_row.get("approx_contracts_within_budget") if matching_row else None
    note = matching_row.get("sizing_note") if matching_row else None
    if note in (None, "") and estimated_risk not in (None, ""):
        if fits_budget is True:
            note = "Estimated risk fits the current sample risk budget."
        elif fits_budget is False:
            note = "Estimated risk sits above the current sample risk budget."
        else:
            note = "Estimated risk is available, but budget fit is not explicit in the current row."

    return {
        "posture_label": ((scan_result.get("portfolio_summary") or {}).get("decision") or {}).get("posture_label"),
        "estimated_max_risk_dollars": estimated_risk,
        "fits_risk_budget": fits_budget,
        "approx_contracts_within_budget": contracts,
        "note": note,
    }


def _build_trade_warnings(trade: dict[str, Any], scan_result: dict[str, Any]) -> list[str]:
    warnings = []
    if trade.get("price_context_warning") and trade.get("price_context_reason"):
        warnings.append(str(trade.get("price_context_reason")))

    diagnostics = scan_result.get("diagnostics") or {}
    if diagnostics.get("provider_errors"):
        warnings.append("Provider errors were reported for this scan.")
    if diagnostics.get("missing_tickers"):
        warnings.append(
            f"Missing tickers: {', '.join(diagnostics.get('missing_tickers', []))}"
        )
    return warnings


def _build_scan_trust_snapshot(scan_result: dict[str, Any]) -> dict[str, Any]:
    diagnostics = scan_result.get("diagnostics") or {}
    provider_errors = diagnostics.get("provider_errors") or []
    missing_tickers = diagnostics.get("missing_tickers") or []
    summary = scan_result.get("summary") or {}

    status = "healthy-no-candidates"
    if provider_errors:
        status = "provider-issues"
    elif missing_tickers:
        status = "partial-coverage"
    elif summary.get("qualified_count", 0) > 0 or len(scan_result.get("alerts", []) or []) > 0:
        status = "healthy-actionable"

    caveats = []
    if provider_errors:
        caveats.append("Provider issues were reported in the current scan.")
    if missing_tickers:
        caveats.append(
            f"{len(missing_tickers)} ticker(s) were unavailable during the current run."
        )
    if not caveats and status == "healthy-no-candidates":
        caveats.append("The scan completed cleanly, but no strong candidates cleared the current thresholds.")

    return {
        "status": status,
        "provider": (scan_result.get("scan_metadata") or {}).get("provider"),
        "provider_error_count": len(provider_errors),
        "missing_ticker_count": len(missing_tickers),
        "caveats": caveats,
    }


def _build_top_opportunity_summary(scan_result: dict[str, Any]) -> dict[str, Any] | None:
    trade = ((scan_result.get("summary") or {}).get("top_overall")) or ((scan_result.get("qualified_trades") or [None])[0])
    if not isinstance(trade, dict) or not trade:
        return None

    return {
        "trade_id": trade.get("trade_id"),
        "ticker": trade.get("ticker"),
        "strategy_type": trade.get("strategy_type"),
        "strategy_label": trade.get("strategy_label"),
        "directional_bias": trade.get("directional_bias"),
        "expiration_date": trade.get("expiration_date"),
        "DTE": trade.get("DTE"),
        "POP": trade.get("POP"),
        "ROR": trade.get("ROR"),
        "score": trade.get("score"),
        "adjusted_score": trade.get("adjusted_score"),
        "decision_summary": trade.get("decision_summary"),
        "status_reason": trade.get("status_reason"),
        "label": trade.get("label"),
    }


def build_scan_comparison_snapshot(
    scan_result: dict[str, Any],
    *,
    previous_scan_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current_summary = scan_result.get("summary") or {}
    current_alerts = scan_result.get("alerts") or []
    current_top_trade = current_summary.get("top_overall") or {}

    if not previous_scan_result:
        notes = ["No previous persisted scan is available for comparison."]
        diagnostics = scan_result.get("diagnostics") or {}
        if diagnostics.get("provider_errors"):
            notes.append("Current scan includes provider errors.")
        if diagnostics.get("missing_tickers"):
            notes.append("Current scan includes missing ticker coverage.")
        return {
            "has_previous_scan": False,
            "previous_scan_id": None,
            "previous_generated_at": None,
            "qualified_count_change": None,
            "alerts_count_change": None,
            "top_opportunity_changed": None,
            "current_top_trade_id": current_top_trade.get("trade_id"),
            "previous_top_trade_id": None,
            "notes": notes,
        }

    previous_summary = previous_scan_result.get("summary") or {}
    previous_alerts = previous_scan_result.get("alerts") or []
    previous_top_trade = previous_summary.get("top_overall") or {}
    qualified_delta = current_summary.get("qualified_count", 0) - previous_summary.get("qualified_count", 0)
    alerts_delta = len(current_alerts) - len(previous_alerts)
    top_changed = current_top_trade.get("trade_id") != previous_top_trade.get("trade_id")

    notes = [
        f"Qualified count changed by {qualified_delta:+d} versus the previous stored scan.",
        f"Alerts count changed by {alerts_delta:+d} versus the previous stored scan.",
    ]
    if previous_top_trade.get("trade_id") and current_top_trade.get("trade_id"):
        if top_changed:
            notes.append("Top opportunity changed from the previous stored scan.")
        else:
            notes.append("Top opportunity is unchanged from the previous stored scan.")

    return {
        "has_previous_scan": True,
        "previous_scan_id": (previous_scan_result.get("scan_metadata") or {}).get("scan_id"),
        "previous_generated_at": (previous_scan_result.get("scan_metadata") or {}).get("generated_at"),
        "qualified_count_change": qualified_delta,
        "alerts_count_change": alerts_delta,
        "top_opportunity_changed": top_changed,
        "current_top_trade_id": current_top_trade.get("trade_id"),
        "previous_top_trade_id": previous_top_trade.get("trade_id"),
        "notes": notes,
    }


def build_overview_snapshot_response(
    scan_result: dict[str, Any],
    *,
    previous_scan_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = scan_result.get("summary") or {}
    scan_metadata = scan_result.get("scan_metadata") or {}
    top_ticker_rows = ((((scan_result.get("portfolio_summary") or {}).get("exposure") or {}).get("qualified") or {}).get("top_ticker_concentration") or [])
    top_ticker_row = top_ticker_rows[0] if top_ticker_rows else None
    decision = ((scan_result.get("portfolio_summary") or {}).get("decision") or {})

    top_ticker_concentration = None
    if isinstance(top_ticker_row, dict) and top_ticker_row:
        top_ticker_concentration = (
            f"{top_ticker_row.get('ticker', 'Top ticker')} {top_ticker_row.get('share_pct', 0)}% of qualified set"
        )

    return {
        "scan_id": scan_metadata.get("scan_id"),
        "headline": {
            "scan_id": scan_metadata.get("scan_id"),
            "generated_at": scan_metadata.get("generated_at"),
            "profile": scan_metadata.get("profile"),
            "ticker_group": scan_metadata.get("ticker_group"),
            "execution_time_seconds": scan_metadata.get("execution_time_seconds"),
            "qualified_count": summary.get("qualified_count", 0),
            "alerts_count": len(scan_result.get("alerts") or []),
            "near_miss_count": summary.get("near_miss_count", 0),
        },
        "top_opportunity": _build_top_opportunity_summary(scan_result),
        "trust_snapshot": _build_scan_trust_snapshot(scan_result),
        "comparison": build_scan_comparison_snapshot(
            scan_result,
            previous_scan_result=previous_scan_result,
        ),
        "portfolio_summary": {
            "posture_label": decision.get("posture_label"),
            "interpretation": decision.get("interpretation", []),
            "top_ticker_concentration": top_ticker_concentration,
            "cautions": decision.get("cautions", []),
        },
    }


def build_trade_summary_row(trade: dict[str, Any]) -> dict[str, Any]:
    return {
        "trade_id": trade.get("trade_id"),
        "ticker": trade.get("ticker"),
        "strategy_type": trade.get("strategy_type"),
        "strategy_key": trade.get("strategy_key"),
        "strategy_label": trade.get("strategy_label"),
        "directional_bias": trade.get("directional_bias"),
        "expiration_date": trade.get("expiration_date"),
        "DTE": trade.get("DTE"),
        "short_strike": trade.get("short_strike"),
        "long_strike": trade.get("long_strike"),
        "POP": trade.get("POP"),
        "ROR": trade.get("ROR"),
        "score": trade.get("score"),
        "adjusted_score": trade.get("adjusted_score"),
        "label": trade.get("label"),
        "decision_summary": trade.get("decision_summary"),
        "status_reason": trade.get("status_reason"),
        "volatility_context": trade.get("volatility_context"),
        "stability_level": trade.get("stability_level"),
        "stability_count": trade.get("stability_count"),
    }


def build_trade_detail_payload(trade: dict[str, Any], scan_result: dict[str, Any]) -> dict[str, Any]:
    breakeven = _breakeven_value(trade)
    scan_id = (scan_result.get("scan_metadata") or {}).get("scan_id")
    history_context = _find_recent_trade_history_context(trade)
    portfolio_fit = _find_portfolio_fit_summary(trade, scan_result)
    warnings = _build_trade_warnings(trade, scan_result)

    return {
        "scan_id": scan_id,
        "trade": {
            **build_trade_summary_row(trade),
            "scan_id": scan_id,
            "direction": _direction_label(trade.get("directional_bias")),
            "underlying_price": trade.get("underlying_price"),
            "net_credit": trade.get("net_credit"),
            "spread_width": trade.get("spread_width"),
            "width": trade.get("spread_width"),
            "max_profit": _first_non_empty(trade.get("max_profit"), trade.get("net_credit")),
            "max_risk": trade.get("max_risk"),
            "max_loss": trade.get("max_risk"),
            "breakeven": breakeven,
            "explanation": trade.get("explanation"),
            "why_this_trade": _first_non_empty(
                trade.get("decision_summary"),
                trade.get("status_reason"),
                trade.get("explanation"),
            ),
            "consistency_bonus": trade.get("consistency_bonus"),
            "consistency_score": _first_non_empty(
                (trade.get("score_breakdown") or {}).get("consistency_score"),
                trade.get("consistency_score"),
                trade.get("stability_count"),
            ),
            "stability_summary": (
                f"{str(trade.get('stability_level') or 'unspecified').replace('_', ' ')}"
                f" ({trade.get('stability_count', 'n/a')})"
            ),
            "portfolio_fit_summary": (portfolio_fit or {}).get("note"),
            "warnings": warnings,
            "diagnostics": [
                note
                for note in [
                    "Provider errors were reported in this scan."
                    if (scan_result.get("diagnostics") or {}).get("provider_errors")
                    else None,
                    f"Missing tickers: {', '.join((scan_result.get('diagnostics') or {}).get('missing_tickers', []))}"
                    if (scan_result.get("diagnostics") or {}).get("missing_tickers")
                    else None,
                ]
                if note
            ],
            "score_breakdown": trade.get("score_breakdown"),
            "penalties": trade.get("penalties"),
        },
        "scan_metadata": {
            "profile": (scan_result.get("scan_metadata") or {}).get("profile"),
            "ticker_group": (scan_result.get("scan_metadata") or {}).get("ticker_group"),
            "generated_at": (scan_result.get("scan_metadata") or {}).get("generated_at"),
        },
        "portfolio_fit": portfolio_fit,
        "history_context": history_context,
        "diagnostics": {
            "provider_errors": (scan_result.get("diagnostics") or {}).get("provider_errors", []),
            "missing_tickers": (scan_result.get("diagnostics") or {}).get("missing_tickers", []),
            "warnings": warnings,
            "notes": history_context.get("notes", []),
        },
    }


def build_trade_detail_response(
    trade: dict[str, Any],
    scan_result: dict[str, Any],
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    payload = build_trade_detail_payload(trade, scan_result)
    payload["history_context"] = _find_recent_trade_history_context(trade, user_id=user_id)
    return payload


def build_history_screen_payload(
    scan_result: dict[str, Any],
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    intelligence = get_historical_intelligence_summary(limit=5, user_id=user_id)
    if not intelligence:
        intelligence = ((scan_result.get("history_context") or {}).get("historical_intelligence_summary") or {})
    metadata = intelligence.get("metadata", {})
    signal_quality = intelligence.get("signal_quality_summary", {})
    feature_summary = intelligence.get("feature_summary", {})

    return {
        "scan_id": (scan_result.get("scan_metadata") or {}).get("scan_id"),
        "summary_cards": [
            {"label": "Runs Analyzed", "value": metadata.get("runs_analyzed", 0)},
            {"label": "Signals Analyzed", "value": metadata.get("signals_analyzed", 0)},
            {"label": "History Available", "value": bool(metadata.get("history_available", False))},
            {"label": "Latest Run", "value": metadata.get("latest_run_timestamp")},
        ],
        "recent_patterns": signal_quality.get("recurring_high_quality_patterns", []),
        "top_tickers": signal_quality.get("most_frequent_qualified_tickers", []),
        "top_strategies": signal_quality.get("most_frequent_qualified_strategies", []),
        "top_pairs": feature_summary.get("average_adjusted_score_by_ticker_strategy_pair", []),
    }


def build_portfolio_screen_payload(scan_result: dict[str, Any]) -> dict[str, Any]:
    portfolio_summary = scan_result.get("portfolio_summary") or {}
    exposure = portfolio_summary.get("exposure") or {}
    position_sizing = portfolio_summary.get("position_sizing") or {}
    overlap = portfolio_summary.get("overlap") or {}
    decision = portfolio_summary.get("decision") or {}
    summary = scan_result.get("summary") or {}

    return {
        "scan_id": (scan_result.get("scan_metadata") or {}).get("scan_id"),
        "summary_cards": [
            {
                "label": "Qualified Trades",
                "value": ((exposure.get("metadata") or {}).get(
                    "qualified_trade_count",
                    summary.get("qualified_count", 0),
                )),
            },
            {
                "label": "Fits Budget",
                "value": ((position_sizing.get("summary") or {}).get("fits_budget_count", 0)),
            },
            {
                "label": "Oversized",
                "value": ((position_sizing.get("summary") or {}).get("oversized_count", 0)),
            },
            {
                "label": "Portfolio Posture",
                "value": decision.get("posture_label", "Portfolio View"),
            },
        ],
        "positions": position_sizing.get("trade_sizing", []),
        "warnings": position_sizing.get("warnings", []),
        "exposure_notes": exposure.get("notes", []),
        "top_ticker_concentration": ((exposure.get("qualified") or {}).get("top_ticker_concentration", [])),
        "directional_exposure": ((exposure.get("qualified") or {}).get("directional_exposure", [])),
        "interpretation": decision.get("interpretation", []),
        "key_signals": decision.get("key_portfolio_signals", []),
        "cautions": decision.get("cautions", []),
        "overlap_warnings": overlap.get("warnings", []),
    }


def build_daily_summary_payload(scan_result: dict[str, Any]) -> dict[str, Any]:
    daily_summary = scan_result.get("daily_summary") or {}
    summary = scan_result.get("summary") or {}
    metadata = scan_result.get("scan_metadata") or {}
    alerts = scan_result.get("alerts") or []

    return {
        "scan_id": (scan_result.get("scan_metadata") or {}).get("scan_id"),
        "headline": {
            "profile": daily_summary.get("profile", metadata.get("profile")),
            "ticker_group": daily_summary.get("ticker_group", metadata.get("ticker_group")),
            "execution_time_seconds": daily_summary.get(
                "execution_time_seconds",
                metadata.get("execution_time_seconds"),
            ),
            "qualified_count": daily_summary.get(
                "qualified_count",
                summary.get("qualified_count", 0),
            ),
            "near_miss_count": daily_summary.get(
                "near_miss_count",
                summary.get("near_miss_count", 0),
            ),
            "alerts_count": daily_summary.get("alerts_count", len(alerts)),
        },
        "top_opportunity": daily_summary.get("top_overall", summary.get("top_overall")),
        "alert_signals": [
            {"label": "Stable Alerts", "value": daily_summary.get("stable_alert_count", 0)},
            {"label": "Emerging Alerts", "value": daily_summary.get("emerging_alert_count", 0)},
            {"label": "New Alerts", "value": daily_summary.get("new_alert_count", 0)},
        ],
        "most_stable_alert": daily_summary.get("most_stable_alert"),
        "notes": [
            *((
                [f"Missing tickers: {', '.join((scan_result.get('diagnostics') or {}).get('missing_tickers', []))}"]
                if (scan_result.get("diagnostics") or {}).get("missing_tickers")
                else []
            )),
            *((
                ["Provider errors were reported in the latest scan."]
                if (scan_result.get("diagnostics") or {}).get("provider_errors")
                else []
            )),
        ],
    }
