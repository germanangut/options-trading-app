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
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 1.2,
      provider: "alpaca",
      request: {
        profile: "balanced",
        ticker_group: "tech",
        selected_strategy_keys: ["bull_put_spread"],
        dte_min: 20,
        dte_max: 35,
        min_score: 65,
        min_pop: null,
        min_ror: null,
        min_consistency: 3,
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
  it("shows partial results messaging when some tickers fail", () => {
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

    expect(screen.getByText("Partial results available")).toBeInTheDocument();
    expect(
      screen.getByText("2 ticker(s) failed or were unavailable during the latest scan, so the alert list may be incomplete."),
    ).toBeInTheDocument();
  });

  it("suggests widening parameters when a healthy run has no alerts", () => {
    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useLatestScan>);

    render(<AlertsPage />);

    expect(screen.getByText("No alerts")).toBeInTheDocument();
    expect(
      screen.getByText("Nothing currently cleared the strongest alert thresholds. If you want a wider review set, broaden the ticker group or lower the score floor."),
    ).toBeInTheDocument();
  });
});