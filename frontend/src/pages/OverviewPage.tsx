import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { formatDuration, formatTradeLabel } from "../lib/formatters";

export function OverviewPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading latest scan" message="Waiting for the backend to return the current ScanResult." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load latest scan">
        {latestScan.error instanceof Error ? latestScan.error.message : "The latest scan could not be loaded."}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No scan available yet"
        message="Run the first scan from the sidebar to populate the overview placeholders."
      />
    );
  }

  const { scan_metadata: metadata, summary, diagnostics } = latestScan.data;

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Qualified Trades" value={summary.qualified_count} />
        <MetricCard label="Near Misses" value={summary.near_miss_count} />
        <MetricCard label="Provider" value={metadata.provider ?? "Unknown"} />
        <MetricCard label="Runtime" value={formatDuration(metadata.execution_time_seconds)} />
      </section>

      {diagnostics.missing_tickers.length > 0 ? (
        <Banner tone="warning" title="Partial market coverage">
          Missing tickers: {diagnostics.missing_tickers.join(", ")}
        </Banner>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card title="Top Opportunity" subtitle="Current placeholder view powered by summary.top_overall.">
          {summary.top_overall ? (
            <div className="space-y-3">
              <div>
                <p className="text-lg font-semibold text-ink-1">{formatTradeLabel(summary.top_overall)}</p>
                <p className="text-sm text-ink-2">
                  DTE {summary.top_overall.DTE ?? "-"} - Score {summary.top_overall.adjusted_score ?? summary.top_overall.score ?? "-"}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <MetricCard label="POP" value={summary.top_overall.POP ?? "-"} compact />
                <MetricCard label="ROR" value={summary.top_overall.ROR ?? "-"} compact />
                <MetricCard label="Label" value={summary.top_overall.label ?? "-"} compact />
              </div>
            </div>
          ) : (
            <EmptyState title="No top trade" message="The latest scan did not return a top-ranked opportunity." />
          )}
        </Card>

        <Card title="Scan Context" subtitle="Stable metadata fields from the canonical contract.">
          <dl className="grid gap-3 text-sm text-ink-2">
            <div className="flex items-center justify-between gap-4">
              <dt>Profile</dt>
              <dd className="font-medium text-ink-1">{metadata.profile}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Ticker Group</dt>
              <dd className="font-medium text-ink-1">{metadata.ticker_group}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>DTE Range</dt>
              <dd className="font-medium text-ink-1">
                {metadata.dte_range.dte_min}-{metadata.dte_range.dte_max}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Strategies</dt>
              <dd className="font-medium text-ink-1">
                {metadata.selected_strategy_keys.length > 0
                  ? metadata.selected_strategy_keys.join(", ")
                  : "All active"}
              </dd>
            </div>
          </dl>
        </Card>
      </section>
    </div>
  );
}
