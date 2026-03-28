def compute_pop(short_delta):
    return round((1 - abs(short_delta)) * 100, 1)


def compute_ror(net_credit, max_risk):
    if max_risk is None or max_risk <= 0:
        return 0.0

    return round((net_credit / max_risk) * 100, 1)


def compute_score_components(pop, ror):
    pop_component = pop * 0.6
    ror_component = ror * 0.4
    base_score = pop_component + ror_component

    return {
        "pop_component": round(pop_component, 2),
        "ror_component": round(ror_component, 2),
        "base_score": round(base_score, 2),
    }


def evaluate_spread(spread):
    if spread is None:
        return None

    short_delta = spread["short_delta"]
    net_credit = spread["net_credit"]
    max_risk = spread["max_risk"]

    pop = compute_pop(short_delta)
    ror = compute_ror(net_credit, max_risk)
    components = compute_score_components(pop, ror)

    spread["POP"] = pop
    spread["ROR"] = ror
    spread["score"] = components["base_score"]
    spread["score_breakdown"] = components

    return spread