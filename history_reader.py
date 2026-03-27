import json
from collections import Counter
from pathlib import Path

SCAN_FILE = Path(".history/scans.jsonl")


def load_scan_history():
    if not SCAN_FILE.exists():
        return []

    entries = []

    with SCAN_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return entries


def summarize_history():
    history = load_scan_history()

    ticker_counter = Counter()
    strategy_counter = Counter()
    top_overall_counter = Counter()

    for entry in history:
        qualified = entry.get("qualified", [])
        summary = entry.get("summary", {})

        for spread in qualified:
            ticker = spread.get("ticker")
            strategy = spread.get("strategy_type")

            if ticker:
                ticker_counter[ticker] += 1
            if strategy:
                strategy_counter[strategy] += 1

        top_overall = summary.get("top_overall")
        if top_overall:
            top_ticker = top_overall.get("ticker")
            if top_ticker:
                top_overall_counter[top_ticker] += 1

    return {
        "scan_count": len(history),
        "most_common_tickers": ticker_counter.most_common(),
        "most_common_strategies": strategy_counter.most_common(),
        "most_common_top_overall": top_overall_counter.most_common(),
    }

def get_consistency_scores():
    summary = summarize_history()

    ticker_scores = dict(summary["most_common_tickers"])
    top_overall_scores = dict(summary["most_common_top_overall"])

    return ticker_scores, top_overall_scores

if __name__ == "__main__":
    summary = summarize_history()
    print(json.dumps(summary, indent=2))