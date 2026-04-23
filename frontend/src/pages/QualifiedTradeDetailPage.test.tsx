import { render, screen } from "@testing-library/react";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ScanResult, TradeDetailResponse } from "../types/api";
import { QualifiedTradeDetailPage } from "./QualifiedTradeDetailPage";

vi.mock("../features/scans/hooks/useScanById", () => ({
  useScanById: vi.fn(),
}));

vi.mock("../features/scans/hooks/useTradeDetail", () => ({
  useTradeDetail: vi.fn(),
}));

vi.mock("../features/scans/hooks/useTradeLifecycle", () => ({
  useTradeLifecycle: vi.fn(),
  useUpsertTradeLifecycle: vi.fn(),
}));

const { useScanById } = await import("../features/scans/hooks/useScanById");

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const { useTradeDetail } = await import("../features/scans/hooks/useTradeDetail");
const { useTradeLifecycle, useUpsertTradeLifecycle } = await import("../features/scans/hooks/useTradeLifecycle");

function buildScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_trade",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.6, ror_weight: 0.4 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 1.1,
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
      qualified_count: 1,
      near_miss_count: 0,
      top_overall: null,
      top_bull_put: null,
      top_bear_call: null,
    },
    qualified_trades: [],
    alerts: [],
    near_miss_trades: [],
    ticker_diagnostics: [],
    portfolio_summary: {
      decision: {
        posture_label: "Balanced posture",
        interpretation: ["Current posture is balanced."],
        key_portfolio_signals: [],
        cautions: [],
      },
      exposure: {
        qualified: {
          top_ticker_concentration: [{ ticker: "AAPL", count: 1, share_pct: 50 }],
        },
        notes: ["Portfolio exposure remains manageable."],
      },
      position_sizing: {
        warnings: ["Size carefully against current allocation."],
      },
    },
    history_context: {
      historical_intelligence_summary: {
        metadata: { runs_analyzed: 8, signals_analyzed: 20 },
        signal_quality_summary: {
          recurring_high_quality_patterns: [{ pattern: "AAPL bull put", count: 3, average_adjusted_score: 71 }],
        },
      },
    },
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

function buildDetail(): TradeDetailResponse {
  return {
    scan_id: "scan_trade",
    scan_metadata: {
      profile: "balanced",
      ticker_group: "tech",
      generated_at: "2026-04-17T00:00:00Z",
    },
    diagnostics: {
      provider_errors: [],
      missing_tickers: [],
    },
    trade: {
      trade_id: "trade_1",
      ticker: "AAPL",
      strategy_type: "bull_put_spread",
      strategy_label: "Bull Put Spread",
      expiration_date: "2026-05-15",
      DTE: 28,
      short_strike: 180,
      long_strike: 175,
      underlying_price: 191.2,
      net_credit: 1.45,
      spread_width: 5,
      max_risk: 355,
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
      score_breakdown: {
        pop_score: 67,
        ror_score: 22,
      },
      penalties: null,
    },
  };
}

describe("QualifiedTradeDetailPage", () => {
  it("renders the execution briefing composition with strike ladder and checklist", () => {
    vi.mocked(useScanById).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildScan(),
    } as ReturnType<typeof useScanById>);
    vi.mocked(useTradeDetail).mockReturnValue({
      isLoading: false,
      isError: false,
      data: buildDetail(),
    } as ReturnType<typeof useTradeDetail>);
    vi.mocked(useTradeLifecycle).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        trade_id: "trade_1",
        lifecycle_state: "saved",
        state_updated_at: "2026-04-22T10:00:00Z",
        note: "Hold for confirmation.",
        tags: [],
        source_scan_id: "scan_trade",
        created_at: "2026-04-22T10:00:00Z",
        updated_at: "2026-04-22T10:00:00Z",
        is_default: false,
      },
    } as unknown as ReturnType<typeof useTradeLifecycle>);
    vi.mocked(useUpsertTradeLifecycle).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as unknown as ReturnType<typeof useUpsertTradeLifecycle>);

    render(
      <MemoryRouter initialEntries={["/scans/scan_trade/trades/trade_1"]}>
        <Routes>
          <Route path="/scans/:scanId/trades/:tradeId" element={<QualifiedTradeDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Why this trade surfaced")).toBeInTheDocument();
    expect(screen.getAllByText("Payoff cue").length).toBeGreaterThan(0);
    expect(screen.getByText("Strike ladder")).toBeInTheDocument();
    expect(screen.getByText("What to confirm next")).toBeInTheDocument();
    expect(screen.getByText("Portfolio context")).toBeInTheDocument();
    // Lifecycle badge renders state label
    expect(screen.getByText("Saved")).toBeInTheDocument();
    // Action buttons present
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Watch" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark Ready" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
    // Note read mode: saved note displayed as text, not in textarea
    expect(screen.getByText("Hold for confirmation.")).toBeInTheDocument();
    expect(screen.queryByRole("textbox", { name: /review note/i })).toBeNull();
    // Edit button available to enter edit mode
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    expect(screen.getAllByText("Constructive premium with steady support.").length).toBeGreaterThan(0);
    expect(screen.getByText(/Defined risk is capped near/i)).toBeInTheDocument();
  });

  it("shows Add note prompt when no note is saved", () => {
    vi.mocked(useScanById).mockReturnValue({
      isLoading: false, isError: false, data: buildScan(),
    } as ReturnType<typeof useScanById>);
    vi.mocked(useTradeDetail).mockReturnValue({
      isLoading: false, isError: false, data: buildDetail(),
    } as ReturnType<typeof useTradeDetail>);
    vi.mocked(useTradeLifecycle).mockReturnValue({
      isLoading: false, isError: false,
      data: {
        trade_id: "trade_1", lifecycle_state: "new",
        state_updated_at: "2026-04-22T10:00:00Z",
        note: null, tags: [], source_scan_id: "scan_trade",
        created_at: "2026-04-22T10:00:00Z", updated_at: "2026-04-22T10:00:00Z", is_default: false,
      },
    } as unknown as ReturnType<typeof useTradeLifecycle>);
    vi.mocked(useUpsertTradeLifecycle).mockReturnValue({
      mutate: vi.fn(), isPending: false,
    } as unknown as ReturnType<typeof useUpsertTradeLifecycle>);

    render(
      <MemoryRouter initialEntries={["/scans/scan_trade/trades/trade_1"]}>
        <Routes>
          <Route path="/scans/:scanId/trades/:tradeId" element={<QualifiedTradeDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Add a note about this trade…")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
  });
});