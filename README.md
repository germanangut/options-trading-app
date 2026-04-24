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

Focused test files already cover scan APIs, auth flows, selector behavior, alert messaging, observability, scan persistence, and trade lifecycle state transitions.

## Reliability posture

The current app includes a lightweight operational posture designed for real scan review rather than a demo-only UI:

- Bounded retries for transient provider failures
- Cache-aware provider execution with short-lived response reuse
- Partial-result handling when some tickers fail but others can still be scored
- Structured diagnostics for degraded scans, latency, retry impact, and cache behavior
- Shared frontend states for healthy-empty, partial, degraded, in-progress, and failed runs

The backend remains the source of truth for scoring, qualification, alerts, portfolio interpretation, and run diagnostics.

## Trade lifecycle model (PU-15A.1)

PU-15A.1 introduces a persistent, user-owned lifecycle record for each qualified trade so workflow state can evolve across scans without touching scan qualification, scoring, alerts, ranking, or provider behavior.

### Lifecycle states

| State | Phase | Description |
| --- | --- | --- |
| `new` | Active | Default state; candidate has not been acted on |
| `saved` | Active | Operator has bookmarked the trade for later review |
| `watching` | Active | Trade is under active monitoring |
| `execution_ready` | Active | Operator has approved the setup for paper execution |
| `dismissed` | Active | Trade has been intentionally set aside |
| `paper_submitted` | Deferred | Paper order submitted (PU-15A.2) |
| `paper_filled` | Deferred | Paper order filled (PU-15A.2) |
| `paper_closed` | Deferred | Paper position closed (PU-15A.2) |

### Lifecycle API endpoints

All endpoints are auth-protected and scoped to the authenticated user.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/lifecycle` | List all lifecycle records for the current user |
| `GET` | `/api/v1/lifecycle/{trade_id}` | Get lifecycle state for one trade; returns `new` with `is_default: true` if not yet set |
| `POST` | `/api/v1/lifecycle/{trade_id}` | Create or update lifecycle state |
| `PATCH` | `/api/v1/lifecycle/{trade_id}` | Partial update of state, note, tags, or source scan reference |

### Frontend integration

PU-15A.2 refines lifecycle interactions so the user experience feels like a real review workflow rather than raw state mutation.

**Qualified Trades board**

- Each card shows a `LifecycleBadge` (`new / saved / watching / ready / dismissed`) with a colored dot
- `LifecycleActions` renders the three forward-progress actions (Save, Watch, Mark Ready) in order, with the active state visually highlighted (accent for saved/watching, success for execution_ready), and Dismiss isolated to the trailing edge as a quieter destructive action
- A lifecycle filter tab row above the trade list lets the operator narrow to `All / New / Saved / Watching / Ready / Dismissed` — each tab shows the count for that state
- Error feedback surfaces via a `WarningBand` when a lifecycle upsert fails

**Trade Detail execution brief**

- The lifecycle section opens with a `LifecycleBadge` and a contextual description of what the current state means for the review workflow
- `LifecycleActions` replaces the raw button row with the same active-state and dismiss-isolation treatment
- The review note section has two modes:
	- **Read mode**: displays the saved note as text with an Edit button; shows "Add a note about this trade…" when no note is saved
	- **Edit mode**: textarea with Save note (primary, disabled until changed) and Cancel; Save triggers a 2.5-second "Saved" confirmation flash then returns to read mode
- All lifecycle errors surface via the component's `errorMessage` prop

### Execution tickets and paper submission (PU-15A.3 / PU-15A.4)

Execution tickets are separate from both scan candidates and lifecycle records. They capture a user-owned execution snapshot and now support a ticket-centered paper submission flow.

Paper submission endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/tickets/{ticket_id}/submit-paper` | Submit eligible ticket to Alpaca paper account and persist broker metadata |
| `POST` | `/api/v1/tickets/{ticket_id}/refresh-paper` | Refresh broker status for an already-submitted ticket |

PU-15A.4 is constrained to paper trading only:

- `ALPACA_TRADING_BASE_URL` must resolve to `https://paper-api.alpaca.markets...`
- live trading endpoints are blocked by a backend guardrail
- credentials are required; missing credentials reject the request with clear messaging

Ticket-to-broker mapping in this phase:

- supported strategies: `bull_put_spread`, `bear_call_spread`
- supported intents: `open_credit`, `open_debit`
- order payload: multi-leg (`order_class: mleg`) option order
- strike/expiry snapshot fields from the ticket are converted to OCC option symbols and sent as broker legs
- exact outbound payload and normalized broker response are stored on the ticket for auditability

