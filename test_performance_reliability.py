from pathlib import Path
import shutil
import uuid

import pytest
import requests

import data_provider
from data_provider import discover_option_contracts_for_window, fetch_underlying_stock_trade
from engine import run_scan_engine
from mock_data import MOCK_OPTIONS_DATA


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _workspace_tmp_dir() -> Path:
    workspace_tmp_dir = Path("tmp_test_performance_reliability") / str(uuid.uuid4())
    workspace_tmp_dir.mkdir(parents=True, exist_ok=True)
    return workspace_tmp_dir


def test_run_scan_engine_keeps_successful_tickers_when_one_provider_result_fails(monkeypatch):
    provider_result = {
        "market_data": {"QQQ": MOCK_OPTIONS_DATA["QQQ"]},
        "missing_tickers": ["BROKEN"],
        "provider": "alpaca-contracts-plus-symbol-snapshots",
        "provider_errors": [
            {
                "ticker": "BROKEN",
                "error": "Provider request timed out.",
                "category": "timeout",
            }
        ],
        "ticker_diagnostics": [
            {
                "ticker": "QQQ",
                "provider_status": "ok",
                "provider": "alpaca",
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 3,
                "provider_duration_ms": 75.5,
                "retry_count": 1,
                "duration_ms": 75.5,
                "provider_diagnostics": {"ticker": "QQQ", "valid_contract_count": 8},
            },
            {
                "ticker": "BROKEN",
                "provider_status": "error",
                "provider": "alpaca",
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 2,
                "provider_duration_ms": 120.0,
                "retry_count": 2,
                "duration_ms": 120.0,
                "provider_diagnostics": {"ticker": "BROKEN", "reason": "Provider request timed out."},
            },
        ],
        "cache": {
            "market_data": {"hit": False},
            "contracts": {"hits": 0, "misses": 1},
            "snapshots": {"hits": 0, "misses": 1},
            "underlying": {"hits": 0, "misses": 1},
        },
        "performance": {
            "provider_duration_ms": 180.0,
            "total_provider_calls": 5,
            "average_provider_latency_ms": 36.0,
            "retry_latency_impact_ms": 150.0,
            "estimated_cache_saved_duration_ms": 0.0,
        },
    }

    monkeypatch.setattr("engine.get_market_data", lambda *args, **kwargs: provider_result)

    result = run_scan_engine(
        profile_name="balanced",
        group_name="tech",
        tickers=["QQQ", "BROKEN"],
        persist_history=False,
    )

    assert result["partial_result"] is True
    assert result["provider_errors"] == provider_result["provider_errors"]
    assert any(trade["ticker"] == "QQQ" for trade in result["qualified"])
    assert len(result["ticker_diagnostics"]) == 2
    broken = next(item for item in result["ticker_diagnostics"] if item["ticker"] == "BROKEN")
    assert broken["provider_status"] == "error"
    assert broken["provider_diagnostics"]["reason"] == "Provider request timed out."
    assert result["performance"]["processed_ticker_count"] == 2
    assert result["performance"]["successful_ticker_count"] == 1
    assert result["performance"]["failed_ticker_count"] == 1
    assert result["performance"]["total_provider_calls"] == 5
    assert result["performance"]["ticker_retry_count_total"] == 3
    assert result["performance"]["ticker_cache_miss_count"] == 2


def test_run_scan_engine_returns_consistent_empty_shape_when_all_tickers_fail(monkeypatch):
    provider_result = {
        "market_data": {},
        "missing_tickers": ["AAA", "BBB"],
        "provider": "alpaca-contracts-plus-symbol-snapshots",
        "provider_errors": [
            {
                "ticker": "AAA",
                "error": "Provider request timed out.",
                "category": "timeout",
                "retry_count": 2,
            },
            {
                "ticker": "BBB",
                "error": "Provider retry budget exhausted.",
                "category": "timeout",
                "retry_count": 3,
            },
        ],
        "ticker_diagnostics": [
            {
                "ticker": "AAA",
                "provider_status": "error",
                "provider": "alpaca",
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 3,
                "provider_duration_ms": 155.0,
                "retry_count": 2,
                "duration_ms": 155.0,
                "provider_diagnostics": {"ticker": "AAA", "reason": "Provider request timed out."},
            },
            {
                "ticker": "BBB",
                "provider_status": "error",
                "provider": "alpaca",
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 4,
                "provider_duration_ms": 220.0,
                "retry_count": 3,
                "duration_ms": 220.0,
                "provider_diagnostics": {"ticker": "BBB", "reason": "Provider retry budget exhausted."},
            },
        ],
        "cache": {
            "market_data": {"hit": False},
            "contracts": {"hits": 0, "misses": 2},
            "snapshots": {"hits": 0, "misses": 2},
            "underlying": {"hits": 0, "misses": 2},
        },
        "performance": {
            "provider_duration_ms": 375.0,
            "total_provider_calls": 7,
            "average_provider_latency_ms": 53.57,
            "retry_count": 5,
            "retry_exhausted": True,
            "retry_latency_impact_ms": 260.0,
            "estimated_cache_saved_duration_ms": 0.0,
        },
    }

    monkeypatch.setattr("engine.get_market_data", lambda *args, **kwargs: provider_result)

    result = run_scan_engine(
        profile_name="balanced",
        group_name="tech",
        tickers=["AAA", "BBB"],
        persist_history=False,
    )

    assert result["partial_result"] is True
    assert result["qualified"] == []
    assert result["alerts"] == []
    assert result["summary"]["qualified_count"] == 0
    assert result["summary"]["top_overall"] is None
    assert result["missing_tickers"] == ["AAA", "BBB"]
    assert len(result["provider_errors"]) == 2
    assert len(result["ticker_diagnostics"]) == 2
    assert all(item["provider_status"] == "error" for item in result["ticker_diagnostics"])
    assert result["performance"]["processed_ticker_count"] == 2
    assert result["performance"]["successful_ticker_count"] == 0
    assert result["performance"]["failed_ticker_count"] == 2
    assert result["performance"]["retry_count"] == 5
    assert result["performance"]["retry_exhausted"] is True
    assert result["performance"]["retry_latency_impact_ms"] == pytest.approx(260.0, abs=0.01)


