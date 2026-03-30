DEFAULT_POP_WEIGHT = 0.6
DEFAULT_ROR_WEIGHT = 0.4


def compute_premium_to_width(net_credit, spread_width):
    if spread_width is None or spread_width <= 0:
        return 0.0
    return round(net_credit / spread_width, 4)


def classify_volatility_context(premium_to_width):
    if premium_to_width >= 0.30:
        return "rich_premium"
    if premium_to_width >= 0.20:
        return "balanced_premium"
    return "thin_premium"

def compute_pop(short_delta):
    return round((1 - abs(short_delta)) * 100, 1)


def compute_ror(net_credit, max_risk):
    if max_risk is None or max_risk <= 0:
        return 0.0

    return round((net_credit / max_risk) * 100, 1)


def normalize_weights(pop_weight=None, ror_weight=None):
    pop_weight = DEFAULT_POP_WEIGHT if pop_weight is None else pop_weight
    ror_weight = DEFAULT_ROR_WEIGHT if ror_weight is None else ror_weight

    total = pop_weight + ror_weight
    if total <= 0:
        return DEFAULT_POP_WEIGHT, DEFAULT_ROR_WEIGHT

    return pop_weight / total, ror_weight / total


def compute_score_components(pop, ror, pop_weight=None, ror_weight=None):
    pop_weight, ror_weight = normalize_weights(pop_weight, ror_weight)

    pop_component = pop * pop_weight
    ror_component = ror * ror_weight
    base_score = pop_component + ror_component

    return {
        "pop_weight": round(pop_weight, 4),
        "ror_weight": round(ror_weight, 4),
        "pop_component": round(pop_component, 2),
        "ror_component": round(ror_component, 2),
        "base_score": round(base_score, 2),
    }


def evaluate_spread(spread, pop_weight=None, ror_weight=None):
    if spread is None:
        return None

    short_delta = spread["short_delta"]
    net_credit = spread["net_credit"]
    max_risk = spread["max_risk"]

    pop = compute_pop(short_delta)
    ror = compute_ror(net_credit, max_risk)
    components = compute_score_components(pop, ror, pop_weight=pop_weight, ror_weight=ror_weight)

    premium_to_width = compute_premium_to_width(
        spread["net_credit"],
        spread["spread_width"]
    )

    volatility_context = classify_volatility_context(premium_to_width)

    spread["POP"] = pop
    spread["ROR"] = ror
    spread["score"] = components["base_score"]
    spread["score_breakdown"] = components
    spread["score_breakdown"]["premium_to_width"] = premium_to_width
    spread["score_breakdown"]["volatility_context"] = volatility_context
    spread["premium_to_width"] = premium_to_width
    spread["volatility_context"] = volatility_context

    return spread