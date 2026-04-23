import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ScanResult } from "../types/api";
import { QualifiedTradesPage } from "./QualifiedTradesPage";


vi.mock("../features/scans/hooks/useLatestScan", () => ({
  useLatestScan: vi.fn(),
}));

vi.mock("../features/scans/hooks/useTradeLifecycle", () => ({
  useLifecycleRecords: vi.fn(),
  useUpsertTradeLifecycle: vi.fn(),
}));


const { useLatestScan } = await import("../features/scans/hooks/useLatestScan");
const { useLifecycleRecords, useUpsertTradeLifecycle } = await import("../features/scans/hooks/useTradeLifecycle");

afterEach(() => {
  cleanup();
});

function mockLifecycleHooks(records: Array<{ trade_id: string; lifecycle_state: string }> = []) {
  vi.mocked(useLifecycleRecords).mockReturnValue({
    data: records,
    isLoading: false,
    isError: false,
  } as ReturnType<typeof useLifecycleRecords>);

  vi.mocked(useUpsertTradeLifecycle).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useUpsertTradeLifecycle>);
}


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
    mockLifecycleHooks();
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

    expect(screen.getByText("Partial results available")).toBeInTheDocument();
    expect(
      screen.getByText("Some tickers were unavailable during the scan, so this empty board may reflect incomplete market coverage."),
    ).toBeInTheDocument();
  });

  it("suggests widening parameters when no qualified trades are returned from a healthy run", () => {
    mockLifecycleHooks();
    const scan = buildPartialScan();
    scan.diagnostics = {
      ...scan.diagnostics,
      missing_tickers: [],
      partial_result: false,
      performance: { provider_duration_ms: 400 },
    };

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: scan,
    } as ReturnType<typeof useLatestScan>);

    render(
      <MemoryRouter>
        <QualifiedTradesPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("No qualified trades")).toBeInTheDocument();
    expect(
      screen.getByText("The latest scan did not produce any qualified opportunities. If you want a wider review set, broaden the ticker group or relax the score threshold."),
    ).toBeInTheDocument();
  });

  it("renders contained ranked trade cards for qualified opportunities", () => {
    mockLifecycleHooks([{ trade_id: "trade_1", lifecycle_state: "watching" }]);
    const scan = buildPartialScan();
    scan.diagnostics = {
      ...scan.diagnostics,
      missing_tickers: [],
      partial_result: false,
    };
    scan.summary = {
      qualified_count: 1,
      near_miss_count: 0,
      top_overall: null,
      top_bull_put: null,
      top_bear_call: null,
    };
    scan.qualified_trades = [
      {
        trade_id: "trade_1",
        ticker: "AAPL",
        strategy_type: "bull_put_spread",
        strategy_label: "Bull Put Spread",
        expiration_date: "2026-05-15",
        DTE: 28,
        short_strike: 180,
        long_strike: 175,
        POP: 67,
        ROR: 22,
        score: 72,
        adjusted_score: 74,
        label: "High Quality",
        decision_summary: "Constructive premium with steady support.",
        directional_bias: "bullish",
        status_reason: "Support held on repeated checks.",
        volatility_context: "balanced_premium",
        stability_level: "stable",
        stability_count: 3,
        net_credit: 1.45,
        spread_width: 5,
        max_risk: 355,
      },
    ];

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: scan,
    } as ReturnType<typeof useLatestScan>);

    render(
      <MemoryRouter>
        <QualifiedTradesPage />
      </MemoryRouter>,
    );

    expect(screen.getAllByText("Ranked decision board").length).toBeGreaterThan(0);
    expect(screen.getAllByText("AAPL - Bull Put Spread").length).toBeGreaterThan(0);
    expect(screen.getByText("Quality ribbon")).toBeInTheDocument();
    expect(screen.getByText("Why It Qualified")).toBeInTheDocument();
    expect(screen.getByText("Risk Frame")).toBeInTheDocument();
    expect(screen.getByText("Portfolio Impact")).toBeInTheDocument();
    // Lifecycle badge renders state label (replaces old "Lifecycle: Watching" text)
    expect(screen.getAllByText("Watching").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /review execution brief/i })).toHaveAttribute("href", "/scans/scan_partial/trades/trade_1");
  });

  it("renders lifecycle filter tabs", () => {
    mockLifecycleHooks([{ trade_id: "trade_1", lifecycle_state: "watching" }]);
    const scan = buildPartialScan();
    scan.diagnostics = { ...scan.diagnostics, missing_tickers: [], partial_result: false };
    scan.summary = { qualified_count: 1, near_miss_count: 0, top_overall: null, top_bull_put: null, top_bear_call: null };
    scan.qualified_trades = [
      {
        trade_id: "trade_1",
        ticker: "AAPL",
        strategy_type: "bull_put_spread",
        strategy_label: "Bull Put Spread",
        expiration_date: "2026-05-15",
        DTE: 28,
        short_strike: 180,
        long_strike: 175,
        POP: 67,
        ROR: 22,
        score: 72,
        adjusted_score: 74,
        label: "High Quality",
        decision_summary: "Constructive premium.",
        directional_bias: "bullish",
        status_reason: "Support held.",
        volatility_context: "balanced_premium",
        stability_level: "stable",
        stability_count: 3,
        net_credit: 1.45,
        spread_width: 5,
        max_risk: 355,
      },
    ];

    vi.mocked(useLatestScan).mockReturnValue({
      isLoading: false,
      isError: false,
      data: scan,
    } as ReturnType<typeof useLatestScan>);

    render(<MemoryRouter><QualifiedTradesPage /></MemoryRouter>);

    expect(screen.queryByRole("tab", { name: /All/i })).not.toBeNull();
    expect(screen.queryByRole("tab", { name: /New/i })).not.toBeNull();
    expect(screen.queryByRole("tab", { name: /Watching/i })).not.toBeNull();
  });
});