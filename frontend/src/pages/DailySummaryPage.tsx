import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectDailySummaryModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatDuration, formatTradeLabel } from "../lib/formatters";

export function DailySummaryPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading daily summary" message="Waiting for the latest daily recap." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load daily summary">
        {describeApiError(latestScan.error, "load", "the daily summary").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No daily summary yet" message="Run a scan first to populate the daily summary." />;
  }

  const dailySummary = selectDailySummaryModel(latestScan.data);
  const recapPrimaryMetrics = [
    { label: "Qualified Trades", value: dailySummary.headline.qualifiedCount, tone: "success" as const },
    { label: "Alerts", value: dailySummary.headline.alertsCount, tone: "accent" as const },
  ];
  const recapSecondaryMetrics = [
    { label: "Near Misses", value: dailySummary.headline.nearMissCount, tone: "warning" as const },
    { label: "Runtime", value: formatDuration(dailySummary.headline.executionTimeSeconds), tone: "neutral" as const },
  ];
  const recapLine = dailySummary.topOpportunity
    ? `${formatTradeLabel(dailySummary.topOpportunity)} is the best candidate to review first from this run.`
    : dailySummary.headline.qualifiedCount > 0
      ? `The run produced ${dailySummary.headline.qualifiedCount} qualified ideas, but none was called out as the single best follow-up.`
      : "The run did not produce a clear lead idea, so use the signal mix and follow-up notes to decide where to review next.";
  const followUpLine = dailySummary.mostStableAlert
    ? `${formatTradeLabel(dailySummary.mostStableAlert)} is the most persistent signal worth checking after the best opportunity.`
    : dailySummary.alertSignals.some((signal) => Number(signal.value) > 0)
      ? "Alert pressure is present, so review the signal mix after the best opportunity." 
      : "No repeated alert pressure is building, so keep the ranked board and overview as the next stop.";
  return (
    <PageShell eyebrow="Daily Summary" title="Daily scan recap" description="Use this page as a compact daily briefing: what happened, what matters, and what deserves follow-up next." className="gap-4">
      <Card eyebrow="Daily recap" title="What happened in this run" subtitle="Start with the recap first, then review the lead idea, signal mix, and follow-up pressure.">
        <div className="space-y-3">
          <div className="grid gap-2.5 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
            <MetricStrip items={recapPrimaryMetrics} columns={2} />
            <MetricStrip items={recapSecondaryMetrics} columns={2} compact />
          </div>
          <div className="grid gap-2.5 md:grid-cols-2">
            <PortfolioImpactBand title="Best read" message={recapLine} tone="accent" />
            <PortfolioImpactBand title="Follow-up" message={followUpLine} tone="neutral" />
          </div>
        </div>
      </Card>

      <section className="grid gap-3 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card eyebrow="Best opportunity" title="What deserves review first" subtitle="Keep the lead setup in view before you widen into alert pressure or follow-up signals.">
          {dailySummary.topOpportunity ? (
            <div className="space-y-3">
              <p className="text-lg font-semibold text-ink-1">{formatTradeLabel(dailySummary.topOpportunity)}</p>
              {dailySummary.topOpportunity.decision_summary ? (
                <div className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm text-ink-2">{dailySummary.topOpportunity.decision_summary}</div>
              ) : (
                <p className="text-sm text-ink-2">No top-opportunity summary text was returned.</p>
              )}
                <p className="text-xs leading-5 text-ink-4">Use the recap as orientation only; move to the cockpit or ranked board for the full decision story.</p>
            </div>
          ) : (
            <EmptyState title="No top opportunity" message="The daily summary did not return a top trade." />
          )}
        </Card>

        <Card eyebrow="Signal mix" title="How the signal mix broke down" subtitle="Read the balance between stable, emerging, and new alert pressure before widening your review.">
          <div className="grid gap-3">
            {dailySummary.alertSignals.map((signal) => (
              <div key={signal.label} className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3">
                <p className="eyebrow-label">{signal.label}</p>
                <p className="mt-1 text-xl font-semibold text-ink-1">{signal.value}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {dailySummary.mostStableAlert ? (
        <Card eyebrow="Follow-up" title="What deserves follow-up" subtitle="Persistent alert pressure is useful when it reinforces the board rather than distracting from it.">
          <p className="text-base font-semibold text-ink-1">{formatTradeLabel(dailySummary.mostStableAlert)}</p>
          <p className="mt-2 rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm text-ink-2">
            Stability level: {dailySummary.mostStableAlert.stability_level ?? "-"}
            {dailySummary.mostStableAlert.stability_count !== undefined
              ? ` (${dailySummary.mostStableAlert.stability_count})`
              : ""}
          </p>
          <p className="mt-3 text-xs leading-5 text-ink-4">Repeated alerts add familiarity, not certainty.</p>
        </Card>
      ) : null}

      {dailySummary.notes.length > 0 ? (
        <Card eyebrow="Follow-up notes" title="What needs a second look" subtitle="Keep these caveats in view before you treat the recap as complete.">
          <div className="grid gap-3">
            {dailySummary.notes.map((note) => (
              <WarningBand key={note} title="Important note">
                {note}
              </WarningBand>
            ))}
          </div>
        </Card>
      ) : null}
    </PageShell>
  );
}
