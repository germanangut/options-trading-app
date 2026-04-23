import { Link } from "react-router-dom";

import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { SectionFrame } from "../components/ui/SectionFrame";
import { WarningBand } from "../components/ui/WarningBand";
import { Chip } from "../components/ui/Chip";
import { usePaperDashboard, useRefreshPaperDashboard } from "../features/scans/hooks/usePaperDashboard";
import { formatCurrency, formatValueLabel } from "../lib/formatters";
import { describeApiError } from "../lib/apiErrors";


function statusTone(status: string | null | undefined): "neutral" | "accent" | "success" | "warning" | "danger" {
  if (!status) {
    return "neutral";
  }

  const normalized = status.toLowerCase();
  if (normalized === "filled" || normalized === "accepted") {
    return "success";
  }
  if (normalized === "submitted" || normalized === "ready" || normalized === "draft") {
    return "accent";
  }
  if (normalized === "rejected") {
    return "danger";
  }
  if (normalized === "canceled") {
    return "warning";
  }
  return "neutral";
}


export function PaperDashboardPage() {
  const dashboardQuery = usePaperDashboard();
  const refreshMutation = useRefreshPaperDashboard();

  if (dashboardQuery.isLoading) {
    return <EmptyState title="Loading paper dashboard" message="Collecting ticket history and paper broker state." />;
  }

  if (dashboardQuery.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load paper dashboard">
        {describeApiError(dashboardQuery.error, "load", "paper dashboard").message}
      </WarningBand>
    );
  }

  if (!dashboardQuery.data) {
    return <EmptyState title="No paper dashboard data" message="Run a paper submission first to populate this workspace." />;
  }

  const dashboard = dashboardQuery.data;

  return (
    <PageShell
      eyebrow="Paper Operations"
      title="Paper positions dashboard"
      description="Review pending orders, open paper positions, and closed outcomes without mixing them with scan analytics."
      actions={
        <button
          type="button"
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="rounded-card border border-accent/25 bg-accent px-3 py-2 text-xs font-semibold text-surface-0 disabled:opacity-50 disabled:pointer-events-none"
        >
          {refreshMutation.isPending ? "Refreshing..." : "Refresh paper status"}
        </button>
      }
    >
      {dashboard.data_source.broker_live_data_warning ? (
        <WarningBand tone="warning" title="Paper broker live data is limited">
          {dashboard.data_source.broker_live_data_warning}
        </WarningBand>
      ) : null}

      <SectionFrame eyebrow="Summary" title="Operational snapshot" subtitle="Counts come from ticket history plus available paper broker enrichment.">
        <MetricStrip
          items={[
            { label: "Pending", value: dashboard.summary.pending_count, tone: "accent" },
            { label: "Open positions", value: dashboard.summary.open_positions_count, tone: "success" },
            { label: "Closed", value: dashboard.summary.closed_count, tone: "neutral" },
            { label: "Recent orders", value: dashboard.summary.recent_orders_count, tone: "neutral" },
          ]}
          columns={4}
          compact
        />
      </SectionFrame>

      <SectionFrame eyebrow="Pending orders" title="Queued or in-flight paper tickets" subtitle="Draft/ready/submitted/accepted tickets that are not yet terminal.">
        {dashboard.pending_orders.length === 0 ? (
          <EmptyState title="No pending paper orders" message="Create and submit an execution ticket to start paper operations." />
        ) : (
          <div className="grid gap-2">
            {dashboard.pending_orders.map((ticket) => (
              <div key={ticket.ticket_id} className="rounded-card border border-white/8 bg-surface-overlay/50 px-3 py-3 text-sm text-ink-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink-1">{ticket.ticker} - {ticket.strategy_label}</p>
                  <Chip tone={statusTone(ticket.execution_status)}>{ticket.execution_status}</Chip>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-ink-3 sm:grid-cols-2">
                  <p>Quantity: {ticket.quantity}</p>
                  <p>Directional bias: {ticket.directional_bias ?? "-"}</p>
                  <p>Broker order id: {ticket.broker_order_id ?? "-"}</p>
                  <p>Submitted at: {ticket.broker_submitted_at ?? "-"}</p>
                  <p>Estimated credit/debit: {formatCurrency(ticket.net_credit_estimate)}</p>
                  <p>Updated at: {ticket.updated_at ?? "-"}</p>
                </div>
                <div className="mt-2">
                  <Link to={ticket.source_scan_id ? `/scans/${ticket.source_scan_id}/trades/${ticket.trade_id}` : "/qualified"} className="text-xs font-semibold text-accent">
                    Open trade detail
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionFrame>

      <SectionFrame eyebrow="Open paper positions" title="Live open exposure" subtitle="Broker-reported open positions, enriched with matching ticket context when available.">
        {dashboard.open_positions.length === 0 ? (
          <EmptyState title="No open paper positions" message="Filled paper orders will appear here when the broker reports an open position." />
        ) : (
          <div className="grid gap-2">
            {dashboard.open_positions.map((position) => (
              <div key={`${position.symbol ?? "unknown"}-${position.linked_ticket_id ?? "none"}`} className="rounded-card border border-white/8 bg-surface-overlay/50 px-3 py-3 text-sm text-ink-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink-1">{position.ticker ?? position.symbol ?? "Position"}</p>
                  <Chip tone="success">open</Chip>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-ink-3 sm:grid-cols-2">
                  <p>Quantity: {position.qty ?? "-"}</p>
                  <p>Side: {position.side ? formatValueLabel(position.side) : "-"}</p>
                  <p>Market value: {formatCurrency(position.market_value)}</p>
                  <p>Cost basis: {formatCurrency(position.cost_basis)}</p>
                  <p>Unrealized P&L: {formatCurrency(position.unrealized_pl)}</p>
                  <p>Unrealized P&L %: {position.unrealized_plpc ?? "-"}</p>
                </div>
                {position.linked_ticket_id ? (
                  <p className="mt-2 text-xs text-ink-4">Linked ticket: {position.linked_ticket_id}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </SectionFrame>

      <SectionFrame eyebrow="Closed paper trades" title="Terminal ticket outcomes" subtitle="Rejected, canceled, or closed-out filled ticket outcomes from app-owned history.">
        {dashboard.closed_trades.length === 0 ? (
          <EmptyState title="No closed paper trades" message="Terminal ticket outcomes will appear here after broker resolution." />
        ) : (
          <div className="grid gap-2">
            {dashboard.closed_trades.map((ticket) => (
              <div key={ticket.ticket_id} className="rounded-card border border-white/8 bg-surface-overlay/50 px-3 py-3 text-sm text-ink-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink-1">{ticket.ticker} - {ticket.strategy_label}</p>
                  <Chip tone={statusTone(ticket.execution_status)}>{ticket.execution_status}</Chip>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-ink-3 sm:grid-cols-2">
                  <p>Broker status: {ticket.broker_status_raw ?? "-"}</p>
                  <p>Broker order id: {ticket.broker_order_id ?? "-"}</p>
                  <p>Submitted at: {ticket.broker_submitted_at ?? "-"}</p>
                  <p>Broker updated: {ticket.broker_updated_at ?? "-"}</p>
                </div>
                {ticket.submission_error_message ? (
                  <p className="mt-2 text-xs text-danger">{ticket.submission_error_message}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </SectionFrame>

      <SectionFrame eyebrow="Recent order history" title="Broker order feed" subtitle="Raw paper broker order history for quick operational traceability.">
        {dashboard.recent_orders.length === 0 ? (
          <EmptyState title="No recent broker orders" message="Recent paper broker orders will appear after submissions are processed." />
        ) : (
          <div className="grid gap-2">
            {dashboard.recent_orders.map((order) => (
              <div key={order.broker_order_id ?? `${order.symbol}-${order.updated_at}`} className="rounded-card border border-white/8 bg-surface-overlay/50 px-3 py-3 text-sm text-ink-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-semibold text-ink-1">{order.symbol ?? "Order"}</p>
                  <Chip tone={statusTone(order.status)}>{order.status ?? "unknown"}</Chip>
                </div>
                <div className="mt-2 grid gap-1 text-xs text-ink-3 sm:grid-cols-2">
                  <p>Order id: {order.broker_order_id ?? "-"}</p>
                  <p>Type: {order.order_type ? formatValueLabel(order.order_type) : "-"}</p>
                  <p>Side: {order.side ? formatValueLabel(order.side) : "-"}</p>
                  <p>Quantity: {order.qty ?? "-"}</p>
                  <p>Filled quantity: {order.filled_qty ?? "-"}</p>
                  <p>Filled avg price: {formatCurrency(order.filled_avg_price)}</p>
                  <p>Submitted at: {order.submitted_at ?? "-"}</p>
                  <p>Updated at: {order.updated_at ?? "-"}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionFrame>
    </PageShell>
  );
}
