import { useState } from "react";
import { Link } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { EmptyState } from "../components/ui/EmptyState";
import { LifecycleActions } from "../components/ui/LifecycleActions";
import { LifecycleBadge } from "../components/ui/LifecycleBadge";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { SectionFrame } from "../components/ui/SectionFrame";
import { TradeCard } from "../components/ui/TradeCard";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { useLifecycleRecords, useUpsertTradeLifecycle } from "../features/scans/hooks/useTradeLifecycle";
import { selectQualifiedBoardModel } from "../features/scans/selectors/decisionExperienceSelectors";
import { describeApiError } from "../lib/apiErrors";

const LIFECYCLE_FILTERS = [
  { key: "all", label: "All" },
  { key: "new", label: "New" },
  { key: "saved", label: "Saved" },
  { key: "watching", label: "Watching" },
  { key: "execution_ready", label: "Ready" },
  { key: "dismissed", label: "Dismissed" },
] as const;

type LifecycleFilter = (typeof LIFECYCLE_FILTERS)[number]["key"];

export function QualifiedTradesPage() {
  const latestScan = useLatestScan();
  const lifecycleRecords = useLifecycleRecords();
  const upsertLifecycle = useUpsertTradeLifecycle();
  const [lifecycleFilter, setLifecycleFilter] = useState<LifecycleFilter>("all");

  if (latestScan.isLoading) {
    return <EmptyState title="Loading qualified trades" message="Waiting for the latest ranked board to open." />;
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
        message="Run a scan first to populate the ranked trade board."
      />
    );
  }

  const qualifiedTrades = selectQualifiedBoardModel(latestScan.data);
  const lifecycleByTradeId = new Map(
    (lifecycleRecords.data ?? []).map((record) => [record.trade_id, record]),
  );

  const lifecycleError = upsertLifecycle.isError
    ? (upsertLifecycle.error?.message ?? "Lifecycle update failed. Try again.")
    : null;

  function setLifecycleState(
    tradeId: string | undefined,
    lifecycleState: "saved" | "watching" | "execution_ready" | "dismissed",
  ) {
    if (!tradeId) return;
    upsertLifecycle.mutate({
      tradeId,
      payload: {
        lifecycle_state: lifecycleState,
        source_scan_id: latestScan.data?.scan_metadata?.scan_id ?? null,
      },
    });
  }

  const filteredItems =
    lifecycleFilter === "all"
      ? qualifiedTrades.items
      : qualifiedTrades.items.filter((item) => {
          const state = lifecycleByTradeId.get(item.id)?.lifecycle_state ?? "new";
          return state === lifecycleFilter;
        });

  const leadItem = filteredItems[0] ?? null;
  const primarySummary = qualifiedTrades.summary.filter(
    (item) => item.label === "Qualified" || item.label === "Portfolio Posture",
  );
  const secondarySummary = qualifiedTrades.summary.filter(
    (item) => item.label !== "Qualified" && item.label !== "Portfolio Posture",
  );

  return (
    <PageShell
      eyebrow="Qualified Trades"
      title="Ranked decision board"
      description="Read this page like a shortlist briefing: identity first, evidence second, then open the execution brief only for names that still fit."
      className="gap-4"
      actions={
        <ActionRow>
          <Link to="/alerts" className="rounded-card border border-white/10 bg-surface-overlay/70 px-4 py-2.5 text-sm font-semibold text-ink-2">
            Compare alerts
          </Link>
        </ActionRow>
      }
    >
      <SectionFrame eyebrow="Shortlist" title="What the board is prioritizing" subtitle="Start with identity and pressure first, then open the execution brief for the names that still earn attention.">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
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
            <MetricStrip items={primarySummary} columns={2} />
            <MetricStrip items={secondarySummary} columns={2} compact />
            <div className="rounded-card border border-accent/20 bg-accent-soft/24 px-4 py-3 text-sm leading-6 text-ink-2">
              Start with the lead card, use the quality ribbon and payoff cue to filter quickly, then open the execution brief only for names that still fit.
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

      {lifecycleError ? (
        <WarningBand tone="danger" title="Lifecycle update failed">
          {lifecycleError}
        </WarningBand>
      ) : null}

      {qualifiedTrades.items.length === 0 ? (
        <EmptyState title={qualifiedTrades.emptyState.title} message={qualifiedTrades.emptyState.message} tone="warning" />
      ) : (
        <div className="grid gap-4">
          {/* Lifecycle filter tabs */}
          <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Filter by lifecycle state">
            {LIFECYCLE_FILTERS.map((filter) => {
              const isActive = lifecycleFilter === filter.key;
              const count =
                filter.key === "all"
                  ? qualifiedTrades.items.length
                  : qualifiedTrades.items.filter(
                      (item) =>
                        (lifecycleByTradeId.get(item.id)?.lifecycle_state ?? "new") === filter.key,
                    ).length;

              return (
                <button
                  key={filter.key}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setLifecycleFilter(filter.key)}
                  className={[
                    "rounded-card px-3 py-1.5 text-xs font-semibold transition-colors",
                    isActive
                      ? "border border-accent/25 bg-accent-soft/50 text-accent"
                      : "border border-white/8 bg-surface-overlay/50 text-ink-3 hover:text-ink-2",
                  ].join(" ")}
                >
                  {filter.label}
                  {count > 0 ? (
                    <span className="ml-1.5 tabular-nums opacity-70">{count}</span>
                  ) : null}
                </button>
              );
            })}
          </div>

          {filteredItems.length === 0 ? (
            <EmptyState
              title={`No ${lifecycleFilter === "execution_ready" ? "ready" : lifecycleFilter} trades`}
              message="No trades in this board match the selected lifecycle state."
            />
          ) : (
            filteredItems.map((item) => {
              const currentState = lifecycleByTradeId.get(item.id)?.lifecycle_state ?? "new";

              return (
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
                    <div className="space-y-2 pt-1">
                      <div className="flex items-center gap-2">
                        <LifecycleBadge state={currentState} size="sm" />
                        {upsertLifecycle.isPending ? (
                          <span className="text-[0.65rem] text-ink-4">Saving…</span>
                        ) : null}
                      </div>
                      <LifecycleActions
                        currentState={currentState}
                        onTransition={(state) => setLifecycleState(item.id, state)}
                        isPending={upsertLifecycle.isPending}
                        size="sm"
                      />
                    </div>
                  }
                />
              );
            })
          )}
        </div>
      )}
    </PageShell>
  );
}
