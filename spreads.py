def get_midpoint(contract):
    return (contract["bid"] + contract["ask"]) / 2


def build_spread(short_leg, long_leg, strategy_type, ticker, underlying_price, expiration_date, dte):
    if short_leg is None or long_leg is None:
        return None

    short_mid = get_midpoint(short_leg)
    long_mid = get_midpoint(long_leg)

    net_credit = short_mid - long_mid
    spread_width = abs(short_leg["strike"] - long_leg["strike"])
    max_risk = spread_width - net_credit

    return {
        "ticker": ticker,
        "underlying_price": underlying_price,
        "strategy_type": strategy_type,
        "expiration_date": expiration_date,
        "DTE": dte,
        "short_strike": short_leg["strike"],
        "long_strike": long_leg["strike"],
        "short_delta": short_leg["delta"],
        "long_delta": long_leg["delta"],
        "short_open_interest": short_leg.get("open_interest", 0),
        "long_open_interest": long_leg.get("open_interest", 0),
        "short_mid": round(short_mid, 3),
        "long_mid": round(long_mid, 3),
        "net_credit": round(net_credit, 3),
        "spread_width": round(spread_width, 3),
        "max_risk": round(max_risk, 3),
    }