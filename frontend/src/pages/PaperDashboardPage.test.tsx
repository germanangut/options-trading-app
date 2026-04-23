import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { PaperDashboardPage } from "./PaperDashboardPage";

vi.mock("../features/scans/hooks/usePaperDashboard", () => ({
  usePaperDashboard: vi.fn(),
  useRefreshPaperDashboard: vi.fn(),
}));

const hooks = await import("../features/scans/hooks/usePaperDashboard");

function mockRefresh() {
  vi.mocked(hooks.useRefreshPaperDashboard).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof hooks.useRefreshPaperDashboard>);
}

describe("PaperDashboardPage", () => {
  it("renders pending/open/closed sections with dashboard data", () => {
    mockRefresh();
    vi.mocked(hooks.usePaperDashboard).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        pending_orders: [
          {
            ticket_id: "ticket_pending",
            trade_id: "trade_1",
            source_scan_id: "scan_1",
            ticker: "AAPL",
            strategy_key: "bull_put_spread",
            strategy_label: "Bull Put Spread",
            directional_bias: "bullish",
            expiration_date: "2026-05-15",
            short_strike: 180,
            long_strike: 175,
            underlying_price_at_creation: 191.2,
            net_credit_estimate: 1.45,
            max_risk_estimate: 355,
            adjusted_score_at_creation: 74,
            quantity: 1,
            order_intent: "open_credit",
            execution_status: "accepted",
            note: null,
            created_at: "2026-04-23T10:00:00Z",
            updated_at: "2026-04-23T10:01:00Z",
            broker_order_id: "order_1",
            broker_status_raw: "accepted",
            broker_submitted_at: "2026-04-23T10:00:30Z",
            broker_updated_at: "2026-04-23T10:01:00Z",
            last_submission_payload: null,
            last_submission_response: null,
            submission_error_message: null,
          },
        ],
        open_positions: [
          {
            symbol: "AAPL260515P00180000",
            ticker: "AAPL",
            qty: 1,
            side: "long",
            avg_entry_price: 1.1,
            market_value: 120,
            cost_basis: 110,
            unrealized_pl: 10,
            unrealized_plpc: 0.09,
            realized_pl: null,
            broker_updated_at: "2026-04-23T10:02:00Z",
            linked_ticket_id: "ticket_filled",
            strategy_label: "Bull Put Spread",
            directional_bias: "bullish",
            ticket_execution_status: "filled",
            estimated_credit_or_debit: 1.45,
          },
        ],
        closed_trades: [
          {
            ticket_id: "ticket_closed",
            trade_id: "trade_2",
            source_scan_id: "scan_1",
            ticker: "MSFT",
            strategy_key: "bear_call_spread",
            strategy_label: "Bear Call Spread",
            directional_bias: "bearish",
            expiration_date: "2026-05-15",
            short_strike: 320,
            long_strike: 325,
            underlying_price_at_creation: 315.2,
            net_credit_estimate: 1.05,
            max_risk_estimate: 395,
            adjusted_score_at_creation: 68,
            quantity: 1,
            order_intent: "open_credit",
            execution_status: "rejected",
            note: null,
            created_at: "2026-04-23T10:00:00Z",
            updated_at: "2026-04-23T10:03:00Z",
            broker_order_id: "order_2",
            broker_status_raw: "rejected",
            broker_submitted_at: "2026-04-23T10:02:00Z",
            broker_updated_at: "2026-04-23T10:03:00Z",
            last_submission_payload: null,
            last_submission_response: null,
            submission_error_message: "insufficient buying power",
          },
        ],
        recent_orders: [
          {
            broker_order_id: "order_1",
            symbol: "AAPL260515P00180000",
            status: "accepted",
            order_type: "limit",
            side: "buy",
            qty: 1,
            filled_qty: 0,
            filled_avg_price: null,
            submitted_at: "2026-04-23T10:00:30Z",
            updated_at: "2026-04-23T10:01:00Z",
          },
        ],
        summary: {
          pending_count: 1,
          open_positions_count: 1,
          closed_count: 1,
          recent_orders_count: 1,
        },
        data_source: {
          mode: "hybrid",
          app_history_source: "execution_ticket",
          broker_live_data_available: true,
          broker_live_data_warning: null,
          status_refresh_attempted: false,
          status_refresh_errors: [],
          generated_at: "2026-04-23T10:04:00Z",
        },
      },
    } as unknown as ReturnType<typeof hooks.usePaperDashboard>);

    render(
      <MemoryRouter>
        <PaperDashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Queued or in-flight paper tickets")).toBeInTheDocument();
    expect(screen.getByText("Live open exposure")).toBeInTheDocument();
    expect(screen.getByText("Terminal ticket outcomes")).toBeInTheDocument();
    expect(screen.getByText("AAPL - Bull Put Spread")).toBeInTheDocument();
    expect(screen.queryByText("No recent broker orders", { exact: false })).not.toBeInTheDocument();
  });

  it("renders empty states when there is no paper activity yet", () => {
    mockRefresh();
    vi.mocked(hooks.usePaperDashboard).mockReturnValue({
      isLoading: false,
      isError: false,
      data: {
        pending_orders: [],
        open_positions: [],
        closed_trades: [],
        recent_orders: [],
        summary: {
          pending_count: 0,
          open_positions_count: 0,
          closed_count: 0,
          recent_orders_count: 0,
        },
        data_source: {
          mode: "hybrid",
          app_history_source: "execution_ticket",
          broker_live_data_available: false,
          broker_live_data_warning: "Paper credentials are not configured.",
          status_refresh_attempted: false,
          status_refresh_errors: [],
          generated_at: "2026-04-23T10:04:00Z",
        },
      },
    } as unknown as ReturnType<typeof hooks.usePaperDashboard>);

    render(
      <MemoryRouter>
        <PaperDashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("No pending paper orders")).toBeInTheDocument();
    expect(screen.getByText("No open paper positions")).toBeInTheDocument();
    expect(screen.getByText("No closed paper trades")).toBeInTheDocument();
  });
});
