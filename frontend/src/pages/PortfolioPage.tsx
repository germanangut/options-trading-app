import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectPortfolioModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatNumber } from "../lib/formatters";

function asNumber(value: string | number | undefined) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : 0;
}

function summaryValue(summaryCards: Array<{ label: string; value: string | number }>, label: string) {
  return summaryCards.find((card) => card.label === label)?.value;
}

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
  const qualifiedTradesCount = asNumber(summaryValue(portfolio.summaryCards, "Qualified Trades"));
  const fitsBudgetCount = asNumber(summaryValue(portfolio.summaryCards, "Fits Budget"));
  const oversizedCount = asNumber(summaryValue(portfolio.summaryCards, "Oversized"));
  const postureLabel = String(summaryValue(portfolio.summaryCards, "Portfolio Posture") ?? "Portfolio view");

  const mainRisk = portfolio.warnings[0] ?? portfolio.cautions[0] ?? portfolio.exposureNotes[0]
    ?? "No immediate sizing pressure was flagged in the latest scan.";
  const headlineInterpretation = portfolio.interpretation[0]
    ?? `The current book is carrying ${qualifiedTradesCount} qualified trade${qualifiedTradesCount === 1 ? "" : "s"} with ${fitsBudgetCount} currently fitting the risk budget.`;
  const postureSummary = oversizedCount > 0
    ? `${oversizedCount} position${oversizedCount === 1 ? " is" : "s are"} still pressing the portfolio beyond the preferred sizing envelope.`
    : `${fitsBudgetCount} position${fitsBudgetCount === 1 ? " fits" : "s fit"} the current risk budget and the book is not showing oversized exposure pressure.`;
  const nextReview = oversizedCount > 0
    ? `Review the ${oversizedCount} oversized position${oversizedCount === 1 ? "" : "s"} first in the sizing table before adding new risk.`
    : portfolio.topTickerConcentration[0]
      ? `Review concentration in ${portfolio.topTickerConcentration[0].ticker} before treating the book as fully balanced.`
      : portfolio.positions[0]
        ? `Review ${portfolio.positions[0].ticker ?? "the lead setup"} in the sizing table as the next portfolio-fit check.`
        : "Review the sizing rows next to confirm how each idea fits the current risk budget.";

  const primaryEvidenceItems = [
    {
      label: "Oversized",
      value: oversizedCount,
      detail: oversizedCount > 0 ? "Needs review before new exposure is added." : "No oversized positions are currently pressing the book.",
      tone: oversizedCount > 0 ? "warning" as const : "success" as const,
    },
    {
      label: "Fits Budget",
      value: fitsBudgetCount,
      detail: fitsBudgetCount > 0 ? "Positions currently inside the preferred sizing range." : "No positions are clearly inside budget yet.",
      tone: fitsBudgetCount > 0 ? "success" as const : "neutral" as const,
    },
  ];

  const secondaryEvidenceItems = [
    {
      label: "Qualified Trades",
      value: qualifiedTradesCount,
      detail: qualifiedTradesCount > 0 ? "Current candidates carried into the portfolio read." : "No qualified ideas are currently feeding the portfolio view.",
      tone: qualifiedTradesCount > 0 ? "accent" as const : "neutral" as const,
    },
    {
      label: "Portfolio Posture",
      value: postureLabel,
      detail: oversizedCount > 0 ? "Current stance reflects active sizing pressure." : "Current stance is supported by the latest portfolio check.",
      tone: oversizedCount > 0 || portfolio.warnings.length > 0 ? "warning" as const : "accent" as const,
    },
  ];

  const interpretationStory = portfolio.interpretation.slice(1);
  const exposureFocus = portfolio.exposureNotes.slice(0, 3);

  return (
    <PageShell
      eyebrow="Portfolio"
      title="Portfolio verdict"
      description="Read the posture, confirm the pressure points, then move straight into sizing review."
      className="gap-4"
    >
      <Card
        className="border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(57,192,187,0.16),transparent_34%),linear-gradient(180deg,rgba(12,18,30,0.96),rgba(8,13,24,0.92))]"
      >
        <div className="space-y-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] lg:items-start">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-pill border border-white/8 bg-surface-2/65 px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-ink-4">
                  Decision Summary
                </span>
              </div>
              <div className="space-y-2.5">
                <h2 className="text-xl font-semibold tracking-tight text-ink-1 sm:text-2xl">{postureLabel}</h2>
                <p className="max-w-3xl text-sm leading-6 text-ink-2 sm:text-[0.95rem]">{headlineInterpretation}</p>
                <p className="max-w-3xl text-sm leading-6 text-ink-3">{postureSummary}</p>
              </div>
            </div>

            <div className="grid gap-2.5">
              <PortfolioImpactBand title="Key concern" message={mainRisk} tone={oversizedCount > 0 || portfolio.warnings.length > 0 ? "warning" : "accent"} />
              <PortfolioImpactBand title="Review next" message={nextReview} tone="accent" />
            </div>
          </div>

          <div className="space-y-2.5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold tracking-tight text-ink-1">Supporting evidence</p>
              <p className="text-xs uppercase tracking-[0.18em] text-ink-4">Portfolio check</p>
            </div>
            <div className="grid gap-2.5 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
              <MetricStrip items={primaryEvidenceItems} columns={2} />
              <MetricStrip items={secondaryEvidenceItems} columns={2} compact />
            </div>
          </div>
        </div>
      </Card>

      <section className="grid gap-3 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <Card eyebrow="Portfolio read" title="Why the book reads this way" subtitle="Use this read to understand why the current posture feels balanced, stretched, or in need of review.">
          {portfolio.interpretation.length > 0 || portfolio.keySignals.length > 0 || portfolio.cautions.length > 0 ? (
            <div className="space-y-3 text-sm text-ink-2">
              {interpretationStory.length > 0 ? interpretationStory.map((item) => (
                <p key={item} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{item}</p>
              )) : (
                <PortfolioImpactBand title="Bottom line" message={headlineInterpretation} tone="neutral" />
              )}
              {portfolio.keySignals.length > 0 ? (
                <div>
                  <p className="mb-2 text-sm font-semibold text-ink-1">What is supporting the book</p>
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
                  <p className="mb-2 text-sm font-semibold text-ink-1">What needs tighter review</p>
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
            <EmptyState title="No portfolio read yet" message="The latest scan did not return any portfolio commentary to explain the current posture." />
          )}
        </Card>

        <Card eyebrow="Exposure" title="What the portfolio is leaning on" subtitle="Review exposure pressure and concentration before you trust the sizing story." className="h-full">
          <div className="space-y-3">
            {exposureFocus.length > 0 ? (
              <ul className="grid gap-2 text-sm text-ink-2">
                {exposureFocus.map((note) => (
                  <li key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                    {note}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No exposure pressure noted" message="The latest scan did not return any additional exposure notes for the current book." />
            )}

            {portfolio.topTickerConcentration.length > 0 ? (
              <div>
                <p className="mb-2 text-sm font-semibold text-ink-1">Concentration to watch</p>
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
            <PortfolioImpactBand title="How to read this" message="Use this panel as the pressure check behind the verdict: concentration and exposure explain whether the posture can absorb another trade." tone="neutral" />
          </div>
        </Card>
      </section>

      <Card eyebrow="Sizing" title="Sizing to review next" subtitle="Use the rows below to confirm which ideas fit cleanly and which ones need a tighter risk decision.">
        {portfolio.positions.length > 0 ? (
          <div className="space-y-3">
            <PortfolioImpactBand
              title="Sizing focus"
              message={nextReview}
              tone={oversizedCount > 0 ? "warning" : "accent"}
            />
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
                    <tr key={`${position.ticker}-${position.strategy}-${index}`} className="transition-colors hover:bg-white/[0.03]">
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
          </div>
        ) : (
          <EmptyState title="No sizing rows" message="The latest scan did not return any position-sizing rows to review." />
        )}
      </Card>
    </PageShell>
  );
}