Execution status mapping from broker status:

| Broker status raw | App execution status |
| --- | --- |
| `new`, `accepted`, `pending_new`, `partially_filled`, `pending_replace`, `replaced`, `calculated`, `stopped` | `accepted` |
| `filled` | `filled` |
| `rejected`, `suspended` | `rejected` |
| `canceled`, `expired`, `done_for_day`, `pending_cancel` | `canceled` |
| unknown/other | `submitted` |

Audit fields stored per ticket:

- `broker_order_id`
- `broker_status_raw`
- `broker_submitted_at`
- `broker_updated_at`
- `last_submission_payload`
- `last_submission_response`
- `submission_error_message`

Known limitations deferred to PU-15A.5:

- broader strategy and order-construction coverage beyond the two spread strategies above
- richer order lifecycle handling (replace/cancel actions and historical timeline UI)
- execution analytics, P&L attribution, and full operational dashboards

### Paper positions dashboard (PU-15A.5)

PU-15A.5 adds a dedicated paper-operations workspace focused on post-submission state, while preserving strict separation between scan analytics, lifecycle workflow state, execution tickets, and broker operational truth.

Primary dashboard sections:

- Pending Orders
- Open Paper Positions
- Closed Paper Trades
- Recent broker order history

Dashboard endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/tickets/paper-dashboard` | Return grouped pending/open/closed paper operational state |
| `GET` | `/api/v1/tickets/paper-dashboard?refresh_status=true` | Same view with best-effort refresh of in-flight submitted/accepted tickets |

Data sourcing approach (hybrid):

- app-owned persisted ticket metadata remains the operational history backbone
- optional broker enrichment pulls open positions and recent orders from Alpaca paper APIs
- if broker credentials or broker fetches are unavailable, dashboard still renders from persisted ticket history with explicit warnings

Status grouping approach:

- Pending Orders: `draft`, `ready`, `submitted`, `accepted`
- Open Paper Positions: live broker-reported open positions, optionally linked to filled tickets by symbol/ticker inference
- Closed Paper Trades: ticket outcomes in terminal states (`rejected`, `canceled`, plus filled tickets not currently matched to open broker positions)

P&L handling:

- unrealized P&L is shown only from broker position fields when available
- realized P&L is not inferred or fabricated in this phase when not directly trustworthy

Current limitations deferred beyond PU-15A.5:

- cancel/replace broker actions from dashboard surfaces
- robust position-to-ticket attribution across every broker symbol edge case
- advanced execution analytics and full performance attribution

### Payoff engine (PU-15B.1)

PU-15B.1 adds an analytical payoff engine for trade-detail decision support. This layer is intentionally independent from broker submission and does not alter scan ranking, lifecycle state semantics, or ticket execution flows.

Supported strategy shapes in this phase:

- `bull_put_spread`
- `bear_call_spread`

Payoff endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/payoff/scans/{scan_id}/trades/{trade_id}` | Compute expiration payoff model for a qualified trade from a scan |
| `GET` | `/api/v1/payoff/tickets/{ticket_id}` | Compute expiration payoff model from stored execution ticket snapshot |

Response includes:

- deterministic underlying-price grid (`price_grid`)
- expiration payoff points (`payoff_points`)
- summary metrics (`max_profit`, `max_loss`, `breakeven_low`/`breakeven_high`)
- textual zones (`profit_zone`, `loss_zone`) and strategy explanation

Frontend integration in this phase:

- Qualified Trade Detail now includes an Expiration Payoff panel
- panel shows max profit/loss/breakeven strip plus a zero-anchored payoff curve
- curve is model-only and sourced from the new payoff API endpoint

Current limitations deferred beyond PU-15B.1:

- no time-step path simulation or probability-weighted outcome surfaces
- no volatility or Greeks sensitivity overlays
- no what-if leg editing workspace (simulation lab)

### Strategy variants (PU-15B.2)

PU-15B.2 adds an analytical variant-comparison layer on top of the selected baseline trade. This phase does not change scan selection, ranking, alerting behavior, lifecycle semantics, ticket workflow, or Alpaca paper integration.

Variant meanings in this phase:

- Baseline: Current scanned setup
- Conservative: Lower credit, more room for the trade to work
- Max Credit: Higher premium, tighter room for error

