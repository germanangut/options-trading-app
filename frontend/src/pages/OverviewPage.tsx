import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectOverviewModel } from "../features/scans/selectors/scanSelectors";
import { formatDuration, formatTradeLabel, formatNumber } from "../lib/formatters";

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

  const overview = selectOverviewModel(latestScan.data);

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label={overview.kpis[0].label} value={overview.kpis[0].value ?? "-"} />
        <MetricCard label={overview.kpis[1].label} value={overview.kpis[1].value ?? "-"} />
        <MetricCard label="Provider" value={overview.metadata.provider ?? "Unknown"} />
        <MetricCard label="Runtime" value={formatDuration(overview.kpis[3].value as number | null)} />
      </section>

      {overview.coverage.missingTickers.length > 0 ? (
        <Banner tone="warning" title="Partial market coverage">
          Missing tickers: {overview.coverage.missingTickers.join(", ")}
        </Banner>
      ) : null}

      {overview.coverage.providerErrors.length > 0 ? (
        <Banner tone="warning" title="Provider issues reported">
          The latest scan contains provider errors, so scan coverage may be incomplete.
        </Banner>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <Card title="Top Opportunity" subtitle="Preview of the highest-ranked trade from the latest scan.">
          {overview.topOpportunity ? (
            <div className="space-y-3">
              <div>
                <p className="text-lg font-semibold text-ink-1">{formatTradeLabel(overview.topOpportunity)}</p>
                <p className="text-sm text-ink-2">
                  DTE {overview.topOpportunity.DTE ?? "-"} - Score {formatNumber(overview.topOpportunity.adjusted_score ?? overview.topOpportunity.score)}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <MetricCard label="POP" value={formatNumber(overview.topOpportunity.POP)} compact />
                <MetricCard label="ROR" value={formatNumber(overview.topOpportunity.ROR)} compact />
                <MetricCard label="Label" value={overview.topOpportunity.label ?? "-"} compact />
              </div>
              {overview.topOpportunity.decision_summary ? (
                <p className="text-sm text-ink-2">{overview.topOpportunity.decision_summary}</p>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No top trade" message="The latest scan did not return a top-ranked opportunity." />
          )}
        </Card>

        <Card title="Scan Context" subtitle="Stable metadata fields from the canonical contract.">
          <dl className="grid gap-3 text-sm text-ink-2">
            <div className="flex items-center justify-between gap-4">
              <dt>Profile</dt>
              <dd className="font-medium text-ink-1">{overview.metadata.profile}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Ticker Group</dt>
              <dd className="font-medium text-ink-1">{overview.metadata.tickerGroup}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>DTE Range</dt>
              <dd className="font-medium text-ink-1">
                {overview.metadata.dteRange.dte_min}-{overview.metadata.dteRange.dte_max}
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt>Strategies</dt>
              <dd className="font-medium text-ink-1">
                {overview.metadata.selectedStrategyKeys.length > 0
                  ? overview.metadata.selectedStrategyKeys.join(", ")
                  : "All active"}
              </dd>
            </div>
          </dl>
        </Card>
      </section>
    </div>
  );
}
