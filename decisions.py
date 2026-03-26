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


def classify_spread(spread):
    if spread is None:
        return None

    pop = spread["POP"]
    ror = spread["ROR"]

    # Execution-quality gate: reject low-liquidity spreads early
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
            "and open interest thresholds."
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