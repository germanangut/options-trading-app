"""Canonical ScanResult adapter for the first backend seam.

This module intentionally preserves the current engine payloads as much as
possible. It only reshapes the top-level sections so a future API layer can
depend on a stable backend contract without changing trading behavior.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
import hashlib
from typing import Any
from uuid import uuid4

from history import get_historical_intelligence_summary


@dataclass(frozen=True)
class ScanRequest:
    """Typed input for the backend scan service.

    Notes:
    - `min_pop` and `min_ror` are accepted for forward compatibility with the
      eventual API contract, but the current engine does not support them.
    - `alerts_only` is also retained as a request field even though the engine
      always returns the full payload today.
    """

    profile: str = "balanced"
    ticker_group: str = "tech"
    selected_strategy_keys: list[str] = field(default_factory=list)
    dte_min: int = 20
    dte_max: int = 35
    min_score: int = 65
    min_pop: float | None = None
    min_ror: float | None = None
    min_consistency: int = 3
    alerts_only: bool = False
    use_mock_data: bool | None = None


def _trade_identity(trade: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(trade, dict) or not trade:
        return None

    return {
        "ticker": trade.get("ticker"),
        "strategy_type": trade.get("strategy_type"),
        "expiration_date": trade.get("expiration_date"),
        "short_strike": trade.get("short_strike"),
        "long_strike": trade.get("long_strike"),
    }


def build_trade_identity_key(trade: dict[str, Any] | None) -> str | None:
    identity = _trade_identity(trade)
    if not identity:
        return None

    return "|".join(
        str(identity.get(field) or "").strip()
        for field in (
            "ticker",
            "strategy_type",
            "expiration_date",
            "short_strike",
            "long_strike",
        )
    )


def generate_trade_id(trade: dict[str, Any] | None) -> str | None:
    identity_key = build_trade_identity_key(trade)
    if not identity_key:
        return None

    digest = hashlib.sha256(identity_key.encode("utf-8")).hexdigest()
    return f"trade_{digest[:16]}"


def _attach_trade_ids(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = deepcopy(trades)

    for trade in normalized:
        trade_id = generate_trade_id(trade)
        if trade_id:
            trade["trade_id"] = trade_id

    return normalized


def _attach_summary_trade_id(summary_trade: dict[str, Any] | None, trades: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not isinstance(summary_trade, dict) or not summary_trade:
        return summary_trade

    normalized = deepcopy(summary_trade)
    summary_identity_key = build_trade_identity_key(summary_trade)
    if not summary_identity_key:
        return normalized

    for trade in trades:
        if build_trade_identity_key(trade) == summary_identity_key and trade.get("trade_id"):
            normalized["trade_id"] = trade["trade_id"]
            break

    return normalized


def _build_scan_metadata(raw_output: dict[str, Any], request: ScanRequest, scan_id: str) -> dict[str, Any]:
    return {
        "scan_id": scan_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "profile": raw_output.get("profile", request.profile),
        "ticker_group": raw_output.get("ticker_group", request.ticker_group),
        "selected_strategy_keys": deepcopy(
            raw_output.get("selected_strategy_keys", request.selected_strategy_keys)
        ),
        "dte_range": deepcopy(raw_output.get("dte_range", {})),
        "scoring_weights": deepcopy(raw_output.get("scoring_weights", {})),
        "alert_thresholds": deepcopy(raw_output.get("alert_thresholds", {})),
        "execution_time_seconds": raw_output.get("execution_time_seconds"),
        "provider": raw_output.get("provider"),
        "request": {
            "profile": request.profile,
            "ticker_group": request.ticker_group,
            "selected_strategy_keys": list(request.selected_strategy_keys),
            "dte_min": request.dte_min,
            "dte_max": request.dte_max,
            "min_score": request.min_score,
            "min_pop": request.min_pop,
            "min_ror": request.min_ror,
            "min_consistency": request.min_consistency,
            "alerts_only": request.alerts_only,
            "use_mock_data": request.use_mock_data,
        },
    }


def build_scan_result(raw_output: dict[str, Any], request: ScanRequest, scan_id: str | None = None) -> dict[str, Any]:
    """Adapt the current engine output into the first canonical ScanResult."""
    raw_output = raw_output or {}
    scan_id = scan_id or f"scan_{uuid4().hex}"

    summary = deepcopy(raw_output.get("summary", {}))
    qualified_trades = _attach_trade_ids(raw_output.get("qualified", []))
    alerts = _attach_trade_ids(raw_output.get("alerts", []))
    near_miss_trades = _attach_trade_ids(raw_output.get("near_miss", []))
    ticker_diagnostics = deepcopy(raw_output.get("ticker_diagnostics", []))
    portfolio_summary = {
        "exposure": deepcopy(raw_output.get("portfolio_exposure_summary", {})),
        "position_sizing": deepcopy(raw_output.get("position_sizing_summary", {})),
        "overlap": deepcopy(raw_output.get("exposure_overlap_summary", {})),
        "decision": deepcopy(raw_output.get("portfolio_decision_summary", {})),
    }

    stable_alerts = [trade for trade in alerts if trade.get("stability_level") == "stable"]
    emerging_alerts = [trade for trade in alerts if trade.get("stability_level") == "emerging"]
    new_alerts = [trade for trade in alerts if trade.get("stability_level") == "new"]
    all_trades = qualified_trades + alerts + near_miss_trades

    summary["top_overall"] = _attach_summary_trade_id(summary.get("top_overall"), all_trades)
    summary["top_bull_put"] = _attach_summary_trade_id(summary.get("top_bull_put"), all_trades)
    summary["top_bear_call"] = _attach_summary_trade_id(summary.get("top_bear_call"), all_trades)

    top_overall = summary.get("top_overall") or (qualified_trades[0] if qualified_trades else None)

    daily_summary = {
        "scan_id": scan_id,
        "profile": raw_output.get("profile", request.profile),
        "ticker_group": raw_output.get("ticker_group", request.ticker_group),
        "execution_time_seconds": raw_output.get("execution_time_seconds"),
        "dte_range": deepcopy(raw_output.get("dte_range", {})),
        "qualified_count": summary.get("qualified_count", len(qualified_trades)),
        "near_miss_count": summary.get("near_miss_count", len(near_miss_trades)),
        "alerts_count": len(alerts),
        "top_overall": deepcopy(top_overall),
        "stable_alert_count": len(stable_alerts),
        "emerging_alert_count": len(emerging_alerts),
        "new_alert_count": len(new_alerts),
        "most_stable_alert": deepcopy(
            max(alerts, key=lambda trade: trade.get("stability_count", 0))
        ) if alerts else None,
    }

    return {
        "scan_metadata": _build_scan_metadata(raw_output, request, scan_id),
        "summary": summary,
        "qualified_trades": qualified_trades,
        "alerts": alerts,
        "near_miss_trades": near_miss_trades,
        "ticker_diagnostics": ticker_diagnostics,
        "portfolio_summary": portfolio_summary,
        "history_context": {
            "historical_intelligence_summary": get_historical_intelligence_summary(limit=5),
        },
        "daily_summary": daily_summary,
        "diagnostics": {
            "missing_tickers": deepcopy(raw_output.get("missing_tickers", [])),
            "provider_errors": deepcopy(raw_output.get("provider_errors", [])),
            "alerts_export_path": raw_output.get("alerts_export_path"),
            "top_overall_identity": _trade_identity(top_overall),
        },
    }
