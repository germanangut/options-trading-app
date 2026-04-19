import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { PageShell } from "../components/ui/PageShell";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectDailySummaryModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatDuration, formatTradeLabel } from "../lib/formatters";

export function DailySummaryPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading daily summary" message="Waiting for the latest daily summary payload." />;
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
  return (
    <PageShell eyebrow="Daily Summary" title="Daily scan recap" description="A compact briefing layer over the latest run for quick daily orientation.">
      <Card eyebrow="Headline Metrics" title="Daily Summary" subtitle="Headline recap of the latest scan.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Qualified Trades" value={dailySummary.headline.qualifiedCount} tone="success" />
          <MetricCard label="Near Misses" value={dailySummary.headline.nearMissCount} tone="warning" />
          <MetricCard label="Alerts" value={dailySummary.headline.alertsCount} tone="accent" />
          <MetricCard label="Runtime" value={formatDuration(dailySummary.headline.executionTimeSeconds)} tone="neutral" />
        </div>
      </Card>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card eyebrow="Best Opportunity" title="Top Opportunity" subtitle="Current best candidate from the latest summary payload.">
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

        <Card eyebrow="Signal Mix" title="Alert Signals" subtitle="Backend-provided alert counts from the daily summary.">
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
        <Card eyebrow="Stability Leader" title="Most Stable Alert" subtitle="Most stable alert item currently surfaced in the summary payload.">
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
        <div className="grid gap-3">
          {dailySummary.notes.map((note) => (
            <WarningBand key={note} title="Important note">
              {note}
            </WarningBand>
          ))}
        </div>
      ) : null}
    </PageShell>
  );
}
