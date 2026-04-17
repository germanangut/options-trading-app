import shutil
import uuid
from pathlib import Path

import data_provider
import pytest


pytest.importorskip("fastapi")
pytest.importorskip("uvicorn")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.repositories.factory import get_auth_repository
from backend.services.scan_store import clear_scan_store, save_scan_result


def _force_mock_mode(monkeypatch, workspace_tmp_dir: Path):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(workspace_tmp_dir / "history" / "scan_store.sqlite"),
    )


def _register_and_get_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _build_trade(
    ticker: str,
    *,
    trade_id: str,
    adjusted_score: float,
    stability_level: str = "stable",
    stability_count: int = 3,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "ticker": ticker,
        "strategy_type": "bull_put_spread",
        "strategy_key": "bull_put_spread",
        "strategy_label": "Bull Put Spread",
        "directional_bias": "bullish",
        "expiration_date": "2026-05-15",
        "DTE": 29,
        "short_strike": 180.0,
        "long_strike": 175.0,
        "POP": 66.0,
        "ROR": 21.0,
        "score": adjusted_score - 2,
        "adjusted_score": adjusted_score,
        "label": "High Quality",
        "decision_summary": f"{ticker} remains one of the stronger current candidates.",
        "status_reason": f"{ticker} cleared the current score and quality thresholds.",
        "volatility_context": "balanced_premium",
        "stability_level": stability_level,
        "stability_count": stability_count,
        "underlying_price": 184.25,
        "net_credit": 1.2,
        "spread_width": 5.0,
        "max_risk": 3.8,
        "max_profit": 1.2,
        "breakeven": 178.8,
        "explanation": f"{ticker} keeps a favorable premium-to-risk balance in the current run.",
        "score_breakdown": {"consistency_score": stability_count, "premium_score": 7.5},
        "price_context_warning": False,
        "price_context_reason": None,
    }


def _build_scan(
    scan_id: str,
    generated_at: str,
    trade: dict[str, object],
    *,
    qualified_count: int,
    alerts_count: int,
) -> dict[str, object]:
    alerts = [dict(trade) for _ in range(alerts_count)]
    qualified = [dict(trade) for _ in range(qualified_count)]
    return {
        "scan_metadata": {
            "scan_id": scan_id,
            "generated_at": generated_at,
            "profile": "balanced",
            "ticker_group": "tech",
            "selected_strategy_keys": ["bull_put_spread"],
            "dte_range": {"dte_min": 20, "dte_max": 35},
            "scoring_weights": {"pop_weight": 0.6, "ror_weight": 0.4},
            "alert_thresholds": {"min_score": 65, "min_consistency": 3},
            "execution_time_seconds": 1.2,
            "provider": "alpaca-mock-fallback",
            "request": {
                "profile": "balanced",
                "ticker_group": "tech",
                "selected_strategy_keys": ["bull_put_spread"],
                "dte_min": 20,
                "dte_max": 35,
                "min_score": 65,
                "min_pop": None,
                "min_ror": None,
                "min_consistency": 3,
                "alerts_only": False,
                "use_mock_data": None,
            },
        },
        "summary": {
            "qualified_count": qualified_count,
            "near_miss_count": 0,
            "top_overall": dict(trade),
            "top_bull_put": dict(trade),
            "top_bear_call": None,
        },
        "qualified_trades": qualified,
        "alerts": alerts,
        "near_miss_trades": [],
        "ticker_diagnostics": [],
        "portfolio_summary": {
            "exposure": {
                "metadata": {"qualified_trade_count": qualified_count},
                "qualified": {
                    "top_ticker_concentration": [{"ticker": trade["ticker"], "count": qualified_count, "share_pct": 100}],
                },
                "notes": [f"{trade['ticker']} is fully concentrated in this synthetic scan."],
            },
            "position_sizing": {
                "trade_sizing": [
                    {
                        "ticker": trade["ticker"],
                        "strategy": trade["strategy_label"],
                        "adjusted_score": trade["adjusted_score"],
                        "estimated_max_risk_dollars": 380.0,
                        "fits_risk_budget": True,
                        "approx_contracts_within_budget": 2,
                        "sizing_note": "Fits within the current sample risk budget.",
                    }
                ],
                "warnings": [],
            },
            "decision": {
                "posture_label": "Focused exposure",
                "interpretation": ["The current set is concentrated in a single ticker/strategy combination."],
                "cautions": ["Review concentration before scaling this candidate."],
            },
        },
        "history_context": {},
        "daily_summary": {},
        "diagnostics": {
            "missing_tickers": [],
            "provider_errors": [],
            "alerts_export_path": None,
            "top_overall_identity": {
                "ticker": trade["ticker"],
                "strategy_type": trade["strategy_type"],
                "expiration_date": trade["expiration_date"],
                "short_strike": trade["short_strike"],
                "long_strike": trade["long_strike"],
            },
        },
    }


