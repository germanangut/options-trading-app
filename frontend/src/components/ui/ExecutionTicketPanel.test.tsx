import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ExecutionTicketPanel } from "./ExecutionTicketPanel";
import type { CreateTicketPayload, ExecutionTicket } from "../../types/api";

vi.mock("../../features/scans/hooks/useExecutionTickets", () => ({
  useExecutionTicketsByTrade: vi.fn(),
  useCreateExecutionTicket: vi.fn(),
  usePatchExecutionTicket: vi.fn(),
  useSubmitExecutionTicketToPaper: vi.fn(),
  useRefreshExecutionTicketFromPaper: vi.fn(),
}));

const hooksModule = await import("../../features/scans/hooks/useExecutionTickets");

const tradeSnapshot: CreateTicketPayload = {
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
};

function buildTicket(overrides?: Partial<ExecutionTicket>): ExecutionTicket {
  return {
    ticket_id: "ticket_1",
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
    execution_status: "ready",
    note: "Review complete",
    created_at: "2026-04-23T10:00:00Z",
    updated_at: "2026-04-23T10:00:00Z",
    broker_order_id: null,
    broker_status_raw: null,
    broker_submitted_at: null,
    broker_updated_at: null,
    last_submission_payload: null,
    last_submission_response: null,
    submission_error_message: null,
    ...overrides,
  };
}

function mockDefaultHooks(ticket: ExecutionTicket | null) {
  vi.mocked(hooksModule.useExecutionTicketsByTrade).mockReturnValue({
    data: ticket ? [ticket] : [],
    isLoading: false,
    isError: false,
  } as unknown as ReturnType<typeof hooksModule.useExecutionTicketsByTrade>);

  vi.mocked(hooksModule.useCreateExecutionTicket).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof hooksModule.useCreateExecutionTicket>);

  vi.mocked(hooksModule.usePatchExecutionTicket).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof hooksModule.usePatchExecutionTicket>);

  vi.mocked(hooksModule.useSubmitExecutionTicketToPaper).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof hooksModule.useSubmitExecutionTicketToPaper>);

  vi.mocked(hooksModule.useRefreshExecutionTicketFromPaper).mockReturnValue({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  } as unknown as ReturnType<typeof hooksModule.useRefreshExecutionTicketFromPaper>);
}

afterEach(() => {
  vi.clearAllMocks();
});

describe("ExecutionTicketPanel", () => {
  it("shows submit guidance when no ticket exists and lifecycle is ready", () => {
    mockDefaultHooks(null);

    render(
      <ExecutionTicketPanel
        tradeId="trade_1"
        scanId="scan_1"
        tradeSnapshot={tradeSnapshot}
        lifecycleState="execution_ready"
      />,
    );

    expect(screen.getByRole("button", { name: "Prepare execution ticket" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit to Paper" })).toBeNull();
  });

  it("submits a ready ticket to paper and renders success state", () => {
    const readyTicket = buildTicket({ execution_status: "ready" });
    mockDefaultHooks(readyTicket);

    const submitMutate = vi.fn((ticketId: string, options?: { onSuccess?: (ticket: ExecutionTicket) => void }) => {
      options?.onSuccess?.(buildTicket({ execution_status: "accepted", broker_order_id: "order_1", broker_status_raw: "accepted" }));
    });

    vi.mocked(hooksModule.useSubmitExecutionTicketToPaper).mockReturnValue({
      mutate: submitMutate,
      isPending: false,
      error: null,
    } as unknown as ReturnType<typeof hooksModule.useSubmitExecutionTicketToPaper>);

    render(
      <ExecutionTicketPanel
        tradeId="trade_1"
        scanId="scan_1"
        tradeSnapshot={tradeSnapshot}
        lifecycleState="execution_ready"
      />,
    );

    const submitButton = screen.getByRole("button", { name: "Submit to Paper" });
    expect(submitButton).toBeEnabled();

    fireEvent.click(submitButton);

    expect(submitMutate).toHaveBeenCalledWith("ticket_1", expect.any(Object));
    expect(screen.getByText("Ticket submitted to paper broker successfully.")).toBeInTheDocument();
  });
});
