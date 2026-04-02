import json
import os
from datetime import datetime


HISTORY_DIR = ".history"


def ensure_history_dir():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)


def get_history_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(HISTORY_DIR, f"run_{today}.jsonl")


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

    with open(file_path, "a") as f:
        f.write(json.dumps(snapshot) + "\n")