# VM Deployment Setup Guide

This guide describes a simple, repeatable deployment setup for running the app on a **single VM using Docker**.

> This setup is intended for the app's current stage: a single-user internal decision-support system.

## 1. VM assumptions and prerequisites

Recommended baseline:

- Linux VM with shell access
- Docker installed
- Docker Compose available via `docker compose`
- A user account with permission to run Docker
- Port `8501` open for internal access as needed
- Sufficient disk space for Docker images plus persisted history/cache data

## 2. Recommended deployment directory structure

Use a single application directory on the VM, for example:

```text
/opt/options-trading-app/
  Dockerfile
  docker-compose.yml
  .env
  .history/
  .cache/
  config.yaml
  strategy_config.yaml
  ...application files...
```

This keeps runtime files, configuration, and persisted app data together in one predictable location.

## 3. Environment file handling

Create a `.env` file in the deployment root when runtime secrets or overrides are needed.

Example:

```env
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_DATA_BASE_URL=https://data.alpaca.markets
ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets
```

Notes:

- The app can still run without Alpaca credentials by falling back to mock data.
- Keep `.env` readable only by the intended VM user/operators.
- Do not commit VM-specific `.env` values back to the repository.

## 4. Persistent history and cache mapping

The current Compose setup maps persistent directories from the VM filesystem into the container:

- `./.history` for run history
- `./.cache` for cached market data

Inside the container these are exposed through:

- `/data/history`
- `/data/cache`

Before first startup, ensure the directories exist:

```bash
mkdir -p .history .cache
```

## 5. Startup command

From the deployment root on the VM, start the app with:

```bash
docker compose up -d --build
```

This will:

- build the image from the existing `Dockerfile`
- start the Streamlit app container
- expose the UI on port `8501`
- preserve history and cache via the mounted directories

## 6. Restart and update workflow

For a normal restart:

```bash
docker compose restart
```

For an application update after pulling or copying new code:

```bash
docker compose down
docker compose up -d --build
```

This keeps the deployment process simple while preserving `.history` and `.cache` on disk.

## 7. Verification steps

After startup, verify the deployment with the following checks:

1. Confirm the container is running:
   ```bash
   docker compose ps
   ```
2. Check recent logs:
   ```bash
   docker compose logs --tail=100
   ```
3. Open the UI in a browser:
   ```text
   http://<vm-host>:8501
   ```
4. Confirm `.history` and `.cache` are present and writable after app usage.

## 8. Basic troubleshooting and log inspection

Useful commands:

```bash
docker compose ps
docker compose logs -f
docker compose logs --tail=200 app
docker compose restart app
docker compose down
```

Common checks:

- If the UI is unreachable, confirm port `8501` is exposed and accessible on the VM.
- If market data is unavailable, review `.env` values and provider-related logs.
- If history or cache is not persisting, confirm the `.history` and `.cache` directories exist and are writable.

## 9. Operational note

This setup is intentionally lightweight and appropriate for the currently selected target: **single VM + Docker**. It is not presented as a multi-user or highly available deployment model.
