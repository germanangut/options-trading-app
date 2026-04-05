import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from settings import get_settings


def get_history_dir():
    history_dir = Path(get_settings().get("history_dir", ".history"))
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def ensure_history_dir():
    get_history_dir()


def get_history_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return get_history_dir() / f"run_{today}.jsonl"


def build_run_snapshot(filtered):
    return {
        "timestamp": datetime.now().isoformat(),
        "profile": filtered.get("profile"),
        "ticker_group": filtered.get("ticker_group"),
        "execution_time": filtered.get("execution_time_seconds"),
        "alerts_count": len(filtered.get("alerts", [])),
        "qualified_count": len(filtered.get("qualified", [])),
        "top_overall": filtered.get("summary", {}).get("top_overall"),
        "alerts": filtered.get("alerts", []),
    }


def save_scan(filtered):
    ensure_history_dir()

    file_path = get_history_file()
    snapshot = build_run_snapshot(filtered)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")


def load_history_runs():
    file_path = get_history_file()

    if not os.path.exists(file_path):
        return []

    runs = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return runs


def compute_trend_insights():
    runs = load_history_runs()

    ticker_counter = Counter()
    strategy_counter = Counter()
    recurring_alert_counter = Counter()

    for run in runs:
        alerts = run.get("alerts", [])

        for alert in alerts:
            ticker = alert.get("ticker")
            strategy = alert.get("strategy_type")

            if ticker:
                ticker_counter[ticker] += 1

            if strategy:
                strategy_counter[strategy] += 1

            if ticker and strategy:
                recurring_alert_counter[f"{ticker} | {strategy}"] += 1

    return {
        "runs_analyzed": len(runs),
        "top_tickers": ticker_counter.most_common(5),
        "top_strategies": strategy_counter.most_common(5),
        "recurring_alerts": recurring_alert_counter.most_common(5),
    }

def compute_alert_stability():
    runs = load_history_runs()

    from collections import Counter

    alert_counter = Counter()

    for run in runs:
        alerts = run.get("alerts", [])
        for alert in alerts:
            ticker = alert.get("ticker")
            strategy = alert.get("strategy_type")

            if ticker and strategy:
                key = f"{ticker}|{strategy}"
                alert_counter[key] += 1

    stability_map = {}

    for key, count in alert_counter.items():
        if count >= 3:
            stability = "stable"
        elif count == 2:
            stability = "emerging"
        else:
            stability = "new"

        stability_map[key] = {
            "count": count,
            "stability": stability
        }

    return stability_map