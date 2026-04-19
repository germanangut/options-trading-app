import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricCard } from "../components/ui/MetricCard";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectPortfolioModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatNumber } from "../lib/formatters";

export function PortfolioPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading portfolio" message="Waiting for portfolio summary data from the latest scan." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load portfolio">
        {describeApiError(latestScan.error, "load", "portfolio data").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No portfolio data yet" message="Run a scan first to populate the portfolio summary." />;
  }

  const portfolio = selectPortfolioModel(latestScan.data);
  return (
    <PageShell eyebrow="Portfolio" title="Portfolio interpretation" description="Exposure, sizing, and posture surfaces aligned with the same premium decision language.">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {portfolio.summaryCards.map((card) => (
          <MetricCard key={card.label} label={card.label} value={card.value} tone="neutral" />
        ))}
      </section>

      {portfolio.warnings.length > 0 ? (
        <div className="grid gap-3">
          {portfolio.warnings.map((warning) => (
            <WarningBand key={warning} title="Portfolio warning">
              {warning}
            </WarningBand>
          ))}
        </div>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <Card eyebrow="Interpretation" title="Portfolio Interpretation" subtitle="Current interpretation strings provided by the backend.">
          {portfolio.interpretation.length > 0 ? (
            <div className="space-y-3 text-sm text-ink-2">
              {portfolio.interpretation.map((item) => (
                <p key={item} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{item}</p>
              ))}
              {portfolio.keySignals.length > 0 ? (
                <div>
                  <p className="mb-2 text-sm font-semibold text-ink-1">Key Signals</p>
                  <ul className="grid gap-2">
                    {portfolio.keySignals.map((signal) => (
                      <li key={signal} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                        {signal}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {portfolio.cautions.length > 0 ? (
                <div>
                  <p className="mb-2 text-sm font-semibold text-ink-1">Cautions</p>
                  <ul className="grid gap-2">
                    {portfolio.cautions.map((caution) => (
                      <li key={caution} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                        {caution}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No portfolio interpretation" message="The backend did not return a portfolio interpretation for the latest scan." />
          )}
        </Card>

        <Card eyebrow="Exposure" title="Exposure Snapshot" subtitle="Read-only exposure notes and concentration rows.">
          <div className="space-y-4">
            {portfolio.exposureNotes.length > 0 ? (
              <ul className="grid gap-2 text-sm text-ink-2">
                {portfolio.exposureNotes.map((note) => (
                  <li key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                    {note}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No exposure notes" message="No exposure notes were returned for the latest scan." />
            )}

            {portfolio.topTickerConcentration.length > 0 ? (
              <div>
                <p className="mb-2 text-sm font-semibold text-ink-1">Top Ticker Concentration</p>
                <ul className="grid gap-2 text-sm text-ink-2">
                  {portfolio.topTickerConcentration.map((row) => (
                    <li key={row.ticker} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                      {row.ticker} - {row.count}
                      {row.share_pct !== undefined ? ` (${row.share_pct}%)` : ""}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <PortfolioImpactBand title="How to use this" message="Read exposure here as a portfolio-fit check after the board and detail view, not as a separate scoring model." tone="neutral" />
          </div>
        </Card>
      </section>

      <Card eyebrow="Sizing Rows" title="Positions" subtitle="Current position-sizing rows from the backend portfolio summary.">
        {portfolio.positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead>
                <tr className="text-left text-ink-3">
                  <th className="px-3 py-3 font-medium">Ticker</th>
                  <th className="px-3 py-3 font-medium">Strategy</th>
                  <th className="px-3 py-3 font-medium">Score</th>
                  <th className="px-3 py-3 font-medium">Est. Risk</th>
                  <th className="px-3 py-3 font-medium">Budget Fit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/6">
                {portfolio.positions.map((position, index) => (
                  <tr key={`${position.ticker}-${position.strategy}-${index}`}>
                    <td className="px-3 py-3 text-ink-1">{position.ticker ?? "-"}</td>
                    <td className="px-3 py-3 text-ink-2">{position.strategy ?? "-"}</td>
                    <td className="px-3 py-3 text-ink-2">{formatNumber(position.adjusted_score)}</td>
                    <td className="px-3 py-3 text-ink-2">
                      {formatNumber(position.estimated_max_risk_dollars)}
                    </td>
                    <td className="px-3 py-3 text-ink-2">
                      {position.fits_risk_budget === true
                        ? "Fits"
                        : position.fits_risk_budget === false
                          ? "Above budget"
                          : "Unknown"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No positions" message="No position-sizing rows were returned for the latest scan." />
        )}
      </Card>
    </PageShell>
  );
}
