import { Card } from "../components/ui/Card";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectAlertsModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function AlertsPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading alerts" message="Waiting for the latest alert list from the backend." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load alerts">
        {describeApiError(latestScan.error, "load", "alerts").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No alerts yet" message="Run a scan to populate the alerts placeholder list." />;
  }

  const alerts = selectAlertsModel(latestScan.data);
  const qualifiedCount = Number(latestScan.data.summary?.qualified_count ?? 0);
  const emptyStateFollowUp = alerts.partialNotice
    ? "Use diagnostics in the shell and the ranked board before treating this as a clean no-alert run."
    : qualifiedCount > 0
      ? "Qualified trades were found this run, but none passed the tighter alert filters. Alerts are meant to surface the strongest candidates, not every qualified trade. Want a broader signal set? Adjust score and signal-history filters in Expert mode."
      : "No qualified trades were found this run either. Review Overview and Daily Summary, or widen the scan before adjusting alert filters.";

  return (
    <PageShell
      eyebrow="Alerts"
      title="Alert pressure"
      description="Use alerts as the layer that widens review beyond the ranked board, not as the first place to make the trade decision."
      className="gap-4"
    >
      <Card eyebrow="Live alert feed" title="What is widening the review set" subtitle={`${alerts.total} alert(s) are currently asking for a wider look.`}>
        {alerts.rows.length === 0 ? (
          <div className="space-y-3">
            <EmptyState
              title={alerts.emptyState.title}
              message={alerts.emptyState.message}
              tone={alerts.partialNotice ? "warning" : "neutral"}
            />
            <PortfolioImpactBand title="What to review instead" message={emptyStateFollowUp} tone={alerts.partialNotice ? "warning" : "neutral"} />
          </div>
        ) : (
          <div className="grid gap-3">
            {alerts.rows.map(({ id, trade, score, tag }) => (
              <div
                key={id}
                className="rounded-card border border-white/8 bg-surface-overlay/60 p-4 shadow-elevated"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <h3 className="text-base font-semibold text-ink-1">{formatTradeLabel(trade)}</h3>
                    <p className="text-sm text-ink-3">
                      Score {formatNumber(score)} • POP {formatNumber(trade.POP)} • ROR {formatNumber(trade.ROR)}
                    </p>
                  </div>
                  <Chip tone="neutral">{tag}</Chip>
                </div>
                {trade.decision_summary ? (
                  <div className="mt-3 rounded-card border border-white/8 bg-surface-2/70 px-3 py-3 text-sm text-ink-2">{trade.decision_summary}</div>
                ) : null}
                <p className="mt-3 text-xs leading-5 text-ink-4">Alerts widen the review set. Keep the ranked board as the primary order of operations when both surfaces are active.</p>
              </div>
            ))}
          </div>
        )}
      </Card>
    </PageShell>
  );
}
