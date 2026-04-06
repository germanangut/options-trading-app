# Options Trading App

`Options Trading App` is a Python + Streamlit decision-support tool for evaluating credit spread opportunities. It scans configured ticker groups, scores bull put and bear call setups using the existing engine rules, highlights the best current candidate, and adds run-health and historical context for review.

> This project is analytical only. It helps evaluate opportunities; it does **not** place live trades or automate execution.

## What the app looks like today

The current Streamlit dashboard is organized around a practical review workflow:

| Area | Purpose |
| --- | --- |
| `Overview` | Shows the Top Decision, System Signals, Trade Lifecycle, and System Boundaries |
| `Alerts` | Surfaces initial opportunities worth reviewing |
| `Qualified Trades` | Focuses on the strongest current candidates that cleared the active thresholds |
| `History` | Shows recurring patterns and stability context from prior runs |
| `Daily Summary` | Gives a run-level interpretation of what the scan found |
| `Raw Output` | Exposes the full structured engine response for inspection |

## Core capabilities

- Uses Alpaca option data when credentials are available
- Falls back to built-in mock data when credentials are not configured
- Evaluates both **bull put spreads** and **bear call spreads**
- Scores candidates using the engine’s existing **POP / ROR** logic and current rule set
- Highlights a best current trade and explains why it surfaced
- Tracks light historical context in `.history` for stability/trend review
- Caches market data in `.cache` for faster repeat runs
- Supports both a Streamlit UI and a CLI workflow

## Current system boundaries

The app is intended for **analysis and decision support**:

- Results reflect the current rules and available data
- Missing tickers or provider issues can reduce coverage for a run
- A run with no alerts or no qualified trades can still be a healthy outcome
- Final trade decisions require user judgment

## Quick start

### 1) Create and activate a virtual environment

```bash
python -m venv venv
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Optionally install the local test runner

```bash
pip install pytest
```

### 4) Run the Streamlit dashboard

```bash
streamlit run app.py
```

Then open `http://localhost:8501`.

### 5) Or run the CLI directly

```bash
python main.py --profile balanced --group tech --alerts-only
```

## Configuration

The app reads defaults from `config.yaml` and merges them with runtime overrides and environment variables.

Example `config.yaml`:

```yaml
profile: balanced
ticker_group: tech

pop_weight: 0.6
ror_weight: 0.4

min_score: 65
min_consistency: 3

dte_min: 20
dte_max: 35
```

Optional environment variables:

```text
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_DATA_BASE_URL=https://data.alpaca.markets
ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets
HISTORY_DIR=.history
CACHE_DIR=.cache
```

## Common usage patterns

### Streamlit UI

```bash
streamlit run app.py
```

### Alerts-only JSON output

```bash
python main.py --profile balanced --group tech --alerts-only
```

### Human-readable daily summary

```bash
python main.py --profile balanced --group tech --daily-summary
```

### Export alerts to CSV

```bash
python main.py --profile balanced --group tech --export-csv
```

## Docker and local container runs

Build the image:

```bash
docker build -t options-trading-app .
```

Run the UI:

```bash
docker run --rm -p 8501:8501 options-trading-app
```

Run with Compose (recommended for local consistency):

```bash
docker compose up --build
```

If you want to preserve history and cache between runs, keep the mounted data directories in place and/or provide `.env` values as needed.

## Project structure

- `app.py` — Streamlit UI and presentation logic
- `engine.py` — core scan engine and business rules
- `ui/` — focused rendering helpers for alerts and qualified trades
- `main.py` — CLI entry point
- `settings.py` — runtime configuration resolution
- `data_provider.py` — market data access and provider fallback behavior
- `history.py` / `history_reader.py` — persistence and trend/stability context
- `output.py` — output formatting and export helpers

## Default ticker groups

- `tech`: `NVDA`, `TSLA`, `META`, `AAPL`, `MSFT`
- `index`: `SPY`, `QQQ`, `IWM`
- `mixed`: `SPY`, `QQQ`, `AAPL`, `MSFT`, `NVDA`

## Testing and validation

Run the unit suite locally:

```bash
python -m pytest -q
```

For a lightweight source validation pass:

```bash
python -m compileall .
```

The current CI flow validates:

- Python source compilation
- unit tests with `pytest`
- Docker image buildability with the existing `Dockerfile`

## Notes

- Historical scans are stored under `.history`
- Market-data cache is stored under `.cache`
- If Alpaca credentials are missing, the app falls back to mock data for development/testing
- The UI is designed to help review opportunities, not to execute orders

## License

This project is released under the terms of the included `LICENSE`.

