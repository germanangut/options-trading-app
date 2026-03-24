DELTA_TOLERANCE = 0.03


def get_bid_ask_spread(contract):
    return contract["ask"] - contract["bid"]


def select_leg(contracts, target_delta, option_type):
    eligible = []

    for contract in contracts:
        if contract["type"] != option_type:
            continue

        if "delta" not in contract or contract["delta"] is None:
            continue

        if abs(contract["delta"] - target_delta) <= DELTA_TOLERANCE:
            eligible.append(contract)

    if not eligible:
        return None

    eligible.sort(
        key=lambda contract: (
            abs(contract["delta"] - target_delta),
            get_bid_ask_spread(contract),
        )
    )

    return eligible[0]