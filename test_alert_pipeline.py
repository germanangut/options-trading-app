from pathlib import Path

import data_provider
import decisions
import engine
from backend.contracts.scan_result import ScanRequest, build_scan_result
from decisions import classify_spread
from engine import apply_stability_boost, run_scan_engine
from output import build_alerts


def _force_mock_mode(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(data_provider, "ALPACA_API_KEY", None)
    monkeypatch.setattr(data_provider, "ALPACA_API_SECRET", None)
    monkeypatch.setenv("HISTORY_DIR", str(tmp_path / "history"))
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))


def _build_spread(volatility_context="rich_premium"):
    return {
        "ticker": "MSFT",
        "strategy_type": "bull put spread",
        "underlying_price": 100.0,
        "short_strike": 95.0,
        "long_strike": 90.0,
        "short_open_interest": 500,
        "long_open_interest": 500,
        "POP": 70.0,
        "ROR": 25.0,
        "score": 64.0,
        "score_breakdown": {},
        "volatility_context": volatility_context,
    }


def test_adjusted_score_preserves_volatility_boost(monkeypatch):
    monkeypatch.setattr(decisions, "get_consistency_scores", lambda: ({}, {}))

    spread = classify_spread(_build_spread(volatility_context="rich_premium"))

    assert spread is not None
    assert spread["volatility_boost"] == 1.0
    assert spread["stability_boost"] == 0.0
    assert spread["adjusted_score"] == 65.0


def test_adjusted_score_includes_stability_boost(monkeypatch):
    monkeypatch.setattr(decisions, "get_consistency_scores", lambda: ({}, {}))

    spread = classify_spread(_build_spread(volatility_context="rich_premium"))
    spread["stability_level"] = "stable"
    spread["stability_count"] = 3

    apply_stability_boost([spread])

    assert spread["stability_boost"] == 1.0
    assert spread["adjusted_score"] == 66.0
    assert spread["score_breakdown"]["adjusted_score"] == 66.0


def test_alert_consistency_gate_uses_stability_count_not_bonus():
    spread = {
        "ticker": "MSFT",
        "strategy_type": "bull put spread",
        "label": "High Quality",
        "adjusted_score": 72.0,
        "consistency_bonus": 10.0,
        "stability_count": 2,
        "volatility_context": "rich_premium",
    }

    assert build_alerts([spread], min_score=65, min_consistency=3) == []

    spread["stability_count"] = 3
    alerts = build_alerts([spread], min_score=65, min_consistency=3)

    assert len(alerts) == 1


def test_run_scan_engine_generates_alerts_after_post_enrichment_stability(monkeypatch, tmp_path: Path):
    _force_mock_mode(monkeypatch, tmp_path)

    monkeypatch.setattr(
        engine,
        "compute_alert_stability",
        lambda: {
            "MSFT|bull put spread": {"count": 2, "stability": "emerging"},
        },
    )

    raw_output = run_scan_engine(
        profile_name="balanced",
        group_name="tech",
        min_score=65,
        min_consistency=3,
        export_csv=False,
        persist_history=False,
    )

    alerts = raw_output["alerts"]

    assert any(
        trade.get("ticker") == "MSFT"
        and trade.get("strategy_type") == "bull put spread"
        for trade in alerts
    )

    alert = next(
        trade
        for trade in alerts
        if trade.get("ticker") == "MSFT"
        and trade.get("strategy_type") == "bull put spread"
    )

    assert alert["stability_count"] == 3
    assert alert["stability_level"] == "stable"
    assert alert["adjusted_score"] >= 65
    assert raw_output["alert_thresholds"]["consistency_field"] == "stability_count"
    assert raw_output["alert_thresholds"]["evaluation_stage"] == "post_enrichment"


