# Options Trading App

A modular Python-based options scanning dashboard for directional credit spread strategies. The app evaluates bull put spreads and bear call spreads across configured ticker groups, ranks opportunities using probability-of-profit (POP) and return-on-risk (ROR), and generates alerts with historical stability insights.

## What it does

- Fetches option chain data from Alpaca when credentials are available.
- Falls back to local mock data when Alpaca access is not configured.
- Builds and evaluates credit spreads for both bull put and bear call strategies.
- Scores opportunities using configurable POP/ROR weighting.
- Applies screening rules for open interest, strike sanity, and volatility context.
- Generates alerts, compact summaries, score explanations, and trend insights.
- Persists daily run history under `.history` and supports trend/stability analysis.

## Key features

- `main.py` is the CLI entry point that parses arguments and orchestrates scanning.
- `engine.py` is the core scanning engine containing all business logic.
- `app.py` provides a Streamlit UI for interactive scanning.
- Configurable profiles: `conservative`, `balanced`, and `aggressive`.
- Built-in ticker groups such as `tech`, `index`, and `mixed`.
- Customizable DTE window and scoring thresholds via CLI or `config.yaml`.
- Alerts export to CSV via `--export-csv`.
- Compact output, explain-score output, daily summary, and alerts-only JSON modes.

## Architecture

The application follows a clean separation of concerns:

- **CLI Layer** (`main.py`): Thin wrapper that parses command-line arguments, calls the scanning engine, and formats output based on requested mode.
- **Business Logic Layer** (`engine.py`): Core scanning engine containing all market data processing, spread evaluation, filtering, and result enrichment logic.
- **Presentation Layer** (`app.py`, `ui/`): Streamlit-based web interface for interactive scanning and visualization.
- **Supporting Modules**: Data access, configuration, metrics calculation, persistence utilities, and centralized runtime settings.

### Runtime settings

The project includes a lightweight `settings.py` layer to centralize runtime configuration resolution. It merges values from:

1. built-in defaults
2. `config.yaml`
3. CLI overrides passed into `engine.py`
4. environment variables for Alpaca credentials and base URLs

This keeps configuration behavior backward-compatible while providing a single place to resolve runtime settings.

This modular design enables:
- Easy testing of business logic in isolation
- Multiple entry points (CLI, web UI, API)
- Clear separation between interface and implementation
- Maintainable and extensible codebase

## Installation

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install requests pyyaml python-dotenv
```

3. If you want the Streamlit UI:

```bash
pip install streamlit
```

4. Optionally create `.env` with Alpaca credentials:

```text
ALPACA_API_KEY=your_api_key
ALPACA_API_SECRET=your_api_secret
ALPACA_DATA_BASE_URL=https://data.alpaca.markets
ALPACA_TRADING_BASE_URL=https://paper-api.alpaca.markets
```

## Configuration

The `config.yaml` file can define default run parameters:

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

## Usage

Run the scanner from the project root:

```bash
python main.py --profile balanced --group tech --alerts-only
```

Common flags:

- `--profile <name>` — choose one of `conservative`, `balanced`, `aggressive`
- `--group <name>` — choose one of `tech`, `index`, `mixed`
- `--tickers <T1,T2,...>` — override ticker list manually
- `--alerts-only` — output only alert data as JSON
- `--compact` — print a compact summary report
- `--explain-score` — print detailed scoring explanations
- `--daily-summary` — print a human-readable daily summary
- `--export-csv` — save alerts to `exports/alerts_latest.csv`
- `--trend-insights` — print historical trend insights from `.history`

Run the Streamlit dashboard:

```bash
streamlit run app.py
```

## Docker usage

Build the image:

```bash
docker build -t options-trading-app .
```

Run the Streamlit UI:

```bash
docker run --rm -p 8501:8501 options-trading-app
```

Then open `http://localhost:8501` in your browser.

Run the CLI entry point inside the container:

```bash
docker run --rm options-trading-app python main.py --profile balanced --group tech --alerts-only
```

## Ticker groups

The project includes these ticker groups by default:

- `tech`: `NVDA`, `TSLA`, `META`, `AAPL`, `MSFT`
- `index`: `SPY`, `QQQ`, `IWM`
- `mixed`: `SPY`, `QQQ`, `AAPL`, `MSFT`, `NVDA`

## How scoring works

- `POP` is derived from the selected short option delta.
- `ROR` is computed with net credit relative to maximum risk.
- Spread quality is determined by threshold rules, including open interest and strike sanity.
- Qualified spreads are labeled `High Quality`, `Near Miss`, or `Rejected`.
- The system applies consistency and volatility adjustments before ranking.

## Notes

- Market data is cached under `.cache` for fast repeated scans.
- Historical scans are appended to `.history/run_<date>.jsonl`.
- If Alpaca credentials are missing, the app uses built-in mock option data.

## License

This project is released under the terms of the included `LICENSE`.

