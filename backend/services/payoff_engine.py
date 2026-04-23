from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.contracts.payoff_models import (
    SUPPORTED_PAYOFF_STRATEGIES,
    PayoffAnalysis,
    PayoffInput,
    PayoffPoint,
)


def _clamp_positive(value: float, *, floor: float = 0.01) -> float:
    return value if value > floor else floor


def _normalize_strategy_key(value: str) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    alias_map = {
        "bull_put_spread": "bull_put_spread",
        "bull_put": "bull_put_spread",
        "bear_call_spread": "bear_call_spread",
        "bear_call": "bear_call_spread",
    }
    return alias_map.get(normalized, normalized)


def _validate_input(data: PayoffInput) -> None:
    if data.strategy_key not in SUPPORTED_PAYOFF_STRATEGIES:
        raise ValueError(
            f"Unsupported payoff strategy '{data.strategy_key}'. "
            f"Supported strategies: {', '.join(SUPPORTED_PAYOFF_STRATEGIES)}."
        )

    if data.quantity < 1:
        raise ValueError("quantity must be at least 1.")

    if data.short_strike <= 0 or data.long_strike <= 0:
        raise ValueError("short_strike and long_strike must be greater than zero.")

    if data.short_strike == data.long_strike:
        raise ValueError("short_strike and long_strike must be different.")

    if data.net_credit < 0:
        raise ValueError("net_credit must be non-negative.")



def _normalize_input(data: PayoffInput) -> PayoffInput:
    if data.strategy_key == "bull_put_spread":
        short_strike = max(data.short_strike, data.long_strike)
        long_strike = min(data.short_strike, data.long_strike)
    elif data.strategy_key == "bear_call_spread":
        short_strike = min(data.short_strike, data.long_strike)
        long_strike = max(data.short_strike, data.long_strike)
    else:
        short_strike = data.short_strike
        long_strike = data.long_strike

    return PayoffInput(
        strategy_key=data.strategy_key,
        ticker=data.ticker,
        underlying_price_reference=data.underlying_price_reference,
        short_strike=short_strike,
        long_strike=long_strike,
        net_credit=data.net_credit,
        quantity=data.quantity,
    )


def _to_float(value: Any, *, field_name: str, default: float | None = None) -> float:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"Missing required numeric field '{field_name}'.")

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric field '{field_name}'.") from exc


def _to_int(value: Any, *, field_name: str, default: int | None = None) -> int:
    if value is None or value == "":
        if default is not None:
            return default
        raise ValueError(f"Missing required integer field '{field_name}'.")

    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer field '{field_name}'.") from exc


def generate_price_grid(
    *,
    strategy_key: str,
    underlying_price_reference: float,
    short_strike: float,
    long_strike: float,
    net_credit: float,
    point_count: int = 41,
) -> list[float]:
    if point_count < 5:
        raise ValueError("point_count must be at least 5.")

    if point_count % 2 == 0:
        point_count += 1

    width = abs(short_strike - long_strike)
    breakeven = short_strike - net_credit if strategy_key == "bull_put_spread" else short_strike + net_credit

    anchor_low = min(long_strike, short_strike, underlying_price_reference, breakeven)
    anchor_high = max(long_strike, short_strike, underlying_price_reference, breakeven)

    base_span = max(anchor_high - anchor_low, width * 4, max(underlying_price_reference * 0.3, 10.0))
    lower_bound = _clamp_positive(anchor_low - base_span * 0.6)
    upper_bound = anchor_high + base_span * 0.6

    step = (upper_bound - lower_bound) / (point_count - 1)
    return [round(lower_bound + step * index, 4) for index in range(point_count)]


def _bull_put_spread_payoff_per_share(
    underlying_price: float,
    *,
    short_strike: float,
    long_strike: float,
    net_credit: float,
) -> float:
    short_put = -max(short_strike - underlying_price, 0.0)
    long_put = max(long_strike - underlying_price, 0.0)
    return net_credit + short_put + long_put


def _bear_call_spread_payoff_per_share(
    underlying_price: float,
    *,
    short_strike: float,
    long_strike: float,
    net_credit: float,
) -> float:
    short_call = -max(underlying_price - short_strike, 0.0)
    long_call = max(underlying_price - long_strike, 0.0)
    return net_credit + short_call + long_call


