import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from settings import get_settings


BASE_DIR = Path(__file__).resolve().parent
LEGACY_HISTORY_DIR_CANDIDATES = (
    BASE_DIR / "history",
    BASE_DIR / "docker-data" / "history",
)


def get_history_dir():
    history_dir = Path(get_settings().get("history_dir", ".history"))
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


def ensure_history_dir():
    get_history_dir()


def get_history_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return get_history_dir() / f"run_{today}.jsonl"


def _load_runs_from_file(file_path):
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


def _compact_signal_record(spread):
    if not isinstance(spread, dict) or not spread:
        return None

    return {
        "ticker": spread.get("ticker"),
        "strategy_type": spread.get("strategy_type"),
        "strategy_key": spread.get("strategy_key"),
        "strategy_label": spread.get("strategy_label"),
        "adjusted_score": spread.get("adjusted_score", spread.get("score")),
        "score": spread.get("score"),
        "POP": spread.get("POP"),
        "ROR": spread.get("ROR"),
        "label": spread.get("label"),
        "volatility_context": spread.get("volatility_context"),
        "status_reason": spread.get("status_reason"),
        "decision_summary": spread.get("decision_summary"),
    }


def get_available_history_files(include_fallback_dirs=False):
    directories = [get_history_dir()]

    if include_fallback_dirs:
        for candidate in LEGACY_HISTORY_DIR_CANDIDATES:
            if candidate not in directories:
                directories.append(candidate)

    history_files = []
    seen = set()

    for directory in directories:
        if not directory.exists():
            continue

        for file_path in sorted(directory.glob("run_*.jsonl")):
            resolved_path = str(file_path.resolve())
            if resolved_path in seen:
                continue

            seen.add(resolved_path)
            history_files.append(file_path)

    return history_files


def load_all_history_runs(include_fallback_dirs=True):
    runs = []

    for file_path in get_available_history_files(
        include_fallback_dirs=include_fallback_dirs
    ):
        runs.extend(_load_runs_from_file(file_path))

    runs.sort(key=lambda run: run.get("timestamp", ""))
    return runs


def build_run_snapshot(filtered):
    qualified = [
        compact_spread
        for compact_spread in (
            _compact_signal_record(spread)
            for spread in filtered.get("qualified", [])
        )
        if compact_spread
    ]

    return {
        "timestamp": datetime.now().isoformat(),
        "profile": filtered.get("profile"),
        "ticker_group": filtered.get("ticker_group"),
        "execution_time": filtered.get("execution_time_seconds"),
        "alerts_count": len(filtered.get("alerts", [])),
        "qualified_count": len(filtered.get("qualified", [])),
        "top_overall": _compact_signal_record(
            filtered.get("summary", {}).get("top_overall")
        ),
        "alerts": filtered.get("alerts", []),
        "qualified": qualified,
    }


def save_scan(filtered):
    ensure_history_dir()

    file_path = get_history_file()
    snapshot = build_run_snapshot(filtered)

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")


def load_history_runs():
    file_path = get_history_file()
    return _load_runs_from_file(file_path)


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


def _get_signal_entries_for_summary(run):
    qualified = [entry for entry in run.get("qualified", []) if isinstance(entry, dict)]
    if qualified:
        return qualified, "qualified"

    alerts = [entry for entry in run.get("alerts", []) if isinstance(entry, dict)]
    if alerts:
        return alerts, "alerts"

    top_overall = run.get("top_overall")
    if isinstance(top_overall, dict) and top_overall:
        return [top_overall], "top_overall"

    return [], None


def _build_average_summary(score_map, key_name, limit=5):
    rows = []

    for name, values in score_map.items():
        if not values:
            continue

        rows.append(
            {
                key_name: name,
                "average_adjusted_score": round(sum(values) / len(values), 2),
                "count": len(values),
            }
        )

    rows.sort(
        key=lambda row: (-row["count"], -row["average_adjusted_score"], row[key_name])
    )
    return rows[:limit]


def compute_historical_signal_quality_summary(limit=5):
    """Compute a lightweight historical summary of signal quality from stored runs."""
    runs = load_all_history_runs(include_fallback_dirs=True)

    ticker_counter = Counter()
    strategy_counter = Counter()
    label_counter = Counter()
    pattern_counter = Counter()
    source_counter = Counter()

    scores_by_ticker = defaultdict(list)
    scores_by_strategy = defaultdict(list)
    scores_by_pattern = defaultdict(list)

    signals_analyzed = 0

    for run in runs:
        signal_entries, source = _get_signal_entries_for_summary(run)
        if source:
            source_counter[source] += len(signal_entries)

        for signal in signal_entries:
            signals_analyzed += 1

            ticker = signal.get("ticker")
            strategy = (
                signal.get("strategy_label")
                or signal.get("strategy_type")
                or signal.get("strategy_key")
            )
            label = signal.get("label")
            adjusted_score = signal.get("adjusted_score")

            if ticker:
                ticker_counter[ticker] += 1

            if strategy:
                strategy_counter[strategy] += 1

            if label:
                label_counter[label] += 1

            if isinstance(adjusted_score, (int, float)):
                if ticker:
                    scores_by_ticker[ticker].append(float(adjusted_score))
                if strategy:
                    scores_by_strategy[strategy].append(float(adjusted_score))

            if ticker and strategy:
                pattern = f"{ticker} | {strategy}"
                pattern_counter[pattern] += 1
                if isinstance(adjusted_score, (int, float)):
                    scores_by_pattern[pattern].append(float(adjusted_score))

    recurring_patterns = []
    for pattern, count in pattern_counter.most_common():
        if count < 2:
            continue

        values = scores_by_pattern.get(pattern, [])
        recurring_patterns.append(
            {
                "pattern": pattern,
                "count": count,
                "average_adjusted_score": round(sum(values) / len(values), 2)
                if values
                else None,
            }
        )

        if len(recurring_patterns) >= limit:
            break

    return {
        "runs_analyzed": len(runs),
        "signals_analyzed": signals_analyzed,
        "data_sources": dict(source_counter),
        "most_frequent_qualified_tickers": [
            {"ticker": ticker, "count": count}
            for ticker, count in ticker_counter.most_common(limit)
        ],
        "most_frequent_qualified_strategies": [
            {"strategy": strategy, "count": count}
            for strategy, count in strategy_counter.most_common(limit)
        ],
        "average_adjusted_score_by_ticker": _build_average_summary(
            scores_by_ticker,
            "ticker",
            limit=limit,
        ),
        "average_adjusted_score_by_strategy": _build_average_summary(
            scores_by_strategy,
            "strategy",
            limit=limit,
        ),
        "recurring_high_quality_patterns": recurring_patterns,
        "label_distribution": [
            {"label": label, "count": count}
            for label, count in label_counter.most_common(limit)
        ],
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