"""Unit tests for delta_neutral_service.py (PU-15B.5)."""

from __future__ import annotations

from backend.services.delta_neutral_service import generate_delta_neutral_exploration


def bull_put_trade(
    *,
    underlying: float = 191.0,
    short_strike: float = 180.0,
    long_strike: float = 175.0,
    net_credit: float = 1.45,
    short_delta: float | None = -0.25,
    long_delta: float | None = -0.10,
) -> dict:
    return {
        "trade_id": "trade_1",
        "ticker": "AAPL",
        "strategy_type": "bull_put_spread",
        "underlying_price": underlying,
        "short_strike": short_strike,
        "long_strike": long_strike,
        "net_credit": net_credit,
        "short_delta": short_delta,
        "long_delta": long_delta,
        "expiration_date": "2026-05-15",
    }


def bear_call_trade(
    *,
    underlying: float = 191.0,
    short_strike: float = 205.0,
    long_strike: float = 210.0,
    net_credit: float = 1.20,
    short_delta: float | None = 0.25,
    long_delta: float | None = 0.10,
) -> dict:
    return {
        "trade_id": "trade_2",
        "ticker": "AAPL",
        "strategy_type": "bear_call_spread",
        "underlying_price": underlying,
        "short_strike": short_strike,
        "long_strike": long_strike,
        "net_credit": net_credit,
        "short_delta": short_delta,
        "long_delta": long_delta,
        "expiration_date": "2026-05-15",
    }


class TestNetDeltaCalculation:
    def test_bull_put_net_delta_formula(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(short_delta=-0.25, long_delta=-0.10),
            scan_id="s1",
            trade_id="t1",
        )
        # net_delta = -short_delta + long_delta => 0.25 + (-0.10) = 0.15
        assert round(result.baseline.net_delta, 4) == 0.15

    def test_bear_call_net_delta_formula(self) -> None:
        result = generate_delta_neutral_exploration(
            bear_call_trade(short_delta=0.25, long_delta=0.10),
            scan_id="s1",
            trade_id="t1",
        )
        # net_delta = -0.25 + 0.10 = -0.15
        assert round(result.baseline.net_delta, 4) == -0.15


class TestCandidateGeneration:
    def test_bull_put_candidate_available_with_delta_reduction(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.neutral_candidate_available is True
        assert result.neutral_candidate is not None
        assert abs(result.neutral_candidate.net_delta) < abs(result.baseline.net_delta)
        assert result.comparison is not None
        assert result.comparison.delta_reduction > 0

    def test_bear_call_candidate_available_with_delta_reduction(self) -> None:
        result = generate_delta_neutral_exploration(
            bear_call_trade(),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.neutral_candidate_available is True
        assert result.neutral_candidate is not None
        assert abs(result.neutral_candidate.net_delta) < abs(result.baseline.net_delta)
        assert result.comparison is not None
        assert result.comparison.delta_reduction > 0

    def test_candidate_has_payoff_when_available(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.neutral_candidate is not None
        assert result.neutral_candidate.payoff is not None
        assert len(result.neutral_candidate.payoff.payoff_points) > 0


class TestUnavailableStates:
    def test_missing_leg_delta_returns_unavailable(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(short_delta=None, long_delta=-0.1),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.neutral_candidate_available is False
        assert result.neutral_candidate is None
        assert result.unavailable_reason is not None
        assert "deltas" in result.unavailable_reason.lower()

    def test_unsupported_strategy_returns_unavailable(self) -> None:
        trade = {
            "trade_id": "trade_x",
            "ticker": "AAPL",
            "strategy_type": "iron_condor",
            "underlying_price": 191.0,
            "short_strike": 180.0,
            "long_strike": 175.0,
            "net_credit": 1.0,
            "short_delta": -0.2,
            "long_delta": -0.1,
        }
        result = generate_delta_neutral_exploration(trade, scan_id="s1", trade_id="t1")
        assert result.neutral_candidate_available is False
        assert result.unavailable_reason is not None


class TestComparisonPayload:
    def test_comparison_fields_present(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.comparison is not None
        assert result.comparison.delta_reduction >= 0
        assert result.comparison.delta_reduction_pct >= 0
        assert len(result.comparison.summary) > 0

    def test_limitation_note_present_for_approximation(self) -> None:
        result = generate_delta_neutral_exploration(
            bull_put_trade(),
            scan_id="s1",
            trade_id="t1",
        )
        assert result.limitation_note is not None
        assert "approximation" in result.limitation_note.lower()
