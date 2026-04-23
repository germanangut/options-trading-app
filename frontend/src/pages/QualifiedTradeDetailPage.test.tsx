import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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

vi.mock("../features/scans/hooks/useTradePayoff", () => ({
  useTradePayoff: vi.fn(),
}));

vi.mock("../features/scans/hooks/useTradeVariants", () => ({
  useTradeVariants: vi.fn(),
}));

vi.mock("../features/scans/hooks/useWorkbenchScenario", () => ({
  useWorkbenchScenario: vi.fn(),
}));

vi.mock("../features/scans/hooks/useTradeLifecycle", () => ({
  useTradeLifecycle: vi.fn(),
  useUpsertTradeLifecycle: vi.fn(),
}));

vi.mock("../components/ui/ExecutionTicketPanel", () => ({
  ExecutionTicketPanel: () => <div data-testid="execution-ticket-panel">Execution Ticket Panel</div>,
}));

const { useScanById } = await import("../features/scans/hooks/useScanById");

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const { useTradeDetail } = await import("../features/scans/hooks/useTradeDetail");
const { useTradePayoff } = await import("../features/scans/hooks/useTradePayoff");
const { useTradeLifecycle, useUpsertTradeLifecycle } = await import("../features/scans/hooks/useTradeLifecycle");
const { useTradeVariants } = await import("../features/scans/hooks/useTradeVariants");
const { useWorkbenchScenario } = await import("../features/scans/hooks/useWorkbenchScenario");

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
    vi.mocked(useTradePayoff).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        source_type: "qualified_trade",
        source_id: "trade_1",
        payoff: {
          strategy_key: "bull_put_spread",
          ticker: "AAPL",
          quantity: 1,
          underlying_price_reference: 191.2,
          short_strike: 180,
          long_strike: 175,
          net_credit: 1.45,
          spread_width: 5,
          max_profit: 145,
          max_loss: 355,
          breakeven_low: 178.55,
          breakeven_high: null,
          profit_zone: "Underlying >= 180.00",
          loss_zone: "Underlying <= 175.00",
          expiration_summary: "Bull put spread keeps full credit above the short strike.",
          price_grid: [160, 170, 180, 190, 200],
          payoff_points: [
            { underlying_price: 160, expiration_payoff: -355 },
            { underlying_price: 170, expiration_payoff: -355 },
            { underlying_price: 180, expiration_payoff: 145 },
            { underlying_price: 190, expiration_payoff: 145 },
            { underlying_price: 200, expiration_payoff: 145 },
          ],
        },
      },
    } as unknown as ReturnType<typeof useTradePayoff>);
    vi.mocked(useTradeVariants).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        scan_id: "scan_trade",
        trade_id: "trade_1",
        strategy_key: "bull_put_spread",
        underlying_price_reference: 191.2,
        ticker: "AAPL",
        variants: [
          {
            variant_type: "baseline",
            strategy_key: "bull_put_spread",
            reference_trade_id: "trade_1",
            short_strike: 180,
            long_strike: 175,
            expiration_date: "2026-05-15",
            net_credit: 1.45,
            spread_width: 5,
            max_profit: 145,
            max_loss: 355,
            breakeven: 178.55,
            label: "Current scanned setup",
            rationale: "The original scanned candidate as selected by the engine.",
            is_credit_estimated: false,
            comparison: {
              is_baseline: true,
              delta_net_credit: 0,
              delta_max_profit: 0,
              delta_max_loss: 0,
              delta_breakeven: 0,
              delta_spread_width: 0,
              risk_reward_ratio: 0.4085,
              delta_risk_reward_ratio: 0,
              summary: "Current scanned setup.",
              safety_tradeoff: "Reference trade.",
            },
            payoff: {
              strategy_key: "bull_put_spread",
              ticker: "AAPL",
              quantity: 1,
              underlying_price_reference: 191.2,
              short_strike: 180,
              long_strike: 175,
              net_credit: 1.45,
              spread_width: 5,
              max_profit: 145,
              max_loss: 355,
              breakeven_low: 178.55,
              breakeven_high: null,
              profit_zone: "Underlying >= 180.00",
              loss_zone: "Underlying <= 175.00",
              expiration_summary: "Bull put spread keeps full credit above the short strike.",
              price_grid: [160, 170, 180, 190, 200],
              payoff_points: [
                { underlying_price: 160, expiration_payoff: -355 },
                { underlying_price: 170, expiration_payoff: -355 },
                { underlying_price: 180, expiration_payoff: 145 },
                { underlying_price: 190, expiration_payoff: 145 },
                { underlying_price: 200, expiration_payoff: 145 },
              ],
            },
          },
          {
            variant_type: "conservative",
            strategy_key: "bull_put_spread",
            reference_trade_id: "trade_1",
            short_strike: 179,
            long_strike: 174,
            expiration_date: "2026-05-15",
            net_credit: 1.3,
            spread_width: 5,
            max_profit: 130,
            max_loss: 370,
            breakeven: 177.7,
            label: "Lower credit, more room for the trade to work",
            rationale: "Short strike shifted down.",
            is_credit_estimated: true,
            comparison: {
              is_baseline: false,
              delta_net_credit: -0.15,
              delta_max_profit: -15,
              delta_max_loss: 15,
              delta_breakeven: -0.85,
              delta_spread_width: 0,
              risk_reward_ratio: 0.3514,
              delta_risk_reward_ratio: -0.0571,
              summary: "Further out-of-the-money short strike, lower credit, more room to work.",
              safety_tradeoff: "Further out-of-the-money short strike, lower credit, more room to work.",
            },
            payoff: {
              strategy_key: "bull_put_spread",
              ticker: "AAPL",
              quantity: 1,
              underlying_price_reference: 191.2,
              short_strike: 179,
              long_strike: 174,
              net_credit: 1.3,
              spread_width: 5,
              max_profit: 130,
              max_loss: 370,
              breakeven_low: 177.7,
              breakeven_high: null,
              profit_zone: "Underlying >= 179.00",
              loss_zone: "Underlying <= 174.00",
              expiration_summary: "Conservative payoff profile.",
              price_grid: [160, 170, 180, 190, 200],
              payoff_points: [
                { underlying_price: 160, expiration_payoff: -370 },
                { underlying_price: 170, expiration_payoff: -370 },
                { underlying_price: 180, expiration_payoff: 130 },
                { underlying_price: 190, expiration_payoff: 130 },
                { underlying_price: 200, expiration_payoff: 130 },
              ],
            },
          },
          {
            variant_type: "max_credit",
            strategy_key: "bull_put_spread",
            reference_trade_id: "trade_1",
            short_strike: 181,
            long_strike: 176,
            expiration_date: "2026-05-15",
            net_credit: 1.62,
            spread_width: 5,
            max_profit: 162,
            max_loss: 338,
            breakeven: 179.38,
            label: "Higher premium, tighter room for error",
            rationale: "Short strike shifted up.",
            is_credit_estimated: true,
            comparison: {
              is_baseline: false,
              delta_net_credit: 0.17,
              delta_max_profit: 17,
              delta_max_loss: -17,
              delta_breakeven: 0.83,
              delta_spread_width: 0,
              risk_reward_ratio: 0.4793,
              delta_risk_reward_ratio: 0.0708,
              summary: "Closer short strike, richer premium, tighter room for error.",
              safety_tradeoff: "Closer short strike, richer premium, tighter room for error.",
            },
            payoff: {
              strategy_key: "bull_put_spread",
              ticker: "AAPL",
              quantity: 1,
              underlying_price_reference: 191.2,
              short_strike: 181,
              long_strike: 176,
              net_credit: 1.62,
              spread_width: 5,
              max_profit: 162,
              max_loss: 338,
              breakeven_low: 179.38,
              breakeven_high: null,
              profit_zone: "Underlying >= 181.00",
              loss_zone: "Underlying <= 176.00",
              expiration_summary: "Max credit payoff profile.",
              price_grid: [160, 170, 180, 190, 200],
              payoff_points: [
                { underlying_price: 160, expiration_payoff: -338 },
                { underlying_price: 170, expiration_payoff: -338 },
                { underlying_price: 180, expiration_payoff: 40 },
                { underlying_price: 190, expiration_payoff: 162 },
                { underlying_price: 200, expiration_payoff: 162 },
              ],
            },
          },
        ],
      },
    } as unknown as ReturnType<typeof useTradeVariants>);
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
    expect(screen.getByText("Expiration payoff")).toBeInTheDocument();
    expect(screen.getAllByText("Max Profit").length).toBeGreaterThan(0);
    expect(screen.getAllByText("$145.00").length).toBeGreaterThan(0);
    expect(screen.getAllByText("$355.00").length).toBeGreaterThan(0);
    expect(screen.getAllByText("$178.55").length).toBeGreaterThan(0);
    expect(screen.getByText("Profit zone")).toBeInTheDocument();
    expect(screen.getByText("Underlying >= 180.00")).toBeInTheDocument();
    expect(screen.getByText("Strike ladder")).toBeInTheDocument();
    expect(screen.getByText("What to confirm next")).toBeInTheDocument();
    expect(screen.getByText("Portfolio context")).toBeInTheDocument();
    expect(screen.getByText("Execution preparation")).toBeInTheDocument();
    expect(screen.getByText("Variant comparison")).toBeInTheDocument();
    expect(screen.getByText("Payoff shape and trade-off lab")).toBeInTheDocument();
    expect(screen.getAllByText("Current scanned setup").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Lower credit, more room for the trade to work").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Higher premium, tighter room for error").length).toBeGreaterThan(0);
    expect(screen.getByText("Change vs baseline")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Conservative" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Max Credit" })).toBeInTheDocument();
    expect(screen.getByTestId("execution-ticket-panel")).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("tab", { name: "Max Credit" }));
    expect(screen.getByText("Closer short strike, richer premium, tighter room for error.")).toBeInTheDocument();
  });

  it("shows Add note prompt when no note is saved", () => {
    vi.mocked(useScanById).mockReturnValue({
      isLoading: false, isError: false, data: buildScan(),
    } as ReturnType<typeof useScanById>);
    vi.mocked(useTradeDetail).mockReturnValue({
      isLoading: false, isError: false, data: buildDetail(),
    } as ReturnType<typeof useTradeDetail>);
    vi.mocked(useTradePayoff).mockReturnValue({
      isLoading: false,
      isError: false,
      data: null,
    } as unknown as ReturnType<typeof useTradePayoff>);
    vi.mocked(useTradeVariants).mockReturnValue({
      isLoading: false,
      isError: false,
      data: null,
    } as unknown as ReturnType<typeof useTradeVariants>);
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

    expect(screen.getByText("Payoff model is unavailable for this trade.")).toBeInTheDocument();
    expect(screen.getByText("Add a note about this trade…")).toBeInTheDocument();
    expect(screen.getByText("Visual strategy lab is unavailable because a baseline payoff structure could not be loaded for this trade.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit" })).toBeNull();
  });

  it("shows baseline-only lab state when no clean alternatives are available", () => {
    vi.mocked(useScanById).mockReturnValue({
      isLoading: false, isError: false, data: buildScan(),
    } as ReturnType<typeof useScanById>);
    vi.mocked(useTradeDetail).mockReturnValue({
      isLoading: false, isError: false, data: buildDetail(),
    } as ReturnType<typeof useTradeDetail>);
    vi.mocked(useTradePayoff).mockReturnValue({
      isLoading: false,
      isError: false,
      data: null,
    } as unknown as ReturnType<typeof useTradePayoff>);
    vi.mocked(useTradeVariants).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        scan_id: "scan_trade",
        trade_id: "trade_1",
        strategy_key: "bull_put_spread",
        underlying_price_reference: 191.2,
        ticker: "AAPL",
        variants: [
          {
            variant_type: "baseline",
            strategy_key: "bull_put_spread",
            reference_trade_id: "trade_1",
            short_strike: 180,
            long_strike: 175,
            expiration_date: "2026-05-15",
            net_credit: 1.45,
            spread_width: 5,
            max_profit: 145,
            max_loss: 355,
            breakeven: 178.55,
            label: "Current scanned setup",
            rationale: "The original scanned candidate as selected by the engine.",
            is_credit_estimated: false,
            comparison: {
              is_baseline: true,
              delta_net_credit: 0,
              delta_max_profit: 0,
              delta_max_loss: 0,
              delta_breakeven: 0,
              delta_spread_width: 0,
              risk_reward_ratio: 0.4085,
              delta_risk_reward_ratio: 0,
              summary: "Current scanned setup.",
              safety_tradeoff: "Reference trade.",
            },
            payoff: {
              strategy_key: "bull_put_spread",
              ticker: "AAPL",
              quantity: 1,
              underlying_price_reference: 191.2,
              short_strike: 180,
              long_strike: 175,
              net_credit: 1.45,
              spread_width: 5,
              max_profit: 145,
              max_loss: 355,
              breakeven_low: 178.55,
              breakeven_high: null,
              profit_zone: "Underlying >= 180.00",
              loss_zone: "Underlying <= 175.00",
              expiration_summary: "Baseline payoff profile.",
              price_grid: [160, 170, 180, 190, 200],
              payoff_points: [
                { underlying_price: 160, expiration_payoff: -355 },
                { underlying_price: 170, expiration_payoff: -355 },
                { underlying_price: 180, expiration_payoff: 145 },
                { underlying_price: 190, expiration_payoff: 145 },
                { underlying_price: 200, expiration_payoff: 145 },
              ],
            },
          },
        ],
      },
    } as unknown as ReturnType<typeof useTradeVariants>);
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

    expect(screen.getByText("No clean variant was found for this setup, so only baseline is available for visual analysis.")).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: "Conservative" })).toBeNull();
    expect(screen.queryByRole("tab", { name: "Max Credit" })).toBeNull();
  });
});