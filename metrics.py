POP_WEIGHT = 0.60
ROR_WEIGHT = 0.40


def evaluate_spread(spread):
    if spread is None:
        return None

    short_delta = spread["short_delta"]
    max_risk = spread["max_risk"]
    net_credit = spread["net_credit"]

    if max_risk <= 0:
        return None

    pop = (1 - abs(short_delta)) * 100
    ror = (net_credit / max_risk) * 100
    score = (pop * POP_WEIGHT) + (ror * ROR_WEIGHT)

    spread["POP"] = round(pop, 1)
    spread["ROR"] = round(ror, 1)
    spread["score"] = round(score, 2)

    return spread