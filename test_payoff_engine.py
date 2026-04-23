from __future__ import annotations

from backend.contracts.payoff_models import PayoffInput
from backend.services.payoff_engine import (
    calculate_payoff,
    generate_price_grid,
    payoff_input_from_ticket,
    payoff_input_from_trade,
)


def test_generate_price_grid_is_deterministic_and_odd_count() -> None:
    grid_one = generate_price_grid(
        strategy_key="bull_put_spread",
        underlying_price_reference=100.0,
        short_strike=95.0,
        long_strike=90.0,
        net_credit=1.2,
        point_count=40,
    )
    grid_two = generate_price_grid(
        strategy_key="bull_put_spread",
        underlying_price_reference=100.0,
        short_strike=95.0,
        long_strike=90.0,
        net_credit=1.2,
        point_count=40,
    )

    assert grid_one == grid_two
    assert len(grid_one) % 2 == 1
    assert grid_one[0] > 0
    assert grid_one[-1] > grid_one[0]


def test_bull_put_spread_payoff_shape() -> None:
    data = PayoffInput(
        strategy_key="bull_put_spread",
        ticker="XYZ",
        underlying_price_reference=100.0,
        short_strike=95.0,
        long_strike=90.0,
        net_credit=1.5,
        quantity=1,
    )

    analysis = calculate_payoff(data, point_count=31)

    assert analysis.max_profit == 150.0
    assert analysis.max_loss == 350.0
    assert analysis.breakeven_low == 93.5
    assert analysis.breakeven_high is None
    assert max(point.expiration_payoff for point in analysis.payoff_points) == 150.0
    assert min(point.expiration_payoff for point in analysis.payoff_points) == -350.0

    sorted_points = sorted(analysis.payoff_points, key=lambda point: point.underlying_price)
    sorted_payoffs = [point.expiration_payoff for point in sorted_points]
    assert sorted_payoffs == sorted(sorted_payoffs)


def test_bear_call_spread_payoff_formula_at_key_prices() -> None:
    data = PayoffInput(
        strategy_key="bear_call_spread",
        ticker="ABC",
        underlying_price_reference=100.0,
        short_strike=105.0,
        long_strike=110.0,
        net_credit=1.0,
        quantity=2,
    )

    analysis = calculate_payoff(data, point_count=9)

    assert analysis.max_profit == 200.0
    assert analysis.max_loss == 800.0
    assert analysis.breakeven_low is None
    assert analysis.breakeven_high == 106.0
    assert analysis.profit_zone == "Underlying <= 105.00"
    assert analysis.loss_zone == "Underlying >= 110.00"
    assert max(point.expiration_payoff for point in analysis.payoff_points) == 200.0
    assert min(point.expiration_payoff for point in analysis.payoff_points) == -800.0

    sorted_points = sorted(analysis.payoff_points, key=lambda point: point.underlying_price)
    sorted_payoffs = [point.expiration_payoff for point in sorted_points]
    assert sorted_payoffs == sorted(sorted_payoffs, reverse=True)


def test_unsupported_strategy_raises() -> None:
    data = PayoffInput(
        strategy_key="iron_condor",
        ticker="XYZ",
        underlying_price_reference=100.0,
        short_strike=105.0,
        long_strike=100.0,
        net_credit=1.2,
        quantity=1,
    )

    try:
        calculate_payoff(data)
    except ValueError as exc:
        assert "Unsupported payoff strategy" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported strategy")


def test_equal_strikes_raise() -> None:
    data = PayoffInput(
        strategy_key="bull_put_spread",
        ticker="XYZ",
        underlying_price_reference=100.0,
        short_strike=100.0,
        long_strike=100.0,
        net_credit=1.2,
        quantity=1,
    )

    try:
        calculate_payoff(data)
    except ValueError as exc:
        assert "must be different" in str(exc)
    else:
        raise AssertionError("Expected ValueError for equal strikes")


def test_max_loss_is_clamped_to_zero_for_overwide_credit() -> None:
    data = PayoffInput(
        strategy_key="bull_put_spread",
        ticker="XYZ",
        underlying_price_reference=100.0,
        short_strike=100.0,
        long_strike=95.0,
        net_credit=6.0,
        quantity=1,
    )

    analysis = calculate_payoff(data)

    assert analysis.max_loss == 0.0


def test_trade_input_normalizes_strategy_aliases() -> None:
    trade = {
        "strategy_type": "Bull Put",
        "ticker": "aapl",
        "short_strike": 180,
        "long_strike": 175,
        "net_credit": 1.45,
        "underlying_price": 191.2,
    }

    payoff_input = payoff_input_from_trade(trade)

    assert payoff_input.strategy_key == "bull_put_spread"
    assert payoff_input.ticker == "AAPL"


def test_ticket_input_rejects_invalid_quantity() -> None:
    ticket = {
        "strategy_key": "bear_call_spread",
        "ticker": "msft",
        "short_strike": 480,
        "long_strike": 485,
        "net_credit_estimate": 1.0,
        "underlying_price_at_creation": 468,
        "quantity": "not-a-number",
    }

    try:
        payoff_input_from_ticket(ticket)
    except ValueError as exc:
        assert "Invalid integer field 'quantity'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid quantity")
