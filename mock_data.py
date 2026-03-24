MOCK_OPTIONS_DATA = {
    "SPY": {
        "underlying_price": 510.0,
        "expiration_date": "2026-04-24",
        "DTE": 35,
        "contracts": [
            {"strike": 500, "type": "put", "delta": -0.30, "bid": 2.20, "ask": 2.40, "open_interest": 1200},
            {"strike": 495, "type": "put", "delta": -0.20, "bid": 1.40, "ask": 1.55, "open_interest": 900},
            {"strike": 520, "type": "call", "delta": 0.30, "bid": 2.10, "ask": 2.30, "open_interest": 1100},
            {"strike": 525, "type": "call", "delta": 0.20, "bid": 1.30, "ask": 1.45, "open_interest": 850},
        ],
    },
    "QQQ": {
        "underlying_price": 438.0,
        "expiration_date": "2026-04-24",
        "DTE": 35,
        "contracts": [
            {"strike": 425, "type": "put", "delta": -0.30, "bid": 2.40, "ask": 2.55, "open_interest": 1000},
            {"strike": 420, "type": "put", "delta": -0.20, "bid": 1.15, "ask": 1.25, "open_interest": 950},
            {"strike": 448, "type": "call", "delta": 0.30, "bid": 2.35, "ask": 2.50, "open_interest": 980},
            {"strike": 453, "type": "call", "delta": 0.20, "bid": 1.10, "ask": 1.20, "open_interest": 870},
        ],
    },
    "AAPL": {
        "underlying_price": 212.0,
        "expiration_date": "2026-04-24",
        "DTE": 35,
        "contracts": [
            {"strike": 205, "type": "put", "delta": -0.30, "bid": 1.30, "ask": 1.45, "open_interest": 1500},
            {"strike": 200, "type": "put", "delta": -0.20, "bid": 0.95, "ask": 1.10, "open_interest": 1300},
            {"strike": 220, "type": "call", "delta": 0.30, "bid": 1.25, "ask": 1.40, "open_interest": 1400},
            {"strike": 225, "type": "call", "delta": 0.20, "bid": 0.90, "ask": 1.05, "open_interest": 1200},
        ],
    },
    "IWM": {
        "underlying_price": 205.0,
        "expiration_date": "2026-04-24",
        "DTE": 35,
        "contracts": [
            {"strike": 198, "type": "put", "delta": None, "bid": 1.90, "ask": 2.05, "open_interest": 700},
            {"strike": 193, "type": "put", "delta": -0.20, "bid": 1.05, "ask": 1.20, "open_interest": 650},
            {"strike": 212, "type": "call", "delta": 0.30, "bid": 1.85, "ask": 2.00, "open_interest": 720},
            {"strike": 217, "type": "call", "delta": 0.20, "bid": 1.00, "ask": 1.15, "open_interest": 680},
        ],
    },
    "MSFT": {
        "underlying_price": 468.0,
        "expiration_date": "2026-04-24",
        "DTE": 35,
        "contracts": [
            {"strike": 455, "type": "put", "delta": -0.31, "bid": 2.00, "ask": 2.18, "open_interest": 1000},
            {"strike": 454, "type": "put", "delta": -0.29, "bid": 2.02, "ask": 2.14, "open_interest": 980},
            {"strike": 450, "type": "put", "delta": -0.20, "bid": 1.10, "ask": 1.22, "open_interest": 900},
            {"strike": 480, "type": "call", "delta": 0.31, "bid": 1.95, "ask": 2.10, "open_interest": 970},
            {"strike": 481, "type": "call", "delta": 0.29, "bid": 1.96, "ask": 2.06, "open_interest": 960},
            {"strike": 485, "type": "call", "delta": 0.20, "bid": 1.05, "ask": 1.15, "open_interest": 910},
        ],
    },
}