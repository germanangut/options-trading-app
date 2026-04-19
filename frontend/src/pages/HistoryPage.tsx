import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { PageShell } from "../components/ui/PageShell";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectHistoryModel, selectScanReliabilityNotice } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";

export function HistoryPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading history" message="Waiting for history context from the latest scan." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load history">
        {describeApiError(latestScan.error, "load", "history").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No history available yet" message="Run a scan first to populate history context." />;
  }

  const history = selectHistoryModel(latestScan.data);
  const reliabilityNotice = selectScanReliabilityNotice(latestScan.data);

  return (
    <PageShell eyebrow="History" title="Historical context" description="Recent pattern and frequency context from the current stored-run summary.">
      {reliabilityNotice ? (
        <WarningBand tone={reliabilityNotice.tone} title={reliabilityNotice.title}>
          {reliabilityNotice.message}
        </WarningBand>
      ) : null}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {history.summaryCards.map((card) => (
          <MetricCard key={card.label} label={card.label} value={card.value} tone="neutral" />
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card eyebrow="Recurring Quality" title="Recent Patterns" subtitle="Recurring names from the backend history summary.">
          {history.recentPatterns.length > 0 ? (
            <div className="grid gap-3">
              {history.recentPatterns.map((pattern) => (
                <div key={pattern.pattern} className="rounded-card border border-white/8 bg-surface-overlay/60 p-4 text-sm text-ink-2">
                  <p className="font-semibold text-ink-1">{pattern.pattern}</p>
                  <p className="mt-1">Count: {pattern.count}</p>
                  <p>Avg Score: {pattern.average_adjusted_score ?? "-"}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No recurring patterns" message="The latest history context did not include recurring trade patterns." />
          )}
        </Card>

        <Card eyebrow="Frequency Leaders" title="Recent Leaders" subtitle="Simple history readout for ticker and strategy frequency.">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold text-ink-1">Top Tickers</p>
              {history.topTickers.length > 0 ? (
                <ul className="grid gap-2 text-sm text-ink-2">
                  {history.topTickers.map((row, index) => (
                    <li key={`${row.ticker}-${index}`} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                      {row.ticker ?? "Unknown"} - {row.count}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No ticker history" message="No ticker frequency data was included." />
              )}
            </div>
            <div>
              <p className="mb-3 text-sm font-semibold text-ink-1">Top Strategies</p>
              {history.topStrategies.length > 0 ? (
                <ul className="grid gap-2 text-sm text-ink-2">
                  {history.topStrategies.map((row, index) => (
                    <li key={`${row.strategy}-${index}`} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                      {row.strategy ?? "Unknown"} - {row.count}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No strategy history" message="No strategy frequency data was included." />
              )}
            </div>
          </div>
          <div className="mt-4 rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm text-ink-2">
            Use these repeat names as context for confidence and familiarity, not as a client-side ranking override.
          </div>
          <p className="mt-3 text-xs leading-5 text-ink-4">History should support pattern recognition without overpowering the current-run evidence.</p>
        </Card>
      </section>
    </PageShell>
  );
}
