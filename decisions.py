from history_reader import get_consistency_scores


POP_THRESHOLD = 60.0
ROR_THRESHOLD = 20.0

POP_NEAR_MISS_MIN = 54.0
ROR_NEAR_MISS_MIN = 18.0

MIN_OPEN_INTEREST = 50


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


def get_price_context_warning(spread):
    if spread is None:
        return False, None

    strategy_type = spread.get("strategy_type")
    underlying_price = spread.get("underlying_price")
    short_strike = spread.get("short_strike")
    long_strike = spread.get("long_strike")

    if underlying_price is None or short_strike is None or long_strike is None:
        return True, "Underlying price is missing, so strike context could not be verified."

    if strategy_type == "bull put spread":
        if not (short_strike < underlying_price and long_strike < underlying_price):
            return True, (
                "Underlying price may be unreliable because bull put strikes do not appear below spot."
            )

    if strategy_type == "bear call spread":
        if not (short_strike > underlying_price and long_strike > underlying_price):
            return True, (
                "Underlying price may be unreliable because bear call strikes do not appear above spot."
            )

    return False, None


def compute_consistency_bonus(spread):
    ticker_scores, top_scores = get_consistency_scores()

    ticker = spread.get("ticker")

    ticker_count = ticker_scores.get(ticker, 0)
    top_count = top_scores.get(ticker, 0)

    raw_bonus = (ticker_count * 0.2) + (top_count * 0.5)
    bonus = min(10, raw_bonus)

    return bonus


def compute_penalties(spread):
    """
    Soft penalties only.
    They reduce ranking attractiveness without rejecting the spread.
    """
    short_oi = spread.get("short_open_interest", 0) or 0
    long_oi = spread.get("long_open_interest", 0) or 0
    spread_width = spread.get("spread_width", 0) or 0

    liquidity_penalty = 0.0
    width_penalty = 0.0
    volatility_penalty = compute_volatility_penalty(spread)

    # Soft liquidity penalty
    min_leg_oi = min(short_oi, long_oi)
    if min_leg_oi < 100:
        liquidity_penalty = 2.0
    elif min_leg_oi < 200:
        liquidity_penalty = 1.0

    # Soft width penalty
    if spread_width > 20:
        width_penalty = 2.0
    elif spread_width > 10:
        width_penalty = 1.0

    total_penalty = liquidity_penalty + width_penalty + volatility_penalty

    return {
        "liquidity_penalty": round(liquidity_penalty, 2),
        "width_penalty": round(width_penalty, 2),
        "volatility_penalty": round(volatility_penalty, 2),
        "total_penalty": round(total_penalty, 2),
    }

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

    bonus = compute_consistency_bonus(spread)
    volatility_boost = compute_volatility_boost(spread)
    penalties = compute_penalties(spread)

    spread["consistency_bonus"] = round(bonus, 2)
    spread["volatility_boost"] = round(volatility_boost, 2)
    spread["penalties"] = penalties

    adjusted_score = (
        spread["score"]
        + bonus
        + volatility_boost
        - penalties["total_penalty"]
    )
    spread["adjusted_score"] = round(adjusted_score, 2)
    spread["penalties"] = penalties

    adjusted_score = spread["score"] + bonus - penalties["total_penalty"]
    spread["adjusted_score"] = round(adjusted_score, 2)

    if "score_breakdown" in spread:
        spread["score_breakdown"]["consistency_bonus"] = round(bonus, 2)
        spread["score_breakdown"]["volatility_boost"] = round(volatility_boost, 2)
        spread["score_breakdown"]["liquidity_penalty"] = penalties["liquidity_penalty"]
        spread["score_breakdown"]["width_penalty"] = penalties["width_penalty"]
        spread["score_breakdown"]["volatility_penalty"] = penalties["volatility_penalty"]
        spread["score_breakdown"]["total_penalty"] = penalties["total_penalty"]
        spread["score_breakdown"]["adjusted_score"] = spread["adjusted_score"]
            
    warning_flag, warning_reason = get_price_context_warning(spread)
    spread["price_context_warning"] = warning_flag
    spread["price_context_reason"] = warning_reason
    spread["decision_summary"] = build_decision_summary(spread)

    return spread

def compute_volatility_penalty(spread):
    volatility_context = spread.get("volatility_context")

    if volatility_context == "rich_premium":
        return 0.0
    if volatility_context == "balanced_premium":
        return 0.5
    return 2.0

def compute_volatility_boost(spread):

    volatility_context = spread.get("volatility_context")

    if volatility_context == "rich_premium":
        return 1.0

    return 0.0


def build_decision_summary(spread):
    if spread is None:
        return None

    label = spread.get("label")
    pop = spread.get("POP")
    ror = spread.get("ROR")
    volatility_context = spread.get("volatility_context")
    penalties = spread.get("penalties", {})

    penalty_parts = []
    if penalties.get("liquidity_penalty", 0) > 0:
        penalty_parts.append("liquidity friction")
    if penalties.get("width_penalty", 0) > 0:
        penalty_parts.append("wide spread structure")
    if penalties.get("volatility_penalty", 0) > 0:
        penalty_parts.append("non-rich premium")

    if not penalty_parts:
        friction_text = "low execution friction"
    else:
        friction_text = "some execution friction from " + ", ".join(penalty_parts)

    if label == "High Quality":
        return (
            f"High quality because it combines POP {pop}, ROR {ror}, "
            f"{volatility_context.replace('_', ' ')}, and {friction_text}."
        )

    if label == "Near Miss":
        return (
            f"Near miss because it showed some attractive traits, including "
            f"{volatility_context.replace('_', ' ')}, but did not fully meet the scoring thresholds."
        )

    return (
        f"Rejected because the trade did not meet the minimum quality bar, "
        f"despite {volatility_context.replace('_', ' ') if volatility_context else 'its current setup'}."
    )