def test_final_alert_counts_match_daily_summary(monkeypatch, tmp_path: Path):
    _force_mock_mode(monkeypatch, tmp_path)

    monkeypatch.setattr(
        engine,
        "compute_alert_stability",
        lambda: {
            "MSFT|bull put spread": {"count": 2, "stability": "emerging"},
        },
    )

    request = ScanRequest(profile="balanced", ticker_group="tech", min_score=65, min_consistency=3)
    raw_output = run_scan_engine(
        profile_name=request.profile,
        group_name=request.ticker_group,
        min_score=request.min_score,
        min_consistency=request.min_consistency,
        export_csv=False,
        persist_history=False,
    )
    scan_result = build_scan_result(raw_output, request, scan_id="scan_alert_test")

    assert len(raw_output["alerts"]) == 1
    assert scan_result["daily_summary"]["alerts_count"] == len(scan_result["alerts"])
    assert scan_result["daily_summary"]["stable_alert_count"] == 1
    assert scan_result["daily_summary"]["emerging_alert_count"] == 0
    assert scan_result["daily_summary"]["new_alert_count"] == 0


def test_balanced_profile_can_still_return_zero_alerts_consistently(monkeypatch, tmp_path: Path):
    _force_mock_mode(monkeypatch, tmp_path)
    monkeypatch.setattr(engine, "compute_alert_stability", lambda: {})

    request = ScanRequest(profile="balanced", ticker_group="tech", min_score=65, min_consistency=3)
    raw_output = run_scan_engine(
        profile_name=request.profile,
        group_name=request.ticker_group,
        min_score=request.min_score,
        min_consistency=request.min_consistency,
        export_csv=False,
        persist_history=False,
    )
    scan_result = build_scan_result(raw_output, request, scan_id="scan_no_alerts_test")

    assert raw_output["alerts"] == []
    assert scan_result["daily_summary"]["alerts_count"] == 0
    assert scan_result["daily_summary"]["stable_alert_count"] == 0
    assert scan_result["daily_summary"]["emerging_alert_count"] == 0
    assert scan_result["daily_summary"]["new_alert_count"] == 0


# ---------------------------------------------------------------------------
# Balanced default threshold calibration tests
# ---------------------------------------------------------------------------

def test_balanced_profile_defaults_are_calibrated():
    """Balanced profile must use the relaxed production defaults (min_score=55, min_consistency=1)."""
    from profiles import PROFILES
    balanced = PROFILES["balanced"]
    assert balanced["min_score"] == 55, (
        f"Balanced min_score should be 55, got {balanced['min_score']}"
    )
    assert balanced["min_consistency"] == 1, (
        f"Balanced min_consistency should be 1, got {balanced['min_consistency']}"
    )


def test_conservative_profile_remains_stricter_than_balanced():
    """Conservative must remain stricter than Balanced on both dimensions."""
    from profiles import PROFILES
    conservative = PROFILES["conservative"]
    balanced = PROFILES["balanced"]
    assert conservative["min_score"] >= balanced["min_score"], (
        "Conservative min_score must be >= Balanced min_score"
    )
    assert conservative["min_consistency"] >= balanced["min_consistency"], (
        "Conservative min_consistency must be >= Balanced min_consistency"
    )


def test_aggressive_profile_remains_at_most_as_strict_as_balanced():
    """Aggressive thresholds must be <= Balanced so profile ordering is preserved."""
    from profiles import PROFILES
    aggressive = PROFILES["aggressive"]
    balanced = PROFILES["balanced"]
    assert aggressive["min_score"] <= balanced["min_score"], (
        "Aggressive min_score must be <= Balanced min_score"
    )
    assert aggressive["min_consistency"] <= balanced["min_consistency"], (
        "Aggressive min_consistency must be <= Balanced min_consistency"
    )


def test_alert_count_does_not_regress_when_thresholds_overridden(monkeypatch, tmp_path: Path):
    """Overriding thresholds to strict values must still produce the expected alert count
    (no silent regression introduced by the recalibration)."""
    _force_mock_mode(monkeypatch, tmp_path)

    monkeypatch.setattr(
        engine,
        "compute_alert_stability",
        lambda: {
            "MSFT|bull put spread": {"count": 2, "stability": "emerging"},
        },
    )

    raw_output = run_scan_engine(
        profile_name="balanced",
        group_name="tech",
        min_score=65,
        min_consistency=3,
        export_csv=False,
        persist_history=False,
    )

    alerts = raw_output["alerts"]
    assert any(
        trade.get("ticker") == "MSFT" and trade.get("strategy_type") == "bull put spread"
        for trade in alerts
    ), "Overriding to min_score=65, min_consistency=3 must still surface the expected MSFT alert"