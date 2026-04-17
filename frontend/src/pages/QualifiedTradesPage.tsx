import { Link } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { Banner } from "../components/ui/Banner";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { QuickReviewPanel } from "../components/ui/QuickReviewPanel";
import { SectionFrame } from "../components/ui/SectionFrame";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectQualifiedBoardModel } from "../features/scans/selectors/decisionExperienceSelectors";

export function QualifiedTradesPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading qualified trades" message="Waiting for the latest ranked board from the backend." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load qualified trades">
        {latestScan.error instanceof Error ? latestScan.error.message : "The latest scan could not be loaded."}
      </Banner>
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

  return (
    <div className="grid gap-5">
      <SectionFrame eyebrow="Qualified Trades" title="Ranked review board" subtitle="Preserves backend order and reconstructs fast comparison cues.">
        <MetricStrip items={qualifiedTrades.summary} columns={4} />
      </SectionFrame>

      {qualifiedTrades.caveats.length > 0 ? (
        <div className="grid gap-3">
          {qualifiedTrades.caveats.map((caveat) => (
            <Banner key={caveat} tone="warning" title="Scan caveat">
              {caveat}
            </Banner>
          ))}
        </div>
      ) : null}

      {qualifiedTrades.items.length === 0 ? (
        <EmptyState title="No qualified trades" message="The latest scan did not produce any qualified opportunities." />
      ) : (
        <div className="grid gap-4">
          {qualifiedTrades.items.map((item) => (
            <SectionFrame
              key={item.id}
              eyebrow={`Rank #${item.rank}`}
              title={item.title}
              subtitle={item.subtitle}
              actions={
                <div className="flex flex-wrap gap-2">
                  <Chip tone={item.directionTone}>{item.direction}</Chip>
                  <Chip tone={item.labelTone}>{item.label}</Chip>
                </div>
              }
              className="relative overflow-hidden"
            >
              <div className="absolute inset-y-0 left-0 w-1.5 bg-accent" />
              <div className="space-y-4 pl-2">
                <MetricStrip items={item.metrics} columns={3} compact />
                <QuickReviewPanel title="Quick review" summary={item.quickReview.summary}>
                  <div className="grid gap-2 text-sm text-ink-2">
                    {item.quickReview.structure.map((line) => (
                      <p key={line}>{line}</p>
                    ))}
                  </div>
                </QuickReviewPanel>
                <ActionRow>
                  {item.href ? (
                    <Link to={item.href} className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">
                      Open detail
                    </Link>
                  ) : null}
                  <Link to="/alerts" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-ink-2">
                    Compare with alerts
                  </Link>
                </ActionRow>
              </div>
            </SectionFrame>
          ))}
        </div>
      )}
    </div>
  );
}
