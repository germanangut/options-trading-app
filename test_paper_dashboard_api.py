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
from backend.services.scan_store import clear_scan_store


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


def _force_mock_mode(monkeypatch, workspace_tmp_dir: Path):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(workspace_tmp_dir / "history"))
    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv(
        "SCAN_DATABASE_PATH",
        str(workspace_tmp_dir / "history" / "scan_store.sqlite"),
    )


def _configure_paper_credentials(monkeypatch):
    monkeypatch.setenv("ALPACA_API_KEY", "paper-key")
    monkeypatch.setenv("ALPACA_API_SECRET", "paper-secret")
    monkeypatch.setenv("ALPACA_TRADING_BASE_URL", "https://paper-api.alpaca.markets")


def _register_and_get_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _ticket_payload() -> dict[str, object]:
    return {
        "trade_id": "trade_dashboard_1",
        "source_scan_id": "scan_dashboard_1",
        "ticker": "aapl",
        "strategy_key": "bull_put_spread",
        "strategy_label": "Bull Put Spread",
        "directional_bias": "bullish",
        "expiration_date": "2026-05-15",
        "short_strike": 180,
        "long_strike": 175,
        "underlying_price_at_creation": 191.2,
        "net_credit_estimate": 1.45,
        "max_risk_estimate": 355,
        "adjusted_score_at_creation": 74,
        "quantity": 1,
        "order_intent": "open_credit",
        "note": "dashboard test",
    }


def _create_ticket(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/tickets", json=_ticket_payload(), headers=headers)
    assert response.status_code == 201
    return response.json()["ticket_id"]


def test_paper_dashboard_groups_pending_open_closed(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_paper_dashboard_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    _configure_paper_credentials(monkeypatch)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        post_calls = {"count": 0}

        def fake_post(*args, **kwargs):
            post_calls["count"] += 1
            status = "accepted" if post_calls["count"] == 1 else "rejected"
            return _FakeResponse(
                200 if status == "accepted" else 422,
                {
                    "id": f"order_{post_calls['count']}",
                    "status": status,
                    "submitted_at": "2026-04-23T11:00:00Z",
                    "updated_at": "2026-04-23T11:01:00Z",
                    "message": "rejected by risk checks" if status == "rejected" else None,
                },
            )

        monkeypatch.setattr("backend.services.ticket_submission_service.requests.post", fake_post)
        monkeypatch.setattr(
            "backend.services.ticket_submission_service.requests.get",
            lambda url, **kwargs: _FakeResponse(
                200,
                [
                    {
                        "symbol": "AAPL260515P00180000",
                        "qty": "1",
                        "side": "long",
                        "avg_entry_price": "1.10",
                        "market_value": "120",
                        "cost_basis": "110",
                        "unrealized_pl": "10",
                        "unrealized_plpc": "0.09",
                    }
                ] if "/v2/positions" in url else [
                    {
                        "id": "order_1",
                        "symbol": "AAPL260515P00180000",
                        "status": "accepted",
                        "type": "limit",
                        "side": "buy",
                        "qty": "1",
                        "filled_qty": "0",
                        "submitted_at": "2026-04-23T11:00:00Z",
                        "updated_at": "2026-04-23T11:01:00Z",
                    }
                ],
            ),
        )

        client = TestClient(app)
        headers = _register_and_get_headers(client, f"dashboard-user-{uuid.uuid4().hex}@example.com")

        ticket_pending = _create_ticket(client, headers)
        ticket_submitted = _create_ticket(client, headers)
        ticket_rejected = _create_ticket(client, headers)

        ready_response = client.patch(f"/api/v1/tickets/{ticket_pending}", json={"execution_status": "ready"}, headers=headers)
        assert ready_response.status_code == 200

        submit_ok = client.post(f"/api/v1/tickets/{ticket_submitted}/submit-paper", headers=headers)
        assert submit_ok.status_code == 200

        submit_rejected = client.post(f"/api/v1/tickets/{ticket_rejected}/submit-paper", headers=headers)
        assert submit_rejected.status_code == 400

        dashboard_response = client.get("/api/v1/tickets/paper-dashboard", headers=headers)
        assert dashboard_response.status_code == 200

        dashboard = dashboard_response.json()
        assert dashboard["summary"]["pending_count"] >= 1
        assert dashboard["summary"]["open_positions_count"] >= 1
        assert dashboard["summary"]["closed_count"] >= 1
        assert dashboard["summary"]["recent_orders_count"] >= 1

        assert len(dashboard["pending_orders"]) >= 1
        assert len(dashboard["open_positions"]) >= 1
        assert len(dashboard["closed_trades"]) >= 1
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_paper_dashboard_empty_and_unauthenticated(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_paper_dashboard_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"dashboard-user-{uuid.uuid4().hex}@example.com")

        dashboard_response = client.get("/api/v1/tickets/paper-dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        body = dashboard_response.json()

        assert body["pending_orders"] == []
        assert body["open_positions"] == []
        assert body["closed_trades"] == []

        unauthenticated = client.get("/api/v1/tickets/paper-dashboard")
        assert unauthenticated.status_code == 401
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)
