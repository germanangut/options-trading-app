import { Link, useParams } from "react-router-dom";

import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectTradeDetailModel } from "../features/scans/selectors/scanSelectors";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function QualifiedTradeDetailPage() {
  const { tradeId } = useParams();
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading trade detail" message="Waiting for the latest scan payload." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load trade detail">
        {latestScan.error instanceof Error ? latestScan.error.message : "The latest scan could not be loaded."}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No scan available"
        message="Run a scan before opening a trade detail route."
      />
    );
  }

  const model = selectTradeDetailModel(latestScan.data, tradeId);

  if (model.routeType !== "resolved" || !model.trade) {
    return (
      <Card title={model.title} subtitle="Temporary route resolution based on the latest scan only.">
        <div className="space-y-4 text-sm text-ink-2">
          {model.notes.map((note) => (
            <p key={note}>{note}</p>
          ))}
          <Link to="/qualified" className="inline-flex rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">
            Back to Qualified Trades
          </Link>
        </div>
      </Card>
    );
  }

  const trade = model.trade;

  return (
    <Card
      title={model.title}
      subtitle="Temporary route strategy. This is not yet backed by a stable backend trade identifier."
    >
      <div className="grid gap-6">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Trade" value={formatTradeLabel(trade)} />
          <MetricCard label="Score" value={formatNumber(trade.adjusted_score ?? trade.score)} />
          <MetricCard label="POP" value={formatNumber(trade.POP)} />
          <MetricCard label="ROR" value={formatNumber(trade.ROR)} />
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <Card title="Trade Summary" subtitle="Backend-provided explanation and status fields.">
            <div className="space-y-3 text-sm text-ink-2">
              {trade.decision_summary ? <p>{trade.decision_summary}</p> : null}
              {trade.status_reason ? <p>Status: {trade.status_reason}</p> : null}
              {trade.explanation ? <p>{trade.explanation}</p> : null}
              {!trade.decision_summary && !trade.status_reason && !trade.explanation ? (
                <EmptyState title="No explanation available" message="The latest scan did not return a summary or explanation for this trade." />
              ) : null}
            </div>
          </Card>

          <Card title="Structure" subtitle="Key structural fields from the latest scan payload.">
            <dl className="grid gap-3 text-sm text-ink-2">
              <div className="flex items-center justify-between gap-4">
                <dt>Expiration</dt>
                <dd className="font-medium text-ink-1">{trade.expiration_date ?? "-"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>DTE</dt>
                <dd className="font-medium text-ink-1">{trade.DTE ?? "-"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Strikes</dt>
                <dd className="font-medium text-ink-1">
                  {trade.short_strike ?? "-"} / {trade.long_strike ?? "-"}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Premium</dt>
                <dd className="font-medium text-ink-1">{formatNumber(trade.net_credit)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Width</dt>
                <dd className="font-medium text-ink-1">{formatNumber(trade.spread_width)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Max Risk</dt>
                <dd className="font-medium text-ink-1">{formatNumber(trade.max_risk)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Volatility</dt>
                <dd className="font-medium text-ink-1">{trade.volatility_context ?? "-"}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt>Stability</dt>
                <dd className="font-medium text-ink-1">
                  {trade.stability_level ?? "-"}
                  {trade.stability_count !== undefined ? ` (${trade.stability_count})` : ""}
                </dd>
              </div>
            </dl>
          </Card>
        </section>

        <Banner tone="info" title="Temporary route identifier">
          This page resolves from the latest scan payload using a derived route key. It should be replaced later with a backend-provided `trade_id`.
        </Banner>

        <div>
          <Link to="/qualified" className="inline-flex rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">
            Back to Qualified Trades
          </Link>
        </div>
      </div>
    </Card>
  );
}
