import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

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

afterEach(() => {
  cleanup();
});

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
  it("renders the grouped scan command structure with an anchored run zone and expert toggle", () => {
    const mutate = vi.fn();

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useLatestScan>);
    vi.mocked(useRunScan).mockReturnValue({
      isPending: false,
      isError: false,
      mutate,
    } as unknown as ReturnType<typeof useRunScan>);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("sidebar-mode-switch")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-posture")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-market-focus")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-direction")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-timing")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-shortlist-style")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-action-zone")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-plan-summary")).toBeInTheDocument();
    expect(screen.getByTestId("run-scan-button")).toHaveClass("bg-accent", "text-surface-0");
    expect(screen.getByTestId("reset-scan-button")).toBeInTheDocument();
    expect(screen.queryByTestId("expert-fields")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("mode-expert"));

    expect(screen.getByTestId("expert-fields")).toBeInTheDocument();
  });

  it("renders a short interpreted plan summary that updates as guided choices change", () => {
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

    expect(screen.getByText("Balanced scan across Tech for either direction.")).toBeInTheDocument();
    expect(screen.getByText("Expiring in 3-5 weeks with moderate filtering and some history.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Bearish/i }));
    fireEvent.click(screen.getByRole("button", { name: /Later/i }));
    fireEvent.click(screen.getByRole("button", { name: /Stricter/i }));
    fireEvent.click(screen.getByRole("button", { name: /Repeat setups/i }));

    expect(screen.getByText("Balanced scan across Tech for bearish direction.")).toBeInTheDocument();
    expect(screen.getByText("Expiring in 5-8 weeks with stricter filtering and repeat setups.")).toBeInTheDocument();
  });

  it("keeps guided selections mapped to the same scan request fields when running a scan", () => {
    const mutate = vi.fn();

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useLatestScan>);
    vi.mocked(useRunScan).mockReturnValue({
      isPending: false,
      isError: false,
      mutate,
    } as unknown as ReturnType<typeof useRunScan>);

    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: /Aggressive/i }));
    fireEvent.click(screen.getByRole("button", { name: /Index/i }));
    fireEvent.click(screen.getByRole("button", { name: /Bearish/i }));
    fireEvent.click(screen.getByRole("button", { name: /Later/i }));
    fireEvent.click(screen.getByRole("button", { name: /Stricter/i }));
    fireEvent.click(screen.getByRole("button", { name: /Repeat setups/i }));
    fireEvent.click(screen.getByTestId("run-scan-button"));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({
        profile: "aggressive",
        ticker_group: "index",
        selected_strategy_keys: ["bear_call_spread"],
        dte_min: 35,
        dte_max: 56,
        min_score: 75,
        min_consistency: 5,
      }),
    );
  });
});