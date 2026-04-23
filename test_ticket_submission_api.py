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
from backend.services.ticket_submission_service import map_broker_status_for_tests


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, object]):
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
        "trade_id": "trade_submit_1",
        "source_scan_id": "scan_submit_1",
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
        "quantity": 2,
        "order_intent": "open_credit",
        "note": "Ready for paper submission.",
    }


def _create_ticket(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/tickets", json=_ticket_payload(), headers=headers)
    assert response.status_code == 201
    return response.json()["ticket_id"]


def _error_message(response) -> str:
    payload = response.json()
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str):
            return detail
        nested = payload.get("error")
        if isinstance(nested, dict) and isinstance(nested.get("message"), str):
            return nested["message"]
    return ""


def test_ticket_submission_success_and_refresh_status(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_ticket_submission_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    _configure_paper_credentials(monkeypatch)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        monkeypatch.setattr(
            "backend.services.ticket_submission_service.requests.post",
            lambda *args, **kwargs: _FakeResponse(
                200,
                {
                    "id": "order_1",
                    "status": "new",
                    "submitted_at": "2026-04-23T10:00:00Z",
                    "updated_at": "2026-04-23T10:00:01Z",
                },
            ),
        )
        monkeypatch.setattr(
            "backend.services.ticket_submission_service.requests.get",
            lambda *args, **kwargs: _FakeResponse(
                200,
                {
                    "id": "order_1",
                    "status": "filled",
                    "updated_at": "2026-04-23T10:05:00Z",
                },
            ),
        )

        client = TestClient(app)
        headers = _register_and_get_headers(client, f"submit-user-{uuid.uuid4().hex}@example.com")
        ticket_id = _create_ticket(client, headers)

        submit_response = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper", headers=headers)
        assert submit_response.status_code == 200
        submitted = submit_response.json()

        assert submitted["broker_order_id"] == "order_1"
        assert submitted["broker_status_raw"] == "new"
        assert submitted["execution_status"] == "accepted"
        assert submitted["last_submission_payload"]["order_class"] == "mleg"

        refresh_response = client.post(f"/api/v1/tickets/{ticket_id}/refresh-paper", headers=headers)
        assert refresh_response.status_code == 200
        refreshed = refresh_response.json()
        assert refreshed["execution_status"] == "filled"
        assert refreshed["broker_status_raw"] == "filled"
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_ticket_submission_rejects_invalid_state_and_unauthenticated(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_ticket_submission_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    _configure_paper_credentials(monkeypatch)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        monkeypatch.setattr(
            "backend.services.ticket_submission_service.requests.post",
            lambda *args, **kwargs: _FakeResponse(
                200,
                {
                    "id": "order_2",
                    "status": "accepted",
                    "submitted_at": "2026-04-23T10:00:00Z",
                    "updated_at": "2026-04-23T10:00:01Z",
                },
            ),
        )

        client = TestClient(app)
        headers = _register_and_get_headers(client, f"submit-user-{uuid.uuid4().hex}@example.com")
        ticket_id = _create_ticket(client, headers)

        first_submit = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper", headers=headers)
        assert first_submit.status_code == 200

        second_submit = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper", headers=headers)
        assert second_submit.status_code == 400
        assert "not eligible" in _error_message(second_submit).lower()

        unauthenticated = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper")
        assert unauthenticated.status_code == 401
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_ticket_submission_missing_credentials_and_broker_rejection(monkeypatch):
    workspace_tmp_dir = Path("tmp_test_ticket_submission_api") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    _force_mock_mode(monkeypatch, workspace_tmp_dir)
    clear_scan_store()
    get_auth_repository().clear()

    try:
        monkeypatch.setenv("ALPACA_API_KEY", "")
        monkeypatch.setenv("ALPACA_API_SECRET", "")
        client = TestClient(app)
        headers = _register_and_get_headers(client, f"submit-user-{uuid.uuid4().hex}@example.com")
        ticket_id = _create_ticket(client, headers)

        # Missing credentials path
        missing_creds = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper", headers=headers)
        assert missing_creds.status_code == 400
        assert "credentials" in _error_message(missing_creds).lower()

        _configure_paper_credentials(monkeypatch)
        monkeypatch.setattr(
            "backend.services.ticket_submission_service.requests.post",
            lambda *args, **kwargs: _FakeResponse(
                422,
                {"status": "rejected", "message": "insufficient buying power"},
            ),
        )

        rejected = client.post(f"/api/v1/tickets/{ticket_id}/submit-paper", headers=headers)
        assert rejected.status_code == 400
        assert "rejected" in _error_message(rejected).lower() or "buying power" in _error_message(rejected).lower()

        ticket_response = client.get(f"/api/v1/tickets/{ticket_id}", headers=headers)
        assert ticket_response.status_code == 200
        ticket = ticket_response.json()
        assert ticket["execution_status"] == "rejected"
        assert ticket["submission_error_message"] is not None
    finally:
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_broker_status_mapping():
    assert map_broker_status_for_tests("new") == "accepted"
    assert map_broker_status_for_tests("accepted") == "accepted"
    assert map_broker_status_for_tests("filled") == "filled"
    assert map_broker_status_for_tests("rejected") == "rejected"
    assert map_broker_status_for_tests("canceled") == "canceled"
    assert map_broker_status_for_tests("unknown_state") == "submitted"
