import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import type { ScanResult } from "../../types/api";
import { Sidebar } from "./Sidebar";

vi.mock("../../features/scans/hooks/useLatestScan", () => ({
  useLatestScan: vi.fn(),
}));

vi.mock("../../features/scans/hooks/useRunScan", () => ({
  useRunScan: vi.fn(),
}));

const { useLatestScan } = await import("../../features/scans/hooks/useLatestScan");
const { useRunScan } = await import("../../features/scans/hooks/useRunScan");

function buildScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_sidebar",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread", "bear_call_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.6, ror_weight: 0.4 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 1.25,
      provider: "alpaca",
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
      qualified_count: 2,
      near_miss_count: 1,
      top_overall: {
        trade_id: "trade_aapl",
        ticker: "AAPL",
        strategy_type: "bull_put_spread",
        strategy_label: "Bull Put Spread",
      },
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

describe("Sidebar", () => {
  it("uses prescriptive guided wording and still switches to expert controls on demand", () => {
    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useLatestScan>);
    vi.mocked(useRunScan).mockReturnValue({
      isPending: false,
      isError: false,
      mutate: vi.fn(),
    } as unknown as ReturnType<typeof useRunScan>);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByText("Tell PRIS what you want")).toBeInTheDocument();
    expect(screen.getByText("What PRIS will scan for")).toBeInTheDocument();
    expect(screen.getByText(/PRIS will scan for balanced premium trades in big tech/i)).toBeInTheDocument();
    expect(screen.queryByTestId("expert-fields")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Bearish setups/i }));
    expect(screen.getByText(/It will look for bearish setups/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Later/i }));
    expect(screen.getAllByText(/expiring later, around 5-8 weeks out/i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByTestId("mode-expert"));

    expect(screen.getByText("Direct control surface")).toBeInTheDocument();
    expect(screen.getByTestId("expert-fields")).toBeInTheDocument();
  });
});