import csv
from pathlib import Path


EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

ALERTS_CSV_PATH = EXPORT_DIR / "alerts_latest.csv"


def export_alerts_to_csv(alerts, filepath=ALERTS_CSV_PATH):
    fieldnames = [
        "ticker",
        "strategy_type",
        "adjusted_score",
        "score",
        "POP",
        "ROR",
        "consistency_bonus",
        "liquidity_penalty",
        "width_penalty",
        "total_penalty",
        "short_strike",
        "long_strike",
        "underlying_price",
        "expiration_date",
        "DTE",
        "label",
        "status_reason",
    ]

    with filepath.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for alert in alerts:
            penalties = alert.get("penalties", {})
            writer.writerow(
                {
                    "ticker": alert.get("ticker"),
                    "strategy_type": alert.get("strategy_type"),
                    "adjusted_score": alert.get("adjusted_score"),
                    "score": alert.get("score"),
                    "POP": alert.get("POP"),
                    "ROR": alert.get("ROR"),
                    "consistency_bonus": alert.get("consistency_bonus"),
                    "liquidity_penalty": penalties.get("liquidity_penalty", 0.0),
                    "width_penalty": penalties.get("width_penalty", 0.0),
                    "total_penalty": penalties.get("total_penalty", 0.0),
                    "short_strike": alert.get("short_strike"),
                    "long_strike": alert.get("long_strike"),
                    "underlying_price": alert.get("underlying_price"),
                    "expiration_date": alert.get("expiration_date"),
                    "DTE": alert.get("DTE"),
                    "label": alert.get("label"),
                    "status_reason": alert.get("status_reason"),
                }
            )

    return str(filepath)
