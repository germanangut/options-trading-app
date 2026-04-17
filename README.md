# Options Trading App

`Options Trading App` is a Python + Streamlit decision-support tool for evaluating credit spread opportunities. It scans configured ticker groups, scores bull put and bear call setups using the existing engine rules, highlights the best current candidate, and adds run-health and historical context for review.

> This project is analytical only. It helps evaluate opportunities; it does **not** place live trades or automate execution.

## What the app looks like today

The current Streamlit dashboard is organized around a practical review workflow: 

| Area | Purpose |
| --- | --- |
| `Overview` | Shows the Top Decision, system signals, trade lifecycle, historical signal context, and system boundaries |
| `Portfolio` | Summarizes current-run concentration, directional tilt, overlap, and sizing context |
| `Alerts` | Surfaces fresh opportunities worth reviewing |
| `Qualified Trades` | Focuses on the strongest current candidates that cleared the active thresholds |
| `History` | Shows trend insights, recurring alerts, and historical context from prior runs |
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

## Productization readiness

A lightweight productization posture definition lives in `infra/product_readiness.yaml`. It documents the app's current stage, intended internal usage model, boundaries, current deployment readiness, and the key requirements before wider sharing. The current deployment target decision is documented in `infra/deployment_target.md`.

## Quick start

### 1) Create and activate a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source venv/bin/activate
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
SCAN_DATABASE_PATH=.history/scan_store.sqlite
AUTH_SESSION_TTL_HOURS=168
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

For a simple VM-based operational setup, see `infra/vm_deployment.md`. For the current private/internal access approach, see `infra/access_model.md`.

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

## Persistence posture

The backend now uses a durable SQLite scan store for canonical `ScanResult` persistence.

- Backend storage backend: SQLite
- Default location: `.history/scan_store.sqlite`
- Override with: `SCAN_DATABASE_PATH=/path/to/scan_store.sqlite`

Why SQLite for PU-10:

- it is built into Python and adds no new infrastructure burden
- it keeps `scan_id` and `trade_id` durable across backend restarts
- it is reliable enough for a single-instance internal product phase
- it provides a clean repository seam for a later migration to Postgres or another managed database

Migration posture:

- The repository abstraction lives under `backend/repositories/`
- Service orchestration remains in the backend service layer
- A future cloud/database migration should swap the repository implementation rather than changing trading logic or API contracts
- Canonical persisted scans are the authoritative backend source for latest scan, trade detail, and history reads
- Legacy JSONL history files are compatibility-only fallback inputs for older runs that predate canonical persistence
- Future database migration should preserve repository contracts and swap the backend implementation rather than changing API or trading logic

## Auth and user ownership posture

PU-11 adds app-owned identity and route protection without changing scan logic.

- Authentication is local to this app and uses email/password plus opaque bearer sessions
- User identity is not coupled to Alpaca or any broker account
- Persisted scans are now user-owned through `owner_user_id`
- Protected backend routes return only the authenticated user's latest scan, trade detail, alerts, portfolio, and history views
- A separate `broker_connections` table exists as a future seam for broker linking without replacing app identity

Current auth routes:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

## React compatibility notes

Wave 2 adds backend-owned decision DTO shaping so React can stay presentation-only while simplifying some selectors.

- Trade detail can prefer the dedicated backend trade-detail response instead of rebuilding execution-prep sections from the latest scan payload
- Overview can consume a dedicated overview snapshot and comparison block instead of stitching together trust, comparison, and top-opportunity summaries client-side
- Trade-specific history context is now available as a compact backend-owned section instead of being inferred only from generic history metadata

## Project structure

- `app.py` — Streamlit UI and presentation logic
- `engine.py` — core scan engine and business rules
- `ui/` — focused rendering helpers for overview, portfolio, alerts, and qualified trades
- `main.py` — CLI entry point
- `settings.py` — runtime configuration resolution
- `data_provider.py` — market data access and provider fallback behavior
- `history.py` / `history_reader.py` — persistence and trend/stability context
- `output.py` — output formatting and export helpers
- `infra/product_readiness.yaml` — lightweight definition of the current productization-readiness posture
- `infra/deployment_target.md` — concise record of the selected deployment approach and rationale
- `infra/vm_deployment.md` — practical guide for running the app on a single VM with Docker
- `infra/access_model.md` — definition of the current private/internal access pattern and reverse proxy approach

## Default ticker groups

- `tech`: `NVDA`, `TSLA`, `META`, `AAPL`, `MSFT`
- `index`: `SPY`, `QQQ`, `IWM`
- `mixed`: `SPY`, `QQQ`, `AAPL`, `MSFT`, `NVDA`, `TSLA`, `INTC`, `AMD`, `AMZN`, `GOOGL`

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

