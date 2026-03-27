POP_THRESHOLD = 60.0
ROR_THRESHOLD = 20.0

POP_NEAR_MISS_MIN = 54.0
ROR_NEAR_MISS_MIN = 18.0

MIN_OPEN_INTEREST = 50

from history_reader import get_consistency_scores


def compute_consistency_bonus(spread):
    ticker_scores, top_scores = get_consistency_scores()

    ticker = spread.get("ticker")

    ticker_count = ticker_scores.get(ticker, 0)
    top_count = top_scores.get(ticker, 0)

    # NEW: normalized + capped bonus
    raw_bonus = (ticker_count * 0.2) + (top_count * 0.5)
    bonus = min(10, raw_bonus)

    return bonus

def has_min_open_interest(spread):
    if spread is None:
        return False

    short_oi = spread.get("short_open_interest", 0) or 0
    long_oi = spread.get("long_open_interest", 0) or 0

    return short_oi >= MIN_OPEN_INTEREST and long_oi >= MIN_OPEN_INTEREST


def has_strike_sanity(spread):
    if spread is None:
        return False

    strategy_type = spread.get("strategy_type")
    underlying_price = spread.get("underlying_price")
    short_strike = spread.get("short_strike")
    long_strike = spread.get("long_strike")

    if underlying_price is None or short_strike is None or long_strike is None:
        return False

    if strategy_type == "bull put spread":
        return short_strike < underlying_price and long_strike < short_strike

    if strategy_type == "bear call spread":
        return short_strike > underlying_price and long_strike > short_strike

    return False


def classify_spread(spread):
    if spread is None:
        return None

    pop = spread["POP"]
    ror = spread["ROR"]

    if not has_min_open_interest(spread):
        spread["label"] = "Rejected"
        spread["status_reason"] = (
            f"Rejected because one or both legs failed the minimum open interest "
            f"requirement of {MIN_OPEN_INTEREST}."
        )
        spread["explanation"] = (
            "This spread was rejected due to insufficient open interest on one or both legs."
        )
        return spread

    if not has_strike_sanity(spread):
        spread["label"] = "Rejected"
        spread["status_reason"] = (
            "Rejected because the strike placement is not directionally consistent "
            "with the underlying price for this spread type."
        )
        spread["explanation"] = (
            "This spread was rejected because its strikes do not make market sense "
            "relative to the underlying price."
        )
        return spread

    qualifies = pop >= POP_THRESHOLD and ror >= ROR_THRESHOLD
    near_miss = (
        (POP_NEAR_MISS_MIN <= pop < POP_THRESHOLD)
        or (ROR_NEAR_MISS_MIN <= ror < ROR_THRESHOLD)
    )

    if qualifies:
        spread["label"] = "High Quality"
        # Apply consistency bonus
        bonus = compute_consistency_bonus(spread)
        spread["consistency_bonus"] = round(bonus, 2)
        spread["adjusted_score"] = round(spread["score"] + bonus, 2)
        spread["status_reason"] = (
            f"Qualified because POP ({pop}) met or exceeded {POP_THRESHOLD} "
            f"and ROR ({ror}) met or exceeded {ROR_THRESHOLD}."
        )
        spread["explanation"] = (
            "This spread satisfies the minimum probability of profit, return on risk, "
            "open interest, and strike sanity thresholds."
        )
    elif near_miss:
        spread["label"] = "Near Miss"
        if pop < POP_THRESHOLD:
            spread["status_reason"] = (
                f"Near Miss because POP ({pop}) was below the required {POP_THRESHOLD}."
            )
        else:
            spread["status_reason"] = (
                f"Near Miss because ROR ({ror}) was below the required {ROR_THRESHOLD}."
            )
        spread["explanation"] = (
            "This spread came close to qualification but missed at least one required threshold."
        )
    else:
        spread["label"] = "Rejected"
        spread["status_reason"] = (
            "Rejected because the spread did not meet qualification thresholds and "
            "was not close enough to count as a near miss."
        )
        spread["explanation"] = (
            "This spread does not meet the minimum requirements for the strategy."
        )

    return spread