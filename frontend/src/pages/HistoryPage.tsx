import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
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
      <Banner tone="danger" title="Unable to load history">
        {describeApiError(latestScan.error, "load", "history").message}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No history available yet" message="Run a scan first to populate history context." />;
  }

  const history = selectHistoryModel(latestScan.data);
  const reliabilityNotice = selectScanReliabilityNotice(latestScan.data);

  return (
    <div className="grid gap-6">
      {reliabilityNotice ? (
        <Banner tone={reliabilityNotice.tone} title={reliabilityNotice.title}>
          {reliabilityNotice.message}
        </Banner>
      ) : null}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {history.summaryCards.map((card) => (
          <MetricCard key={card.label} label={card.label} value={card.value} />
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card title="Recent Patterns" subtitle="Recurring names from the backend history summary.">
          {history.recentPatterns.length > 0 ? (
            <div className="grid gap-3">
              {history.recentPatterns.map((pattern) => (
                <div key={pattern.pattern} className="rounded-xl border border-slate-200 bg-surface-0 p-4 text-sm text-ink-2">
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

        <Card title="Recent Leaders" subtitle="Simple history readout for ticker and strategy frequency.">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold text-ink-1">Top Tickers</p>
              {history.topTickers.length > 0 ? (
                <ul className="grid gap-2 text-sm text-ink-2">
                  {history.topTickers.map((row, index) => (
                    <li key={`${row.ticker}-${index}`} className="rounded-xl bg-surface-2 px-3 py-2">
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
                    <li key={`${row.strategy}-${index}`} className="rounded-xl bg-surface-2 px-3 py-2">
                      {row.strategy ?? "Unknown"} - {row.count}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No strategy history" message="No strategy frequency data was included." />
              )}
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
