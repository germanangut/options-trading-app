import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ScanResult } from "../types/api";
import { AlertsPage } from "./AlertsPage";


vi.mock("../features/scans/hooks/useLatestScan", () => ({
  useLatestScan: vi.fn(),
}));


const { useLatestScan } = await import("../features/scans/hooks/useLatestScan");


function buildScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_alerts",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.6, ror_weight: 0.4 },
      alert_thresholds: { min_score: 55, min_consistency: 1 },
      execution_time_seconds: 1.2,
      provider: "alpaca",
      request: {
        profile: "balanced",
        ticker_group: "tech",
        selected_strategy_keys: ["bull_put_spread"],
        dte_min: 20,
        dte_max: 35,
        min_score: 55,
        min_pop: null,
        min_ror: null,
        min_consistency: 1,
        alerts_only: false,
        use_mock_data: null,
      },
    },
    summary: {
      qualified_count: 0,
      near_miss_count: 0,
      top_overall: null,
      top_bull_put: null,
      top_bear_call: null,
    },
    qualified_trades: [],
    alerts: [],
    near_miss_trades: [],
    ticker_diagnostics: [],
    portfolio_summary: {},
    history_context: {},
    daily_summary: {},
    diagnostics: {
      missing_tickers: [],
      provider_errors: [],
      alerts_export_path: null,
      top_overall_identity: null,
      partial_result: false,
      performance: {},
      cache: {},
    },
  };
}


describe("AlertsPage", () => {
  it("keeps partial coverage out of the main page body when some tickers fail", () => {
    const scan = buildScan();
    scan.diagnostics.partial_result = true;
    scan.diagnostics.missing_tickers = ["AAPL", "NVDA"];
    scan.diagnostics.performance = { failed_ticker_count: 2 };

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: scan,
    } as ReturnType<typeof useLatestScan>);

    render(<AlertsPage />);

    expect(screen.queryByText("Partial results available")).not.toBeInTheDocument();
    expect(screen.getByText("No alerts under partial coverage")).toBeInTheDocument();
    expect(screen.getByText("Some tickers were unavailable during the scan, so review diagnostics before treating this as a fully clean market pass.")).toBeInTheDocument();
  });

  it("explains no alerts with zero qualified trades present", () => {
    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useLatestScan>);

    render(<AlertsPage />);

    expect(screen.getAllByText("No alerts this run").length).toBeGreaterThan(0);
    expect(
      screen.getByText(/No qualified trades or alerts were produced in this run/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No qualified trades were found this run either/),
    ).toBeInTheDocument();
  });

  it("explains no alerts when qualified trades exist but none passed alert filters", () => {
    const scan = buildScan();
    scan.summary = {
      qualified_count: 2,
      near_miss_count: 1,
      top_overall: null,
      top_bull_put: null,
      top_bear_call: null,
    };
    scan.qualified_trades = [
      {
        trade_id: "trade_msft",
        ticker: "MSFT",
        strategy_type: "bull_put_spread",
        strategy_key: "bull_put_spread",
        strategy_label: "Bull Put Spread",
        directional_bias: "bullish",
        expiration_date: "2026-05-15",
        DTE: 28,
        short_strike: 390,
        long_strike: 385,
        POP: 66,
        ROR: 18,
        score: 57,
        adjusted_score: 58,
        label: "High Quality",
        decision_summary: null,
        status_reason: "Cleared Balanced thresholds.",
        volatility_context: "balanced_premium",
        stability_level: "new",
        stability_count: 0,
      },
    ];

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: scan,
    } as ReturnType<typeof useLatestScan>);

    render(<AlertsPage />);

    expect(screen.getAllByText("No alerts this run").length).toBeGreaterThan(0);
    // emptyState message from selector
    expect(
      screen.getByText(/Qualified trades were found, but none passed the tighter alert filters/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Alerts surface only the strongest candidates/)).toBeInTheDocument();
    // follow-up band (qualified > 0 path)
    expect(
      screen.getByText(/Qualified trades were found this run, but none passed the tighter alert filters/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Adjust score and signal-history filters in Expert mode/)).toBeInTheDocument();
  });
});