def test_discover_contracts_retries_after_timeout(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}
    data_provider._clear_in_memory_cache()

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        if call_count["value"] == 1:
            raise requests.exceptions.Timeout("timed out")

        return _FakeResponse(
            200,
            {
                "option_contracts": [
                    {
                        "symbol": "SPY250117P00450000",
                        "expiration_date": "2030-01-17",
                    }
                ]
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        result = discover_option_contracts_for_window("SPY", dte_min=1, dte_max=4000)
        assert call_count["value"] == 2
        assert result["contracts"]
        assert result["request_metadata"]["attempt_count"] == 2
        assert result["request_metadata"]["retry_count"] == 1
        assert result["request_metadata"]["retry_exhausted"] is False
        assert result["request_metadata"]["cache_hit"] is False
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_discover_contracts_reports_retry_exhaustion(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}
    data_provider._clear_in_memory_cache()

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        raise requests.exceptions.Timeout("still timing out")

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_RETRY_COUNT", "2")
    monkeypatch.setenv("PROVIDER_TOTAL_TIMEOUT_SECONDS", "20")
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        with pytest.raises(data_provider.ProviderRequestError) as exc_info:
            discover_option_contracts_for_window("SPY", dte_min=1, dte_max=4000)

        assert call_count["value"] == 3
        assert exc_info.value.retry_count == 2
        assert exc_info.value.retry_exhausted is True
        assert exc_info.value.category == "timeout"
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_discover_contracts_does_not_retry_auth_failure(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}
    data_provider._clear_in_memory_cache()

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        return _FakeResponse(401, {"message": "unauthorized"})

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_RETRY_COUNT", "2")
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        with pytest.raises(data_provider.ProviderRequestError) as exc_info:
            discover_option_contracts_for_window("SPY", dte_min=1, dte_max=4000)

        assert call_count["value"] == 1
        assert exc_info.value.retry_count == 0
        assert exc_info.value.retry_exhausted is False
        assert exc_info.value.category == "auth"
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_fetch_underlying_trade_uses_cache_on_repeat_call(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        return _FakeResponse(
            200,
            {
                "trades": {
                    "SPY": {
                        "p": 502.13,
                    }
                }
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_MEMORY_CACHE_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_UNDERLYING_CACHE_TTL_SECONDS", "60")
    data_provider._clear_in_memory_cache()
    monkeypatch.setattr(data_provider.requests, "get", fake_get)

    try:
        first = fetch_underlying_stock_trade("SPY")
        second = fetch_underlying_stock_trade("SPY")

        assert call_count["value"] == 1
        assert first["trade"]["p"] == 502.13
        assert second["trade"]["p"] == 502.13
        assert first["request_metadata"]["cache_hit"] is False
        assert first["request_metadata"]["cache_miss"] is True
        assert second["request_metadata"]["cache_hit"] is True
        assert second["request_metadata"]["cache_layer"] == "memory"
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_fetch_underlying_trade_cache_expires(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}
    current_time = {"value": 1000.0}

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        return _FakeResponse(
            200,
            {
                "trades": {
                    "SPY": {
                        "p": 499.25,
                    }
                }
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_MEMORY_CACHE_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_UNDERLYING_CACHE_TTL_SECONDS", "1")
    monkeypatch.setattr(data_provider.time, "time", lambda: current_time["value"])
    monkeypatch.setattr(data_provider.requests, "get", fake_get)
    data_provider._clear_in_memory_cache()

    try:
        first = fetch_underlying_stock_trade("SPY")
        current_time["value"] = 1002.0
        second = fetch_underlying_stock_trade("SPY")

        assert call_count["value"] == 2
        assert first["request_metadata"]["cache_hit"] is False
        assert second["request_metadata"]["cache_hit"] is False
        assert second["request_metadata"]["cache_miss"] is True
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_fetch_underlying_trade_bypasses_cache_for_invalid_inputs(monkeypatch):
    workspace_tmp_dir = _workspace_tmp_dir()
    call_count = {"value": 0}

    def fake_get(*args, **kwargs):
        call_count["value"] += 1
        return _FakeResponse(
            200,
            {
                "trades": {
                    "": {
                        "p": 100.0,
                    }
                }
            },
        )

    monkeypatch.setenv("CACHE_DIR", str(workspace_tmp_dir / "cache"))
    monkeypatch.setenv("PROVIDER_MEMORY_CACHE_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_UNDERLYING_CACHE_TTL_SECONDS", "60")
    monkeypatch.setattr(data_provider.requests, "get", fake_get)
    data_provider._clear_in_memory_cache()

    try:
        first = fetch_underlying_stock_trade("")
        second = fetch_underlying_stock_trade("")

        assert call_count["value"] == 2
        assert first["request_metadata"]["cache_hit"] is False
        assert second["request_metadata"]["cache_hit"] is False
        assert first["request_metadata"]["cache_key"] is None
        assert second["request_metadata"]["cache_key"] is None
    finally:
        data_provider._clear_in_memory_cache()
        shutil.rmtree(workspace_tmp_dir, ignore_errors=True)


def test_get_alpaca_market_data_reuses_ticker_provider_cache(monkeypatch):
    data_provider._clear_in_memory_cache()
    call_counts = {
        "discover": 0,
        "snapshots": 0,
        "underlying": 0,
        "normalize": 0,
    }

    monkeypatch.setenv("PROVIDER_MEMORY_CACHE_ENABLED", "true")
    monkeypatch.setenv("PROVIDER_TICKER_DATA_CACHE_TTL_SECONDS", "60")

    def fake_discover(*args, **kwargs):
        call_counts["discover"] += 1
        return {
            "contracts": [{"symbol": "SPY250117P00450000"}],
            "chosen_expiration": "2030-01-17",
            "chosen_dte": 30,
            "request_metadata": {
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 1,
                "duration_ms": 40.0,
                "retry_count": 0,
                "retry_exhausted": False,
                "retry_delay_ms": 0.0,
            },
        }

    def fake_snapshots(*args, **kwargs):
        call_counts["snapshots"] += 1
        return {
            "snapshots": {"SPY250117P00450000": {}},
            "request_metadata": {
                "cache_hits": 0,
                "cache_misses": 1,
                "provider_call_count": 1,
                "duration_ms": 25.0,
                "retry_count": 0,
                "retry_exhausted_count": 0,
                "retry_delay_ms": 0.0,
                "estimated_saved_duration_ms": 0.0,
            },
        }

    def fake_underlying(*args, **kwargs):
        call_counts["underlying"] += 1
        return {
            "trade": {"p": 501.0},
            "request_metadata": {
                "cache_hit": False,
                "cache_miss": True,
                "provider_call_count": 1,
                "duration_ms": 15.0,
                "retry_count": 0,
                "retry_exhausted": False,
                "retry_delay_ms": 0.0,
                "estimated_saved_duration_ms": 0.0,
            },
        }

    def fake_normalize(*args, **kwargs):
        call_counts["normalize"] += 1
        return {
            "underlying_price": 501.0,
            "expiration_date": "2030-01-17",
            "DTE": 30,
            "contracts": [{"symbol": "SPY250117P00450000", "delta": -0.3, "bid": 1.0, "ask": 1.1, "strike": 450.0, "type": "put"}],
            "provider_diagnostics": {"ticker": "SPY", "degraded": False},
        }

    monkeypatch.setattr(data_provider, "discover_option_contracts_for_window", fake_discover)
    monkeypatch.setattr(data_provider, "fetch_option_snapshots_for_symbols", fake_snapshots)
    monkeypatch.setattr(data_provider, "fetch_underlying_stock_trade", fake_underlying)
    monkeypatch.setattr(data_provider, "normalize_discovered_contracts", fake_normalize)

    try:
        first = data_provider.get_alpaca_market_data(["SPY"], dte_min=20, dte_max=35)
        second = data_provider.get_alpaca_market_data(["SPY"], dte_min=20, dte_max=35)

        assert call_counts == {"discover": 1, "snapshots": 1, "underlying": 1, "normalize": 1}
        assert first["cache"]["ticker_data"]["misses"] == 1
        assert second["cache"]["ticker_data"]["hits"] == 1
        assert first["performance"]["total_provider_calls"] == 3
        assert first["performance"]["average_provider_latency_ms"] == pytest.approx(26.67, abs=0.01)
        assert first["ticker_diagnostics"][0]["provider_duration_ms"] == pytest.approx(80.0, abs=0.01)
        assert second["ticker_diagnostics"][0]["cache_hit"] is True
        assert second["ticker_diagnostics"][0]["provider_duration_ms"] == 0.0
        assert second["performance"]["provider_call_reduction_count"] >= 1
    finally:
        data_provider._clear_in_memory_cache()