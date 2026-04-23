import { useEffect, useMemo, useState } from "react";

import type { CreateTicketPayload } from "../../types/api";
import { Chip } from "./Chip";
import {
  useCreateExecutionTicket,
  useExecutionTicketsByTrade,
  usePatchExecutionTicket,
} from "../../features/scans/hooks/useExecutionTickets";

type ExecutionTicketPanelProps = {
  tradeId: string;
  scanId?: string;
  tradeSnapshot: CreateTicketPayload;
  lifecycleState?: string;
};

export function ExecutionTicketPanel({
  tradeId,
  scanId,
  tradeSnapshot,
  lifecycleState,
}: ExecutionTicketPanelProps) {
  const ticketsQuery = useExecutionTicketsByTrade(tradeId);
  const createTicket = useCreateExecutionTicket();
  const patchTicket = usePatchExecutionTicket();

  const ticket = useMemo(() => {
    if (!ticketsQuery.data || ticketsQuery.data.length === 0) {
      return null;
    }
    return ticketsQuery.data[0];
  }, [ticketsQuery.data]);

  const [quantityDraft, setQuantityDraft] = useState(1);
  const [noteDraft, setNoteDraft] = useState("");
  const [noteEditing, setNoteEditing] = useState(false);

  useEffect(() => {
    if (!ticket) {
      setQuantityDraft(1);
      setNoteDraft("");
      setNoteEditing(false);
      return;
    }
    setQuantityDraft(ticket.quantity);
    setNoteDraft(ticket.note ?? "");
    setNoteEditing(false);
  }, [ticket]);

  const quantityChanged = ticket ? quantityDraft !== ticket.quantity : false;
  const noteChanged = ticket ? noteDraft.trim() !== (ticket.note ?? "").trim() : false;

  const isPending = createTicket.isPending || patchTicket.isPending;
  const panelError = createTicket.error?.message ?? patchTicket.error?.message ?? null;

  function submitCreate() {
    if (!tradeId || isPending) {
      return;
    }
    createTicket.mutate({
      ...tradeSnapshot,
      trade_id: tradeId,
      source_scan_id: scanId ?? tradeSnapshot.source_scan_id ?? null,
      quantity: quantityDraft,
      note: noteDraft.trim() || undefined,
    });
  }

  function saveQuantity() {
    if (!ticket || isPending || quantityDraft < 1 || !quantityChanged) {
      return;
    }
    patchTicket.mutate({
      ticketId: ticket.ticket_id,
      payload: { quantity: quantityDraft },
    });
  }

  function saveNote() {
    if (!ticket || isPending || !noteChanged) {
      return;
    }
    const trimmed = noteDraft.trim();
    patchTicket.mutate({
      ticketId: ticket.ticket_id,
      payload: trimmed ? { note: trimmed } : { clear_note: true },
    });
    setNoteEditing(false);
  }

  function setStatusReady() {
    if (!ticket || isPending || ticket.execution_status === "ready") {
      return;
    }
    patchTicket.mutate({
      ticketId: ticket.ticket_id,
      payload: { execution_status: "ready" },
    });
  }

  if (ticketsQuery.isLoading) {
    return <p className="text-sm text-ink-3">Loading execution ticket state…</p>;
  }

  if (ticketsQuery.isError) {
    return <p className="text-sm text-danger">Unable to load execution tickets. Try again.</p>;
  }

  if (!ticket) {
    if (lifecycleState !== "execution_ready") {
      return (
        <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-4">
          <p className="text-sm text-ink-3">Mark trade as Ready first to prepare an execution ticket.</p>
        </div>
      );
    }

    return (
      <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-4 space-y-3">
        <p className="text-sm text-ink-2">Create a structured execution ticket snapshot before any broker submission flow is enabled.</p>
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs text-ink-4" htmlFor="ticket-quantity-create">Qty</label>
          <input
            id="ticket-quantity-create"
            type="number"
            min={1}
            value={quantityDraft}
            onChange={(event) => setQuantityDraft(Math.max(1, Number(event.target.value || 1)))}
            className="w-20 rounded-card border border-white/10 bg-surface-overlay/70 px-2 py-1.5 text-sm text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/30"
          />
        </div>
        <textarea
          value={noteDraft}
          onChange={(event) => setNoteDraft(event.target.value)}
          rows={2}
          className="w-full rounded-card border border-white/10 bg-surface-overlay/70 px-3 py-2 text-sm text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/30"
          placeholder="Optional execution context note..."
          aria-label="Execution ticket note"
        />
        <button
          type="button"
          onClick={submitCreate}
          disabled={isPending || quantityDraft < 1}
          className="rounded-card border border-accent/25 bg-accent px-3 py-2 text-xs font-semibold text-surface-0 disabled:opacity-50 disabled:pointer-events-none"
        >
          {createTicket.isPending ? "Preparing…" : "Prepare execution ticket"}
        </button>
        {panelError ? <p className="text-xs text-danger">{panelError}</p> : null}
      </div>
    );
  }

  const statusTone = ticket.execution_status === "ready" ? "success" : "neutral";

  return (
    <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-4 space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Chip tone={statusTone}>{ticket.execution_status}</Chip>
        <span className="text-xs text-ink-4">
          {ticket.execution_status === "ready"
            ? "Ready for paper execution"
            : "Draft ticket captured for operator review"}
        </span>
      </div>

      <div className="grid gap-2 text-sm text-ink-2 sm:grid-cols-2">
        <p>{ticket.ticker} - {ticket.strategy_label}</p>
        <p>Expiry: {ticket.expiration_date ?? "-"}</p>
        <p>Short: {ticket.short_strike ?? "-"}</p>
        <p>Long: {ticket.long_strike ?? "-"}</p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setQuantityDraft((value) => Math.max(1, value - 1))}
          className="rounded-card border border-white/10 px-2 py-1 text-sm text-ink-2"
          aria-label="Decrease quantity"
        >
          -
        </button>
        <input
          type="number"
          min={1}
          value={quantityDraft}
          onChange={(event) => setQuantityDraft(Math.max(1, Number(event.target.value || 1)))}
          className="w-20 rounded-card border border-white/10 bg-surface-overlay/70 px-2 py-1.5 text-sm text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/30"
          aria-label="Execution quantity"
        />
        <button
          type="button"
          onClick={() => setQuantityDraft((value) => value + 1)}
          className="rounded-card border border-white/10 px-2 py-1 text-sm text-ink-2"
          aria-label="Increase quantity"
        >
          +
        </button>
        <button
          type="button"
          onClick={saveQuantity}
          disabled={!quantityChanged || isPending}
          className="rounded-card border border-white/10 px-3 py-1.5 text-xs font-semibold text-ink-2 disabled:opacity-50 disabled:pointer-events-none"
        >
          Save quantity
        </button>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-4">Ticket note</p>
          {!noteEditing ? (
            <button
              type="button"
              onClick={() => setNoteEditing(true)}
              className="text-xs text-ink-3 hover:text-ink-2"
            >
              {ticket.note ? "Edit" : "Add note"}
            </button>
          ) : null}
        </div>

        {noteEditing ? (
          <div className="space-y-2">
            <textarea
              value={noteDraft}
              onChange={(event) => setNoteDraft(event.target.value)}
              rows={2}
              className="w-full rounded-card border border-white/10 bg-surface-overlay/70 px-3 py-2 text-sm text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/30"
              aria-label="Execution ticket note"
            />
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={saveNote}
                disabled={!noteChanged || isPending}
                className="rounded-card border border-accent/25 bg-accent px-3 py-1.5 text-xs font-semibold text-surface-0 disabled:opacity-50 disabled:pointer-events-none"
              >
                Save note
              </button>
              <button
                type="button"
                onClick={() => {
                  setNoteDraft(ticket.note ?? "");
                  setNoteEditing(false);
                }}
                className="rounded-card border border-white/10 px-3 py-1.5 text-xs font-semibold text-ink-3"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : ticket.note ? (
          <p className="text-sm text-ink-2">{ticket.note}</p>
        ) : (
          <p className="text-sm text-ink-4">No note added.</p>
        )}
      </div>

      {ticket.execution_status === "draft" ? (
        <button
          type="button"
          onClick={setStatusReady}
          disabled={isPending}
          className="rounded-card border border-success/25 bg-success px-3 py-2 text-xs font-semibold text-surface-0 disabled:opacity-50 disabled:pointer-events-none"
        >
          Mark Ready
        </button>
      ) : null}

      {panelError ? <p className="text-xs text-danger">{panelError}</p> : null}
    </div>
  );
}
