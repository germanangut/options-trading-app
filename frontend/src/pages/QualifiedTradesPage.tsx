import { Link } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { SectionFrame } from "../components/ui/SectionFrame";
import { TradeCard } from "../components/ui/TradeCard";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectQualifiedBoardModel } from "../features/scans/selectors/decisionExperienceSelectors";
import { describeApiError } from "../lib/apiErrors";

export function QualifiedTradesPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading qualified trades" message="Waiting for the latest ranked board from the backend." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load qualified trades">
        {describeApiError(latestScan.error, "load", "qualified trades").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No qualified trades yet"
        message="Run a scan first. This page will later evolve into the primary trade review surface."
      />
    );
  }

  const qualifiedTrades = selectQualifiedBoardModel(latestScan.data);
  const leadItem = qualifiedTrades.items[0] ?? null;

  return (
    <PageShell
      eyebrow="Qualified Trades"
      title="Ranked decision board"
      description="Read this page like a shortlist briefing: identity first, risk shape second, portfolio fit third, then open the execution brief."
      actions={
        <ActionRow>
          <Link to="/alerts" className="rounded-card border border-white/10 bg-surface-overlay/70 px-4 py-2.5 text-sm font-semibold text-ink-2">
            Compare alerts
          </Link>
        </ActionRow>
      }
    >
      <SectionFrame eyebrow="Board Readout" title="Current shortlist" subtitle="The board preserves backend ranking and turns each row into a decision story instead of a flat summary.">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
          <div className="grid gap-3">
            {leadItem ? (
              <div className="rounded-card border border-accent/20 bg-accent-soft/24 p-4">
                <p className="eyebrow-label">Lead idea</p>
                <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-lg font-semibold text-ink-1">{leadItem.title}</p>
                    <p className="text-sm leading-6 text-ink-2">{leadItem.quickReview.summary}</p>
                  </div>
                  {leadItem.href ? (
                    <Link to={leadItem.href} className="rounded-card border border-accent/25 bg-accent px-4 py-2.5 text-sm font-semibold text-surface-0 shadow-elevated">
                      Open lead brief
                    </Link>
                  ) : null}
                </div>
              </div>
            ) : null}
            <div className="grid gap-2">
              {qualifiedTrades.narrative.map((line) => (
                <div key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm leading-6 text-ink-2">
                  {line}
                </div>
              ))}
            </div>
          </div>
          <div className="grid gap-3">
            <MetricStrip items={qualifiedTrades.summary} columns={4} />
            <div className="rounded-card border border-accent/20 bg-accent-soft/24 px-4 py-3 text-sm leading-6 text-ink-2">
              Start with the top-ranked card, use the quality ribbon and payoff cue to filter quickly, then open the execution brief only for names that still fit.
            </div>
          </div>
        </div>
      </SectionFrame>

      {qualifiedTrades.caveats.length > 0 ? (
        <div className="grid gap-3">
          {qualifiedTrades.caveats.map((caveat) => (
            <WarningBand key={caveat} title="Scan caveat">
              {caveat}
            </WarningBand>
          ))}
        </div>
      ) : null}

      {qualifiedTrades.items.length === 0 ? (
        <EmptyState title={qualifiedTrades.emptyState.title} message={qualifiedTrades.emptyState.message} tone="warning" />
      ) : (
        <div className="grid gap-4">
          {qualifiedTrades.items.map((item) => (
            <TradeCard
              key={item.id}
              href={item.href}
              rank={item.rank}
              title={item.title}
              subtitle={item.subtitle}
              direction={item.direction}
              directionTone={item.directionTone}
              label={item.label}
              labelTone={item.labelTone}
              freshnessLabel={item.freshnessLabel}
              freshnessTone={item.freshnessTone}
              score={item.score}
              scoreDetail={item.scoreDetail}
              strategyLabel={item.strategyLabel}
              metrics={item.metrics}
              summary={item.quickReview.summary}
              structure={item.quickReview.structure}
              narrative={item.narrative}
              chartLabel={item.chartLabel}
              riskNote={item.riskNote}
              portfolioNote={item.portfolioNote}
              riskProfile={item.riskProfile}
              actionLabel={item.actionLabel}
              footer={
                <ActionRow>
                  <span className="text-sm text-ink-4">Open the execution-prep detail view only after the card still looks right on risk, quality, and concentration.</span>
                </ActionRow>
              }
            />
          ))}
        </div>
      )}
    </PageShell>
  );
}