Important scope notes:

- Delta-neutral is intentionally out of scope for PU-15B.2
- Variants are analytical only and are not auto-promoted to execution-ready
- If clean variant construction is not possible, fewer variants are returned

Supported strategy families in PU-15B.2:

- `bull_put_spread`
- `bear_call_spread`

Variant endpoint:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/variants/scans/{scan_id}/trades/{trade_id}` | Return baseline + eligible conservative/max-credit analytical variants for the selected qualified trade |

Variant response includes:

- `variant_type` (`baseline`, `conservative`, `max_credit`)
- spread shape (`short_strike`, `long_strike`, `expiration_date`, `spread_width`)
- economics (`net_credit`, `max_profit`, `max_loss`, `breakeven`)
- user-facing explanation (`label`, `rationale`)
- payoff summary (`payoff` with max profit/loss, breakeven and payoff points)

Current data limitations in this phase:

- baseline credit is from the scanned trade snapshot
- conservative/max-credit credits are deterministic analytical estimates when full chain pricing is not present in the trade payload
- no fabricated contracts, strikes, or premiums are returned

Deferred beyond PU-15B.2:

- delta-neutral variants
- strategy workbench/lab with sliders and what-if controls
- multi-strategy compare grids
- portfolio-level scenario simulation
- volatility/time-decay scenario simulation

### Visual strategy lab (PU-15B.3)

PU-15B.3 adds a compact visual strategy lab inside Qualified Trade Detail to compare baseline and available variants as a decision-support surface.

Purpose in this phase:

- make variant differences visually clear without changing scan selection or execution workflows
- compare payoff shape and key economics in a compact, readable layout
- explain what changed versus baseline in plain language

Supported strategies and variants in PU-15B.3:

- strategies: `bull_put_spread`, `bear_call_spread`
- variants: `baseline`, `conservative`, `max_credit`

Interaction model chosen:

- baseline-pinned comparison
- one selected comparison target (`conservative` or `max_credit`) at a time via compact tabs
- side-by-side baseline and selected-variant expiration payoff charts to avoid overlay clutter

Comparison metrics shown:

- net credit
- max profit
- max loss
- breakeven
- spread width
- payoff curve (expiration)
- explicit delta-to-baseline summary from backend comparison payload

Why delta-neutral is not included:

- delta-neutral variants are intentionally deferred beyond PU-15B.3 to keep this phase scoped to current controlled spread variants and clear structural comparisons.

Deferred beyond PU-15B.3:

- full-screen strategy lab/workbench
- manual strike editing
- what-if sliders
- multi-variant overlay with dense chart controls
- volatility/time-decay scenario simulation layers

### Delta-neutral exploration (PU-15B.5)

PU-15B.5 adds a separate analytical comparison path for directional exposure. It does not replace the baseline trade and does not change scan logic, ranking, lifecycle behavior, ticket workflows, or broker integration.

What delta-neutral means in this app:

- baseline remains the selected scanned directional spread
- delta-neutral exploration attempts a closer-to-neutral nearby candidate
- this phase targets reduced directional bias, not guaranteed perfect zero delta

Supported baseline strategies in PU-15B.5:

- `bull_put_spread`
- `bear_call_spread`

Delta-neutral endpoint:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/v1/delta-neutral/scans/{scan_id}/trades/{trade_id}` | Return baseline directional summary and a reduced-bias candidate when cleanly available |

Response includes:

- baseline net delta (`baseline.net_delta`)
- neutral candidate availability flag (`neutral_candidate_available`)
- neutral candidate net delta (`neutral_candidate.net_delta`) when available
- delta reduction summary (`comparison.delta_reduction`, `comparison.delta_reduction_pct`)
- payoff/risk summary and payoff curves for baseline and candidate
- unavailable reason when no clean candidate can be constructed

Current limitations in this phase:

- candidate net delta is an analytical approximation from baseline leg deltas and nearby structural adjustments
- no freeform strategy builder or multi-leg editor
- no portfolio hedging engine
- no auto-promotion to execution-ready workflows

Deferred beyond PU-15B.5:

- exact-neutral multi-structure search engine
- iron-condor / multi-leg neutral labs
- portfolio-level hedge balancing and optimization
- advanced Greek surface exploration (time/volatility sensitivity)

### Scope boundaries in this phase

- No broker order placement
- No paper order submission workflow
- No execution automation
- Lifecycle records are user-owned and do not alter scan output or scoring

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

