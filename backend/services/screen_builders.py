"""Backend-owned shaping helpers for frontend-safe screen payloads."""

from __future__ import annotations

from typing import Any


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
    return {
        "scan_id": ((scan_result.get("scan_metadata") or {}).get("scan_id")),
        "trade": {
            **build_trade_summary_row(trade),
            "underlying_price": trade.get("underlying_price"),
            "net_credit": trade.get("net_credit"),
            "spread_width": trade.get("spread_width"),
            "max_risk": trade.get("max_risk"),
            "explanation": trade.get("explanation"),
            "consistency_bonus": trade.get("consistency_bonus"),
            "score_breakdown": trade.get("score_breakdown"),
            "penalties": trade.get("penalties"),
        },
        "scan_metadata": {
            "profile": (scan_result.get("scan_metadata") or {}).get("profile"),
            "ticker_group": (scan_result.get("scan_metadata") or {}).get("ticker_group"),
            "generated_at": (scan_result.get("scan_metadata") or {}).get("generated_at"),
        },
        "diagnostics": {
            "provider_errors": (scan_result.get("diagnostics") or {}).get("provider_errors", []),
            "missing_tickers": (scan_result.get("diagnostics") or {}).get("missing_tickers", []),
        },
    }


def build_history_screen_payload(scan_result: dict[str, Any]) -> dict[str, Any]:
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

    return {
        "scan_id": (scan_result.get("scan_metadata") or {}).get("scan_id"),
        "summary_cards": [
            {
                "label": "Qualified Trades",
                "value": ((exposure.get("metadata") or {}).get("qualified_trade_count", 0)),
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

    return {
        "scan_id": (scan_result.get("scan_metadata") or {}).get("scan_id"),
        "headline": {
            "profile": daily_summary.get("profile"),
            "ticker_group": daily_summary.get("ticker_group"),
            "execution_time_seconds": daily_summary.get("execution_time_seconds"),
            "qualified_count": daily_summary.get("qualified_count"),
            "near_miss_count": daily_summary.get("near_miss_count"),
            "alerts_count": daily_summary.get("alerts_count"),
        },
        "top_opportunity": daily_summary.get("top_overall"),
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