def calculate_payoff(data: PayoffInput, *, point_count: int = 41) -> PayoffAnalysis:
    normalized_data = _normalize_input(data)
    _validate_input(normalized_data)

    spread_width = abs(normalized_data.short_strike - normalized_data.long_strike)
    contract_multiplier = 100 * normalized_data.quantity
    max_profit = round(normalized_data.net_credit * contract_multiplier, 2)
    max_loss = round(max(0.0, spread_width - normalized_data.net_credit) * contract_multiplier, 2)
    breakeven = round(
        normalized_data.short_strike - normalized_data.net_credit
        if normalized_data.strategy_key == "bull_put_spread"
        else normalized_data.short_strike + normalized_data.net_credit,
        4,
    )

    grid = generate_price_grid(
        strategy_key=normalized_data.strategy_key,
        underlying_price_reference=normalized_data.underlying_price_reference,
        short_strike=normalized_data.short_strike,
        long_strike=normalized_data.long_strike,
        net_credit=normalized_data.net_credit,
        point_count=point_count,
    )

    if normalized_data.strategy_key == "bull_put_spread":
        breakeven_low = breakeven
        breakeven_high = None
        points = [
            PayoffPoint(
                underlying_price=price,
                expiration_payoff=round(
                    _bull_put_spread_payoff_per_share(
                        price,
                        short_strike=normalized_data.short_strike,
                        long_strike=normalized_data.long_strike,
                        net_credit=normalized_data.net_credit,
                    ) * contract_multiplier,
                    2,
                ),
            )
            for price in grid
        ]
        profit_zone = f"Underlying >= {normalized_data.short_strike:.2f}"
        loss_zone = f"Underlying <= {normalized_data.long_strike:.2f}"
        summary = (
            "Bull put spread keeps full credit above the short strike, "
            "transitions through breakeven, and reaches max loss at or below the long strike."
        )
    else:
        breakeven_low = None
        breakeven_high = breakeven
        points = [
            PayoffPoint(
                underlying_price=price,
                expiration_payoff=round(
                    _bear_call_spread_payoff_per_share(
                        price,
                        short_strike=normalized_data.short_strike,
                        long_strike=normalized_data.long_strike,
                        net_credit=normalized_data.net_credit,
                    ) * contract_multiplier,
                    2,
                ),
            )
            for price in grid
        ]
        profit_zone = f"Underlying <= {normalized_data.short_strike:.2f}"
        loss_zone = f"Underlying >= {normalized_data.long_strike:.2f}"
        summary = (
            "Bear call spread keeps full credit below the short strike, "
            "transitions through breakeven, and reaches max loss at or above the long strike."
        )

    return PayoffAnalysis(
        strategy_key=normalized_data.strategy_key,
        ticker=normalized_data.ticker,
        quantity=normalized_data.quantity,
        underlying_price_reference=normalized_data.underlying_price_reference,
        short_strike=normalized_data.short_strike,
        long_strike=normalized_data.long_strike,
        net_credit=normalized_data.net_credit,
        spread_width=spread_width,
        max_profit=max_profit,
        max_loss=max_loss,
        breakeven_low=breakeven_low,
        breakeven_high=breakeven_high,
        profit_zone=profit_zone,
        loss_zone=loss_zone,
        expiration_summary=summary,
        price_grid=grid,
        payoff_points=points,
    )


def payoff_analysis_to_dict(analysis: PayoffAnalysis) -> dict[str, Any]:
    payload = asdict(analysis)
    payload["payoff_points"] = [asdict(point) for point in analysis.payoff_points]
    return payload


def payoff_input_from_trade(trade: dict[str, Any], *, quantity: int = 1) -> PayoffInput:
    strategy_key = _normalize_strategy_key(
        str(trade.get("strategy_key") or trade.get("strategy_type") or "").strip()
    )
    if not strategy_key:
        raise ValueError("Trade is missing strategy_type/strategy_key.")

    short_strike = _to_float(trade.get("short_strike"), field_name="short_strike")
    long_strike = _to_float(trade.get("long_strike"), field_name="long_strike")
    net_credit = _to_float(trade.get("net_credit"), field_name="net_credit", default=0.0)
    underlying_reference = _to_float(
        trade.get("underlying_price"),
        field_name="underlying_price",
        default=(short_strike + long_strike) / 2,
    )

    return PayoffInput(
        strategy_key=strategy_key,
        ticker=str(trade.get("ticker") or "").strip().upper() or None,
        underlying_price_reference=underlying_reference,
        short_strike=short_strike,
        long_strike=long_strike,
        net_credit=net_credit,
        quantity=quantity,
    )


def payoff_input_from_ticket(ticket: dict[str, Any]) -> PayoffInput:
    strategy_key = _normalize_strategy_key(str(ticket.get("strategy_key") or "").strip())
    if not strategy_key:
        raise ValueError("Ticket is missing strategy_key.")

    short_strike = _to_float(ticket.get("short_strike"), field_name="short_strike")
    long_strike = _to_float(ticket.get("long_strike"), field_name="long_strike")
    net_credit = _to_float(ticket.get("net_credit_estimate"), field_name="net_credit_estimate", default=0.0)
    underlying_reference = _to_float(
        ticket.get("underlying_price_at_creation"),
        field_name="underlying_price_at_creation",
        default=(short_strike + long_strike) / 2,
    )
    quantity = _to_int(ticket.get("quantity"), field_name="quantity", default=1)

    return PayoffInput(
        strategy_key=strategy_key,
        ticker=str(ticket.get("ticker") or "").strip().upper() or None,
        underlying_price_reference=underlying_reference,
        short_strike=short_strike,
        long_strike=long_strike,
        net_credit=net_credit,
        quantity=quantity,
    )
