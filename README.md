# Options Trading App

Options Trading App is an authenticated decision-support workspace for reviewing credit spread opportunities. It runs scans across configured ticker groups, scores bull put and bear call setups, surfaces the highest-priority opportunities, and preserves enough history and diagnostics to explain what happened in the latest run.

> This product is for analysis and review. It does not place orders or automate execution.

## What the app is today

The current product is split into two deployed surfaces:

- A React workspace in `frontend/` for operators
- A FastAPI backend in `backend/` for auth, scan execution, persisted history, and diagnostics

The main user workflow is:

1. Sign in
2. Run a scan with Guided or Expert controls
3. Review the latest overview snapshot
4. Inspect qualified trades, alerts, portfolio posture, history, and daily summary
5. Open a qualified trade detail view for execution prep

## Current product surfaces

| Surface | Purpose |
| --- | --- |
| `Login` | Session entry for protected review flows |
| `Overview` | Latest-run cockpit with top decision, trust signals, and what to review next |
| `Qualified Trades` | Ranked review list of candidates that cleared the active thresholds |
| `Qualified Trade Detail` | Execution-prep view for structure, verdict, and checklist framing |
| `Alerts` | Shortlist of the freshest opportunities worth immediate review |
| `Portfolio` | Exposure, directional balance, concentration, and overlap context |
| `History` | Prior-run context, recurring signals, and trend continuity |
| `Daily Summary` | Run-level interpretation of what the scan found |

## Product behavior

- `Balanced` is calibrated to produce a modest number of alerts on a typical run instead of behaving like an almost-empty strict mode
- Alerts are stricter than qualified trades, so a run can show qualified trades while still returning zero alerts
- When a run has zero alerts, the UI explains whether no candidates qualified at all or whether candidates existed but did not pass alert thresholds
- Expert mode allows operators to relax thresholds when they want more signal volume
- Healthy empty states are treated as valid outcomes, not automatic failures
- Partial provider coverage and degraded runs surface through diagnostics rather than disappearing into blank screens

## Architecture at a glance

### Frontend

- Vite-based React app in `frontend/`
- Auth-protected routes for overview, qualified trades, alerts, portfolio, history, and daily summary
- Selector-driven presentation layer that reshapes backend payloads without changing scoring logic

### Backend

- FastAPI service in `backend/`
- Token-based auth endpoints for register, login, logout, and current session lookup
- Scan endpoints for latest scan retrieval, scan history access, overview snapshots, alerts, qualified trades, trade detail, portfolio, history, and daily summary
- Health and readiness endpoints for deployment checks

### Persistence and runtime state

- Durable scan storage through `SCAN_DATABASE_PATH`
- Run history stored under `HISTORY_DIR`
- Cache data stored under `CACHE_DIR`
- Optional live market data via Alpaca credentials, with mock mode available when credentials are absent

## Local development

### Recommended startup

Use the included local launcher from the repository root:

```powershell
.\run-dev.ps1
```

That starts:

- The backend API on `http://127.0.0.1:8000`
- The frontend on `http://localhost:5173`

Optional flags:

```powershell
.\run-dev.ps1 -InstallFrontendDeps
```

### Manual startup

If your local environment is already prepared, run the services separately:

```powershell
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

```powershell
cd frontend
npm install
npm run dev
```

### Local URLs

- Frontend: `http://localhost:5173`
- Backend docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`
- Ready: `http://127.0.0.1:8000/ready`

## Configuration

Defaults are read from `config.yaml` and merged with runtime overrides and environment variables.

Representative local configuration:

```yaml
profile: balanced
ticker_group: tech

pop_weight: 0.6
ror_weight: 0.4

min_score: 55
min_consistency: 1

dte_min: 20
dte_max: 35
```

Common environment variables:

```text
ALPACA_API_KEY=
ALPACA_API_SECRET=
ALPACA_DATA_BASE_URL=https://data.alpaca.markets
ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets
HISTORY_DIR=.history
CACHE_DIR=.cache
SCAN_DATABASE_PATH=.history/scan_store.sqlite
AUTH_SESSION_TTL_HOURS=168
MARKET_DATA_CACHE_TTL_SECONDS=60
PROVIDER_MEMORY_CACHE_ENABLED=true
PROVIDER_MEMORY_CACHE_MAX_ENTRIES=512
PROVIDER_TIMEOUT_SECONDS=12
PROVIDER_TOTAL_TIMEOUT_SECONDS=20
PROVIDER_RETRY_COUNT=2
PROVIDER_RETRY_BACKOFF_SECONDS=0.35
PROVIDER_RETRY_STRATEGY=exponential
PROVIDER_RETRY_MAX_BACKOFF_SECONDS=1.5
PROVIDER_TICKER_DATA_CACHE_TTL_SECONDS=20
PROVIDER_CONTRACTS_CACHE_TTL_SECONDS=120
PROVIDER_SNAPSHOTS_CACHE_TTL_SECONDS=45
PROVIDER_UNDERLYING_CACHE_TTL_SECONDS=15
VITE_API_BASE_URL=http://127.0.0.1:8000
VITE_AUTH_TOKEN_STORAGE_KEY=options-platform.auth-token
```

## Deployment

Current deployment topology:

- Frontend: Vercel with `frontend/` as the project root
- Backend: Render web service using the repository `Dockerfile`
- Persistence: mounted Render disk for SQLite, history, and cache data

Frontend deployment settings:

- Framework preset: `Vite`
- Build command: `npm run build`
- Output directory: `dist`

Backend deployment expectations:

- Health check: `GET /health`
- Readiness check: `GET /ready`
- Persistent disk mounted at `/var/data`
- Production persistence paths under `/var/data`

Detailed deployment notes live in `infra/render_vercel_deployment.md` and `render.yaml`.

## Testing

Frontend:

```powershell
cd frontend
npm test
npm run build
```

Backend:

```powershell
pytest
```

Focused test files already cover scan APIs, auth flows, selector behavior, alert messaging, observability, and scan persistence.

## Reliability posture

The current app includes a lightweight operational posture designed for real scan review rather than a demo-only UI:

- Bounded retries for transient provider failures
- Cache-aware provider execution with short-lived response reuse
- Partial-result handling when some tickers fail but others can still be scored
- Structured diagnostics for degraded scans, latency, retry impact, and cache behavior
- Shared frontend states for healthy-empty, partial, degraded, in-progress, and failed runs

The backend remains the source of truth for scoring, qualification, alerts, portfolio interpretation, and run diagnostics.

## Trade lifecycle model (PU-15A.1)

PU-15A.1 introduces a persistent lifecycle record for each trade_id so user workflow state can evolve across scans without changing scan qualification, scoring, alerts, ranking, or provider behavior.

Current lifecycle states in the model:

- new
- saved
- watching
- execution_ready
- paper_submitted
- paper_filled
- paper_closed
- dismissed

Active states in this phase:

- new
- saved
- watching
- execution_ready
- dismissed

In this phase, lifecycle is user-managed state only:

- no broker order placement
- no paper order submission workflow
- no execution automation

Later phases (PU-15A.2 and PU-15A.4) will build on the same model to add paper execution transitions, execution history details, and broker-facing orchestration.

## Repository pointers

- `backend/`: API routes, services, repositories, auth, and observability
- `frontend/`: routed workspace, selectors, UI components, tests, and Vercel config
- `infra/`: deployment and readiness notes
- `history/` and `.history/`: persisted run artifacts and local runtime storage
- `exports/`: generated exports from scan results

## Boundaries

- This system supports review and decision preparation only
- Trade selection still depends on operator judgment
- Missing provider coverage can narrow a run without invalidating the rest of the result
- Zero alerts can be a healthy outcome under the current filters

## License

This project is released under the terms of the included `LICENSE`.

