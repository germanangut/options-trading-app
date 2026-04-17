# Render + Vercel Deployment

## Target topology

- Backend API: Render web service
- Frontend UI: Vercel project with `frontend` as the root directory
- Persistence: SQLite file plus history/cache directories mounted on a Render disk
- Delivery: GitHub-connected automatic deploys from the main branch

## Backend on Render

### Recommended service type

- Use a Render web service connected to this GitHub repository
- Use the included [render.yaml](render.yaml) blueprint or equivalent manual settings
- Keep a persistent disk mounted at `/var/data`

### Backend build and start posture

- Dockerfile: [Dockerfile](Dockerfile)
- Container listens on `0.0.0.0`
- Port comes from Render `PORT` with fallback to `8000`
- Health endpoint: `GET /health`
- Readiness endpoint: `GET /ready`

### Backend environment variables

Required or commonly configured on Render:

- `APP_ENV=production`
- `LOG_LEVEL=INFO`
- `AUTH_SESSION_TTL_HOURS=168`
- `HISTORY_DIR=/var/data/history`
- `CACHE_DIR=/var/data/cache`
- `SCAN_DATABASE_PATH=/var/data/scan_store.sqlite`
- `CORS_ALLOW_ORIGINS=https://your-frontend.vercel.app`
- `CORS_ALLOW_ORIGIN_REGEX=https://.*-your-projects-team\.vercel\.app`
- `ALPACA_API_KEY=` optional for live provider access
- `ALPACA_API_SECRET=` optional for live provider access
- `ALPACA_DATA_BASE_URL=https://data.alpaca.markets`
- `ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets`
- `SENTRY_DSN=` optional

### SQLite posture on Render

- Fastest viable path is to keep SQLite
- SQLite is only durable if the Render service uses a mounted disk
- Without a disk, filesystem state is ephemeral and scans/auth sessions can be lost on restart or redeploy
- With the included blueprint, use:
  - `SCAN_DATABASE_PATH=/var/data/scan_store.sqlite`
  - `HISTORY_DIR=/var/data/history`
  - `CACHE_DIR=/var/data/cache`

## Frontend on Vercel

### Recommended project settings

- Root Directory: `frontend`
- Framework Preset: Vite
- Build Command: `npm run build`
- Output Directory: `dist`

### Frontend environment variables

Configure in Vercel:

- `VITE_API_BASE_URL=https://your-render-service.onrender.com`
- `VITE_AUTH_TOKEN_STORAGE_KEY=options-platform.auth-token`

Notes:

- `VITE_API_BASE_URL` must be set for production so the frontend does not assume localhost
- Auth is bearer-token based and stored in browser local storage, so there is no frontend cookie secret to configure in this phase

## Local vs production separation

### Local development

- Backend API base URL: `http://127.0.0.1:8000`
- Frontend local origin: `http://localhost:5173`
- Persistence path: `.history/scan_store.sqlite`

### Backend production

- Backend URL: Render service URL
- Persistence path: `/var/data/scan_store.sqlite`
- CORS origins: exact Vercel production domain and optional preview regex

### Frontend production

- Frontend URL: Vercel production domain
- API base URL: Render backend URL via `VITE_API_BASE_URL`
- Auth token key: configurable via `VITE_AUTH_TOKEN_STORAGE_KEY`

## CORS guidance

- Keep exact frontend origins in `CORS_ALLOW_ORIGINS`
- Use `CORS_ALLOW_ORIGIN_REGEX` only when Vercel preview deployments need to reach the backend
- Do not use wildcard `*` in production if auth-bearing requests are involved

## Verification checklist

After first deployment, verify:

1. Render service boots successfully and stays healthy
2. `GET /health` returns `200`
3. `GET /ready` returns `200`
4. Frontend loads from Vercel without localhost assumptions
5. Register/login works from the deployed frontend
6. Protected routes reject unauthenticated access and allow authenticated access
7. Running a scan succeeds
8. Latest scan loads successfully
9. Overview, qualified trades, trade detail, portfolio, history, and daily summary screens load

## GitHub-connected auto deploy posture

- Backend: connect Render to the repository and deploy from `main`
- Frontend: connect Vercel to the repository and set Root Directory to `frontend`
- Expected backend container command comes from [Dockerfile](Dockerfile)
- Expected frontend build command comes from [frontend/package.json](../frontend/package.json)

## First-time manual setup

1. Create the Render web service and attach the persistent disk
2. Set backend environment variables in Render
3. Create the Vercel project with `frontend` as Root Directory
4. Set `VITE_API_BASE_URL` in Vercel to the Render backend URL
5. Add the final Vercel production URL to Render `CORS_ALLOW_ORIGINS`
6. Redeploy backend after the final frontend URL is known

## Deferred to PU-14

- Managed database migration away from SQLite
- Dedicated preview-environment backend strategy
- Secret manager integration beyond platform env vars
- CDN and proxy header hardening beyond the current lightweight request ID posture
- Richer release automation and deployment promotion workflows