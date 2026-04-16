import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from backend.services.scan_store import list_scan_results
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
        "stability_level": spread.get("stability_level"),
        "stability_count": spread.get("stability_count"),
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
    """Load history newest-first from canonical persisted scans when available.

    Persisted canonical scans are authoritative. Legacy JSONL files remain a
    compatibility-only fallback for older runs that predate repository-backed
    storage.
    """
    runs = []

    for scan_result in list_scan_results(newest_first=True):
        snapshot = _build_run_snapshot_from_scan_result(scan_result)
        if snapshot:
            runs.append(snapshot)

    if runs:
        return runs

    for file_path in get_available_history_files(
        include_fallback_dirs=include_fallback_dirs
    ):
        runs.extend(_load_runs_from_file(file_path))

    runs.sort(
        key=lambda run: (
            run.get("timestamp", ""),
            run.get("stored_at", ""),
            run.get("scan_id", ""),
            run.get("profile", ""),
            run.get("ticker_group", ""),
        ),
        reverse=True,
    )
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


def _build_run_snapshot_from_scan_result(scan_result):
    if not isinstance(scan_result, dict) or not scan_result:
        return None

    scan_metadata = scan_result.get("scan_metadata", {})
    storage_metadata = scan_result.get("storage_metadata", {})
    summary = scan_result.get("summary", {})
    qualified_trades = scan_result.get("qualified_trades", []) or []
    alerts = scan_result.get("alerts", []) or []

    return {
        "scan_id": scan_metadata.get("scan_id"),
        "timestamp": scan_metadata.get("generated_at"),
        "stored_at": storage_metadata.get("stored_at"),
        "profile": scan_metadata.get("profile"),
        "ticker_group": scan_metadata.get("ticker_group"),
        "execution_time": scan_metadata.get("execution_time_seconds"),
        "alerts_count": len(alerts),
        "qualified_count": len(qualified_trades),
        "top_overall": _compact_signal_record(summary.get("top_overall")),
        "alerts": [
            compact_alert
            for compact_alert in (
                _compact_signal_record(alert)
                for alert in alerts
            )
            if compact_alert
        ],
        "qualified": [
            compact_trade
            for compact_trade in (
                _compact_signal_record(trade)
                for trade in qualified_trades
            )
            if compact_trade
        ],
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


def _build_count_summary(counter, key_name, limit=5):
    return [
        {key_name: name, "count": count}
        for name, count in counter.most_common(limit)
    ]


def _compute_historical_intelligence_components(limit=5):
    runs = load_all_history_runs(include_fallback_dirs=True)

    ticker_counter = Counter()
    strategy_counter = Counter()
    label_counter = Counter()
    pattern_counter = Counter()
    source_counter = Counter()
    volatility_context_counter = Counter()
    stability_level_counter = Counter()

    scores_by_ticker = defaultdict(list)
    scores_by_strategy = defaultdict(list)
    scores_by_pattern = defaultdict(list)
    scores_by_volatility_context = defaultdict(list)
    scores_by_stability_level = defaultdict(list)

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
            volatility_context = signal.get("volatility_context")
            stability_level = signal.get("stability_level")

            if ticker:
                ticker_counter[ticker] += 1

            if strategy:
                strategy_counter[strategy] += 1

            if label:
                label_counter[label] += 1

            if volatility_context:
                volatility_context_counter[volatility_context] += 1

            if stability_level:
                stability_level_counter[stability_level] += 1

            if isinstance(adjusted_score, (int, float)):
                score_value = float(adjusted_score)

                if ticker:
                    scores_by_ticker[ticker].append(score_value)
                if strategy:
                    scores_by_strategy[strategy].append(score_value)
                if volatility_context:
                    scores_by_volatility_context[volatility_context].append(score_value)
                if stability_level:
                    scores_by_stability_level[stability_level].append(score_value)

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

    feature_summary = {
        "counts_by_volatility_context": _build_count_summary(
            volatility_context_counter,
            "volatility_context",
            limit=limit,
        ),
        "average_adjusted_score_by_volatility_context": _build_average_summary(
            scores_by_volatility_context,
            "volatility_context",
            limit=limit,
        ),
        "counts_by_stability_level": _build_count_summary(
            stability_level_counter,
            "stability_level",
            limit=limit,
        ),
        "average_adjusted_score_by_stability_level": _build_average_summary(
            scores_by_stability_level,
            "stability_level",
            limit=limit,
        ),
        "recurring_ticker_strategy_pairs": recurring_patterns,
        "average_adjusted_score_by_ticker_strategy_pair": _build_average_summary(
            scores_by_pattern,
            "pair",
            limit=limit,
        ),
    }

    metadata = {
        "runs_analyzed": len(runs),
        "signals_analyzed": signals_analyzed,
        "data_sources": dict(source_counter),
        "history_available": bool(runs),
        "signal_history_available": signals_analyzed > 0,
        "latest_run_timestamp": runs[0].get("timestamp") if runs else None,
    }

    signal_quality_summary = {
        "runs_analyzed": metadata["runs_analyzed"],
        "signals_analyzed": metadata["signals_analyzed"],
        "data_sources": metadata["data_sources"],
        "most_frequent_qualified_tickers": _build_count_summary(
            ticker_counter,
            "ticker",
            limit=limit,
        ),
        "most_frequent_qualified_strategies": _build_count_summary(
            strategy_counter,
            "strategy",
            limit=limit,
        ),
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
        "average_adjusted_score_by_ticker_strategy_pair": feature_summary[
            "average_adjusted_score_by_ticker_strategy_pair"
        ],
        "counts_by_volatility_context": feature_summary[
            "counts_by_volatility_context"
        ],
        "average_adjusted_score_by_volatility_context": feature_summary[
            "average_adjusted_score_by_volatility_context"
        ],
        "counts_by_stability_level": feature_summary[
            "counts_by_stability_level"
        ],
        "average_adjusted_score_by_stability_level": feature_summary[
            "average_adjusted_score_by_stability_level"
        ],
        "label_distribution": _build_count_summary(
            label_counter,
            "label",
            limit=limit,
        ),
        "feature_summary": feature_summary,
    }

    return {
        "metadata": metadata,
        "signal_quality_summary": signal_quality_summary,
        "feature_summary": feature_summary,
    }


def get_historical_intelligence_summary(limit=5):
    """Return a consolidated, JSON-serializable summary of historical intelligence."""
    return _compute_historical_intelligence_components(limit=limit)


def compute_historical_signal_quality_summary(limit=5):
    """Compute a lightweight historical summary of signal quality from stored runs."""
    return get_historical_intelligence_summary(limit=limit).get(
        "signal_quality_summary",
        {},
    )


def compute_historical_signal_feature_summary(limit=5):
    """Return the structured feature-extraction portion of the historical signal summary."""
    return get_historical_intelligence_summary(limit=limit).get("feature_summary", {})

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