def test_overview_snapshot_compares_against_previous_scan(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_decision_experience_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"overview-{uuid.uuid4().hex}@example.com")
        previous_trade = _build_trade("AAPL", trade_id="trade_prev", adjusted_score=71.0)
        current_trade = _build_trade("MSFT", trade_id="trade_curr", adjusted_score=75.0)

        save_scan_result(_build_scan("scan_prev", "2026-04-16T08:00:00Z", previous_trade, qualified_count=1, alerts_count=1), user_id=client.get("/auth/me", headers=headers).json()["user_id"])
        save_scan_result(_build_scan("scan_curr", "2026-04-16T09:00:00Z", current_trade, qualified_count=2, alerts_count=0), user_id=client.get("/auth/me", headers=headers).json()["user_id"])

        response = client.get("/api/v1/scans/scan_curr/overview", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["comparison"]["has_previous_scan"] is True
        assert body["comparison"]["previous_scan_id"] == "scan_prev"
        assert body["comparison"]["qualified_count_change"] == 1
        assert body["comparison"]["alerts_count_change"] == -1
        assert body["comparison"]["top_opportunity_changed"] is True
        assert body["trust_snapshot"]["status"] == "healthy-actionable"
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_trade_detail_enriched_payload_and_history_context(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_decision_experience_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"detail-{uuid.uuid4().hex}@example.com")
        user_id = client.get("/auth/me", headers=headers).json()["user_id"]
        trade = _build_trade("AAPL", trade_id="trade_aapl", adjusted_score=74.5, stability_count=4)
        older = _build_scan("scan_old", "2026-04-16T07:00:00Z", trade, qualified_count=1, alerts_count=1)
        current = _build_scan("scan_now", "2026-04-16T09:00:00Z", trade, qualified_count=1, alerts_count=1)
        save_scan_result(older, user_id=user_id)
        save_scan_result(current, user_id=user_id)

        response = client.get("/api/v1/scans/scan_now/trades/trade_aapl", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["trade"]["trade_id"] == "trade_aapl"
        assert body["trade"]["max_profit"] == 1.2
        assert body["trade"]["max_loss"] == 3.8
        assert body["trade"]["breakeven"] == 178.8
        assert body["trade"]["why_this_trade"]
        assert body["history_context"]["has_history"] is True
        assert body["history_context"]["recent_appearance_count"] >= 2
        assert body["history_context"]["appeared_recently"] is True
        assert body["portfolio_fit"]["fits_risk_budget"] is True
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_trade_history_context_gracefully_handles_absent_history(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_decision_experience_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"history-{uuid.uuid4().hex}@example.com")
        user_id = client.get("/auth/me", headers=headers).json()["user_id"]
        trade = _build_trade("NFLX", trade_id="trade_nflx", adjusted_score=70.0)
        current = _build_scan("scan_lonely", "2026-04-16T09:00:00Z", trade, qualified_count=1, alerts_count=0)
        save_scan_result(current, user_id=user_id)

        overview_response = client.get("/api/v1/scans/scan_lonely/overview", headers=headers)
        detail_response = client.get("/api/v1/scans/scan_lonely/trades/trade_nflx", headers=headers)

        assert overview_response.status_code == 200
        assert detail_response.status_code == 200
        assert overview_response.json()["comparison"]["has_previous_scan"] is False
        assert detail_response.json()["history_context"]["runs_analyzed"] == 1
        assert detail_response.json()["history_context"]["recent_appearance_count"] == 1
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)