import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { ScanResult } from "../types/api";
import { QualifiedTradesPage } from "./QualifiedTradesPage";


vi.mock("../features/scans/hooks/useLatestScan", () => ({
  useLatestScan: vi.fn(),
}));


const { useLatestScan } = await import("../features/scans/hooks/useLatestScan");


function buildPartialScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_partial",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread", "bear_call_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.6, ror_weight: 0.4 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 1.25,
      provider: "alpaca-contracts-plus-symbol-snapshots",
      request: {
        profile: "balanced",
        ticker_group: "tech",
        selected_strategy_keys: ["bull_put_spread", "bear_call_spread"],
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
      missing_tickers: ["NVDA"],
      provider_errors: [],
      alerts_export_path: null,
      top_overall_identity: null,
      partial_result: true,
      performance: { provider_duration_ms: 820 },
      cache: {},
    },
  };
}


describe("QualifiedTradesPage", () => {
  it("explains that an empty board may reflect partial coverage", () => {
    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildPartialScan(),
    } as ReturnType<typeof useLatestScan>);

    render(
      <MemoryRouter>
        <QualifiedTradesPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("No qualified trades under partial coverage")).toBeInTheDocument();
    expect(
      screen.getByText("Some tickers were unavailable during the scan, so this empty board may reflect incomplete market coverage."),
    ).toBeInTheDocument();
  });
});