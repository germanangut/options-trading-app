import json
from pathlib import Path
from datetime import datetime

HISTORY_DIR = Path(".history")
HISTORY_DIR.mkdir(exist_ok=True)

SCAN_FILE = HISTORY_DIR / "scans.jsonl"

def save_scan(result):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": result.get("summary"),
        "qualified": result.get("qualified"),
    }

    with SCAN_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")