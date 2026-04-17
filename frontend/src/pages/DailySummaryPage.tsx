import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectDailySummaryModel, selectScanReliabilityNotice } from "../features/scans/selectors/scanSelectors";
import { formatDuration, formatTradeLabel } from "../lib/formatters";

export function DailySummaryPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading daily summary" message="Waiting for the latest daily summary payload." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load daily summary">
        {latestScan.error instanceof Error ? latestScan.error.message : "The latest scan could not be loaded."}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No daily summary yet" message="Run a scan first to populate the daily summary." />;
  }

  const dailySummary = selectDailySummaryModel(latestScan.data);
  const reliabilityNotice = selectScanReliabilityNotice(latestScan.data);

  return (
    <div className="grid gap-6">
      {reliabilityNotice ? (
        <Banner tone={reliabilityNotice.tone} title={reliabilityNotice.title}>
          {reliabilityNotice.message}
        </Banner>
      ) : null}
      <Card title="Daily Summary" subtitle="Headline recap of the latest scan.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Qualified Trades" value={dailySummary.headline.qualifiedCount} />
          <MetricCard label="Near Misses" value={dailySummary.headline.nearMissCount} />
          <MetricCard label="Alerts" value={dailySummary.headline.alertsCount} />
          <MetricCard label="Runtime" value={formatDuration(dailySummary.headline.executionTimeSeconds)} />
        </div>
      </Card>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <Card title="Top Opportunity" subtitle="Current best candidate from the latest summary payload.">
          {dailySummary.topOpportunity ? (
            <div className="space-y-3">
              <p className="text-lg font-semibold text-ink-1">{formatTradeLabel(dailySummary.topOpportunity)}</p>
              {dailySummary.topOpportunity.decision_summary ? (
                <p className="text-sm text-ink-2">{dailySummary.topOpportunity.decision_summary}</p>
              ) : (
                <p className="text-sm text-ink-2">No top-opportunity summary text was returned.</p>
              )}
            </div>
          ) : (
            <EmptyState title="No top opportunity" message="The daily summary did not return a top trade." />
          )}
        </Card>

        <Card title="Alert Signals" subtitle="Backend-provided alert counts from the daily summary.">
          <div className="grid gap-3">
            {dailySummary.alertSignals.map((signal) => (
              <div key={signal.label} className="rounded-xl bg-surface-2 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">{signal.label}</p>
                <p className="mt-1 text-xl font-semibold text-ink-1">{signal.value}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {dailySummary.mostStableAlert ? (
        <Card title="Most Stable Alert" subtitle="Most stable alert item currently surfaced in the summary payload.">
          <p className="text-base font-semibold text-ink-1">{formatTradeLabel(dailySummary.mostStableAlert)}</p>
          <p className="mt-2 text-sm text-ink-2">
            Stability level: {dailySummary.mostStableAlert.stability_level ?? "-"}
            {dailySummary.mostStableAlert.stability_count !== undefined
              ? ` (${dailySummary.mostStableAlert.stability_count})`
              : ""}
          </p>
        </Card>
      ) : null}

      {dailySummary.notes.length > 0 ? (
        <div className="grid gap-3">
          {dailySummary.notes.map((note) => (
            <Banner key={note} tone="warning" title="Important note">
              {note}
            </Banner>
          ))}
        </div>
      ) : null}
    </div>
  );
}
