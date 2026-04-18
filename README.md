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
MARKET_DATA_CACHE_TTL_SECONDS=60
PROVIDER_TIMEOUT_SECONDS=12
PROVIDER_TOTAL_TIMEOUT_SECONDS=20
PROVIDER_RETRY_COUNT=2
PROVIDER_RETRY_BACKOFF_SECONDS=0.35
PROVIDER_RETRY_STRATEGY=exponential
PROVIDER_RETRY_MAX_BACKOFF_SECONDS=1.5
PROVIDER_CONTRACTS_CACHE_TTL_SECONDS=120
PROVIDER_SNAPSHOTS_CACHE_TTL_SECONDS=45
PROVIDER_UNDERLYING_CACHE_TTL_SECONDS=15
```

## PU-14 performance and reliability posture

PU-14 improves runtime resilience and latency visibility without changing trading logic, scoring rules, or the existing top-level scan contract.

### Retry policy

- Provider HTTP operations use bounded retries only for transient conditions such as timeouts, connection failures, and retryable upstream HTTP responses like `408`, `429`, `500`, `502`, `503`, and `504`
- Default retry count is small: `2` retries beyond the initial attempt
- Retries are timeout-aware and preserve both a per-attempt timeout through `PROVIDER_TIMEOUT_SECONDS` and an overall retry budget through `PROVIDER_TOTAL_TIMEOUT_SECONDS`
- Backoff strategy is configurable through `PROVIDER_RETRY_STRATEGY` and defaults to capped exponential backoff so retries do not bunch into aggressive bursts under provider instability
- Backoff delay starts from `PROVIDER_RETRY_BACKOFF_SECONDS` and is capped by `PROVIDER_RETRY_MAX_BACKOFF_SECONDS`
- Auth, validation, malformed payload, and other non-transient provider failures are not retried
- Retry scheduling and final request outcome are logged with retry count, retry exhaustion state, and retry-delay impact so repeated provider instability is visible in production logs
- Scan diagnostics carry additive retry metadata through existing performance and provider-error diagnostics so the frontend can infer degraded provider conditions without a UI redesign

### Cache policy

- Aggregated market-data responses use a short-lived cache controlled by `MARKET_DATA_CACHE_TTL_SECONDS`
- Provider sub-reads are cached independently with explicit TTLs:
	- contracts: `PROVIDER_CONTRACTS_CACHE_TTL_SECONDS`
	- option snapshots: `PROVIDER_SNAPSHOTS_CACHE_TTL_SECONDS`
	- underlying trades: `PROVIDER_UNDERLYING_CACHE_TTL_SECONDS`
- Degraded provider responses are not persisted into the aggregated market-data cache, which avoids re-serving known provider failures as if they were healthy reads
- Cache behavior is surfaced in structured diagnostics and logs as hit/miss metadata

### Graceful degradation behavior

- A single ticker failure no longer fails the whole scan when other tickers can still be processed safely
- Scan output preserves successful ticker results, failed ticker coverage gaps, and per-ticker diagnostics in the same response
- Empty option chains, partial snapshot coverage, malformed provider payloads, and missing underlying data degrade individual tickers instead of terminating the full run when partial output is still possible
- Frontend surfaces now distinguish between genuinely empty result sets and empty boards produced under partial coverage or provider degradation

### Performance visibility

- Structured logs now make scan bottlenecks easier to isolate through:
	- total scan duration
	- provider duration
	- per-ticker processing duration
	- persistence duration
	- cache hit/miss behavior
- Additive response diagnostics now include non-breaking performance and cache metadata for frontend messaging and operational debugging

### Known limitations deferred beyond PU-14

- no distributed or shared cache layer across backend instances
- no circuit breaker or provider failover beyond bounded retries and graceful degradation
- no background scan queue, concurrency shaping, or job orchestration for large burst traffic
- no dedicated metrics backend or tracing export; visibility remains log-first
- no stale-while-revalidate strategy or proactive refresh of cached provider reads

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
For the current cloud deployment path using Render and Vercel, see `infra/render_vercel_deployment.md`.

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

## Observability and security hardening

PU-12 adds lightweight operational hardening for the FastAPI backend without changing trading logic.

### Logging conventions

- Backend logs are structured JSON lines emitted through a centralized logger helper
- Request middleware attaches a per-request `request_id` and returns it as the `X-Request-ID` response header
- Request context is propagated into service, repository, auth, and provider logs through context-local binding
- Sensitive fields such as passwords, tokens, secrets, and API credentials are masked before logging

### Logged event categories

- `request_started`
- `request_completed`
- `request_failed`
- `scan_started`
- `scan_completed`
- `scan_failed`
- `persistence_read`
- `persistence_write`
- `auth_login_success`
- `auth_login_failure`
- `auth_logout`
- `provider_request_started`
- `provider_request_completed`
- `provider_request_failed`
- security-adjacent events such as `token_validation_failed` and `unauthorized_access_attempt`

### Error handling

- API errors use a standardized envelope: `error.code`, `error.message`, `error.request_id`
- Validation, auth, not-found, provider, and internal failures are handled centrally
- Stack traces remain server-side only and are not exposed to API clients

### Health and readiness

- `GET /health` returns a simple liveness status
- `GET /ready` checks persistence access, auth store access, config resolution, and provider mode readiness
- Provider readiness is lightweight and does not perform an external API probe

### Deployment and runtime notes

- Logs are emitted as newline-delimited JSON on standard output and are intended to be consumed directly by Docker, container platforms, or external collectors
- In containerized deployments, prefer platform log collection from stdout/stderr rather than writing application log files inside the container
- `X-Request-ID` is accepted from upstream when present and echoed back to clients; only trust upstream-supplied request IDs when your reverse proxy or load balancer is under your control
- If the app sits behind a public reverse proxy, configure that proxy to generate or sanitize request IDs instead of blindly forwarding arbitrary client-provided correlation headers
- Keep `GET /ready` lightweight and focused on internal dependency readiness; it should not require live provider calls or external market-data reachability

### Environment variables

Existing runtime variables still apply, plus the following observability-oriented settings:

- `APP_ENV`: environment label such as `development`, `test`, or `production`
- `LOG_LEVEL`: backend log level, for example `INFO`, `DEBUG`, or `WARNING`
- `LOG_FORMAT`: reserved seam for log formatting selection, currently JSON-oriented
- `SENTRY_DSN`: optional external error tracking DSN
- `ALPACA_API_KEY`
- `ALPACA_API_SECRET`
- `ALPACA_DATA_BASE_URL`
- `ALPACA_TRADING_BASE_URL`
- `HISTORY_DIR`
- `CACHE_DIR`
- `SCAN_DATABASE_PATH`
- `AUTH_SESSION_TTL_HOURS`
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`

### Cloud deployment

- Backend target: Render
- Frontend target: Vercel
- Backend container/runtime details are defined in [Dockerfile](Dockerfile) and [render.yaml](render.yaml)
- Frontend deployment settings are documented in [infra/render_vercel_deployment.md](infra/render_vercel_deployment.md) and [frontend/vercel.json](frontend/vercel.json)

### Deferred to PU-13

- external log aggregation and retention policy
- real cloud secret manager integration
- stronger deployment-time security headers and reverse-proxy hardening
- metrics and tracing export to dedicated observability backends
- active provider readiness probing with rate-limit-aware behavior

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

