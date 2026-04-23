import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { ChartPanel } from "../components/ui/ChartPanel";
import { EmptyState } from "../components/ui/EmptyState";
import { ExecutionTicketPanel } from "../components/ui/ExecutionTicketPanel";
import { LifecycleActions } from "../components/ui/LifecycleActions";
import { LifecycleBadge } from "../components/ui/LifecycleBadge";
import { MetricStrip } from "../components/ui/MetricStrip";
import { MiniPayoffCue } from "../components/ui/MiniPayoffCue";
import { PayoffCurve } from "../components/ui/PayoffCurve";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { ScoreRibbon } from "../components/ui/ScoreRibbon";
import { SectionFrame } from "../components/ui/SectionFrame";
import { Chip } from "../components/ui/Chip";
import { WarningBand } from "../components/ui/WarningBand";
import { VisualStrategyLab } from "../components/ui/VisualStrategyLab";
import { WhatIfWorkbench } from "../components/ui/WhatIfWorkbench";
import { useScanById } from "../features/scans/hooks/useScanById";
import { useTradeDetail } from "../features/scans/hooks/useTradeDetail";
import { useTradePayoff } from "../features/scans/hooks/useTradePayoff";
import { useTradeVariants } from "../features/scans/hooks/useTradeVariants";
import { useWorkbenchScenario } from "../features/scans/hooks/useWorkbenchScenario";
import { useTradeLifecycle, useUpsertTradeLifecycle } from "../features/scans/hooks/useTradeLifecycle";
import { selectTradeDetailExperienceModel } from "../features/scans/selectors/decisionExperienceSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatCurrency } from "../lib/formatters";
import type { CreateTicketPayload, WorkbenchStrikeShift, WorkbenchWidthAdjustment } from "../types/api";
import { VariantComparisonPanel } from "../components/ui/VariantComparisonPanel";

export function QualifiedTradeDetailPage() {
  const { scanId, tradeId } = useParams();
  const scanQuery = useScanById(scanId);
  const detailQuery = useTradeDetail(scanId, tradeId);
  const payoffQuery = useTradePayoff(scanId, tradeId);
  const lifecycleQuery = useTradeLifecycle(tradeId);
  const variantsQuery = useTradeVariants(scanId, tradeId);
  const upsertLifecycle = useUpsertTradeLifecycle();
  const savedNote = lifecycleQuery.data?.note ?? null;
  const [noteEditing, setNoteEditing] = useState(false);
  const [noteDraft, setNoteDraft] = useState("");
  const [noteJustSaved, setNoteJustSaved] = useState(false);
  const [workbenchStrikeShift, setWorkbenchStrikeShift] = useState<WorkbenchStrikeShift>("baseline");
  const [workbenchWidthAdjustment, setWorkbenchWidthAdjustment] = useState<WorkbenchWidthAdjustment>("baseline");
  const workbenchQuery = useWorkbenchScenario(scanId, tradeId, workbenchStrikeShift, workbenchWidthAdjustment);

  useEffect(() => {
    setNoteDraft(savedNote ?? "");
    setNoteEditing(false);
  }, [savedNote]);

  if (scanQuery.isLoading || detailQuery.isLoading) {
    return <EmptyState title="Loading trade detail" message="Waiting for the trade brief and scan context." />;
  }

  if (scanQuery.isError || detailQuery.isError) {
    const error = scanQuery.error ?? detailQuery.error;

    return (
      <WarningBand tone="danger" title="Unable to load trade detail">
        {describeApiError(error, "load", "trade detail").message}
      </WarningBand>
    );
  }

  if (!scanId || !tradeId) {
    return (
      <EmptyState title="Incomplete route" message="Trade detail requires both a scan id and a trade id." />
    );
  }

  if (!scanQuery.data || !detailQuery.data) {
    return (
      <EmptyState title="Trade not found" message="This route is valid, but the current scan did not return a matching trade." />
    );
  }

  const model = selectTradeDetailExperienceModel(scanQuery.data, detailQuery.data);
  const lifecycleState = lifecycleQuery.data?.lifecycle_state ?? "new";
  const tradeSnapshot: CreateTicketPayload = {
    trade_id: tradeId,
    source_scan_id: scanId ?? null,
    ticker: detailQuery.data.trade.ticker,
    strategy_key: detailQuery.data.trade.strategy_type,
    strategy_label: detailQuery.data.trade.strategy_label ?? detailQuery.data.trade.strategy_type,
    directional_bias: detailQuery.data.trade.directional_bias ?? null,
    expiration_date: detailQuery.data.trade.expiration_date ?? null,
    short_strike: detailQuery.data.trade.short_strike ?? null,
    long_strike: detailQuery.data.trade.long_strike ?? null,
    underlying_price_at_creation: detailQuery.data.trade.underlying_price ?? null,
    net_credit_estimate: detailQuery.data.trade.net_credit ?? null,
    max_risk_estimate: detailQuery.data.trade.max_risk ?? null,
    adjusted_score_at_creation: detailQuery.data.trade.adjusted_score ?? null,
  };
  const supportNotes = model.whyThisTrade.slice(0, 4);
  const contextNotes = [...model.stability.notes, ...model.historyStory, ...model.portfolioImpact.notes.slice(1)].slice(0, 4);
  const payoff = payoffQuery.data?.payoff ?? null;
  const payoffSummaryItems = payoff
    ? [
      {
        label: "Max Profit",
        value: formatCurrency(payoff.max_profit),
        tone: "success" as const,
      },
      {
        label: "Max Loss",
        value: formatCurrency(payoff.max_loss),
        tone: "danger" as const,
      },
      {
        label: "Breakeven",
        value:
          payoff.breakeven_low !== null
            ? `$${payoff.breakeven_low.toFixed(2)}`
            : payoff.breakeven_high !== null
              ? `$${payoff.breakeven_high.toFixed(2)}`
              : "-",
        tone: "accent" as const,
      },
    ]
    : [];

  const lifecycleErrorMessage = upsertLifecycle.isError
    ? (upsertLifecycle.error?.message ?? "Lifecycle update failed. Try again.")
    : null;

  const noteDraftChanged = noteDraft.trim() !== (savedNote ?? "").trim();

  function setLifecycleState(nextState: "saved" | "watching" | "execution_ready" | "dismissed") {
    if (!tradeId) return;
    upsertLifecycle.mutate({
      tradeId,
      payload: {
        lifecycle_state: nextState,
        source_scan_id: scanId ?? null,
      },
    });
  }

  function saveLifecycleNote() {
    if (!tradeId) return;
    upsertLifecycle.mutate(
      { tradeId, payload: { note: noteDraft.trim() || null, source_scan_id: scanId ?? null } },
      {
        onSuccess: () => {
          setNoteEditing(false);
          setNoteJustSaved(true);
          setTimeout(() => setNoteJustSaved(false), 2500);
        },
      },
    );
  }

  return (
    <PageShell
      eyebrow="Trade Detail"
      title={model.header.title}
      description={model.header.subtitle}
      className="gap-4"
      actions={
        <ActionRow>
          <Chip tone={model.header.directionTone}>{model.header.direction}</Chip>
          <Chip tone={model.header.statusTone}>{model.header.statusLabel}</Chip>
        </ActionRow>
      }
    >
      <SectionFrame eyebrow="Execution briefing" title="One-glance trade brief" subtitle="Understand the setup immediately, then move deeper without losing the execution story.">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <div className="space-y-4">
            <ChartPanel title="Why this trade surfaced" subtitle="Use this brief to decide whether the setup still deserves a full execution review." className="bg-surface-1/92">
              <div className="space-y-4">
                <p className="text-sm leading-6 text-ink-1 sm:text-[0.95rem]">{model.quickVerdict}</p>
                <div className="grid gap-2">
                  {model.briefingPoints.map((point) => (
                    <div key={point} className="rounded-card border border-white/8 bg-surface-2/70 px-3 py-2 text-sm text-ink-2">
                      {point}
                    </div>
                  ))}
                </div>
                <ActionRow>
                  {model.actions.slice(0, 2).map((action, index) => (
                    <Link
                      key={action.to}
                      to={action.to}
                      className={[
                        "rounded-card px-4 py-2.5 text-sm font-semibold",
                        index === 0 ? "border border-accent/25 bg-accent text-surface-0" : "border border-white/10 bg-surface-overlay/70 text-ink-2",
                      ].join(" ")}
                    >
                      {action.label}
                    </Link>
                  ))}
                </ActionRow>
              </div>
            </ChartPanel>
            <ChartPanel title="Payoff cue" subtitle="Use this visual anchor to place the credit against the defined downside before reviewing leg-level detail.">
              <MiniPayoffCue
                reward={detailQuery.data.trade.net_credit}
                risk={detailQuery.data.trade.max_risk}
                rewardLabel="Net credit"
                riskLabel="Max risk"
                subtitle="Use the credit against the defined downside to decide whether the structure still earns deeper review."
              />
            </ChartPanel>
            <ChartPanel title="Expiration payoff" subtitle="Model-only view of payoff at expiration based on strategy structure and current ticket assumptions.">
              {payoffQuery.isLoading ? (
                <p className="text-xs text-ink-4">Loading payoff model...</p>
              ) : payoff ? (
                <div className="space-y-4">
                  <MetricStrip items={payoffSummaryItems} columns={3} />
                  <PayoffCurve points={payoff.payoff_points} />
                  <p className="text-xs leading-5 text-ink-4">{payoff.expiration_summary}</p>
                  <div className="grid gap-2 text-xs text-ink-4 sm:grid-cols-2">
                    <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2">
                      <p className="eyebrow-label">Profit zone</p>
                      <p className="mt-1 text-ink-2">{payoff.profit_zone}</p>
                    </div>
                    <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2">
                      <p className="eyebrow-label">Loss zone</p>
                      <p className="mt-1 text-ink-2">{payoff.loss_zone}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-ink-4">Payoff model is unavailable for this trade.</p>
              )}
            </ChartPanel>
          </div>

          <div className="space-y-4">
            <ScoreRibbon score={model.riskReward.find((item) => item.label === "Score")?.value ?? "-"} detail="Read this first, then confirm structure, payout, and concentration." label="Decision Quality" />
            <ChartPanel title="Primary decision numbers" subtitle="Read the score and risk block first, then confirm structure and concentration.">
              <div className="space-y-4">
                <MetricStrip items={model.riskReward} columns={3} />
                <div className="grid gap-2 text-sm text-ink-2">
                  {model.riskStory.map((line) => (
                    <div key={line} className="rounded-card border border-white/8 bg-surface-2/70 px-3 py-2">
                      {line}
                    </div>
                  ))}
                </div>
              </div>
            </ChartPanel>
            {model.portfolioImpact.notes[0] ? (
              <PortfolioImpactBand title="Portfolio context" message={model.portfolioImpact.notes[0]} tone="warning" />
            ) : null}
            <WarningBand tone={model.diagnostics.tone} title={model.diagnostics.title}>
              {model.diagnostics.message}
            </WarningBand>
          </div>
        </div>
      </SectionFrame>

      <SectionFrame
        eyebrow="Strategy variants"
        title="Variant comparison"
        subtitle="Compare this scanned setup against conservative and max-credit alternatives. Analytical only — not execution-ready."
      >
        <VariantComparisonPanel
          variantSet={variantsQuery.data}
          isLoading={variantsQuery.isLoading}
        />
      </SectionFrame>

      <SectionFrame
        eyebrow="Visual strategy lab"
        title="Payoff shape and trade-off lab"
        subtitle="Compare baseline vs one variant at a time to keep payoff visuals clear and decision-focused."
      >
        <VisualStrategyLab variantSet={variantsQuery.data} isLoading={variantsQuery.isLoading} />
      </SectionFrame>

      <SectionFrame
        eyebrow="What-if workbench"
        title="Scenario explorer"
        subtitle="Adjust the short strike or spread width to see how credit, max loss, and payoff change. Analytical only — not execution-ready."
      >
        <WhatIfWorkbench
          scanId={scanId}
          tradeId={tradeId}
          result={workbenchQuery.data}
          isLoading={workbenchQuery.isLoading}
          strikeShift={workbenchStrikeShift}
          widthAdjustment={workbenchWidthAdjustment}
          onStrikeShiftChange={setWorkbenchStrikeShift}
          onWidthAdjustmentChange={setWorkbenchWidthAdjustment}
        />
      </SectionFrame>

      <SectionFrame eyebrow="Lifecycle" title="Trade workflow state" subtitle="User-managed state is persistent and separate from scan qualification and ranking.">
        <div className="space-y-4">
          {/* State badge + state description */}
          <div className="flex flex-wrap items-center gap-3">
            <LifecycleBadge state={lifecycleState} />
            <span className="text-xs text-ink-4">
              {lifecycleState === "new" && "Not yet reviewed — use the actions below to move this trade forward."}
              {lifecycleState === "saved" && "Kept for later review. Revisit when conditions change."}
              {lifecycleState === "watching" && "Actively monitoring this setup across scans."}
              {lifecycleState === "execution_ready" && "Approved for execution consideration. Review the checklist before proceeding."}
              {lifecycleState === "dismissed" && "Removed from active consideration. Restore by saving or watching again."}
            </span>
          </div>

          {/* Action buttons */}
          <LifecycleActions
            currentState={lifecycleState}
            onTransition={setLifecycleState}
            isPending={upsertLifecycle.isPending}
            errorMessage={lifecycleErrorMessage}
          />

          {/* Note editor */}
          <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-3 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-4">Review note</p>
              {noteJustSaved ? (
                <span className="text-xs text-success" role="status">Saved</span>
              ) : savedNote && !noteEditing ? (
                <button
                  type="button"
                  onClick={() => { setNoteDraft(savedNote); setNoteEditing(true); }}
                  className="text-xs text-ink-3 hover:text-ink-2"
                >
                  Edit
                </button>
              ) : null}
            </div>

            {noteEditing ? (
              <div className="space-y-2">
                <textarea
                  value={noteDraft}
                  onChange={(event) => setNoteDraft(event.target.value)}
                  rows={3}
                  className="w-full rounded-card border border-white/10 bg-surface-overlay/70 px-3 py-2 text-sm text-ink-2 focus:outline-none focus:ring-1 focus:ring-accent/30"
                  placeholder="Add a note about this trade state or review…"
                  aria-label="Review note"
                />
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={saveLifecycleNote}
                    disabled={upsertLifecycle.isPending || !noteDraftChanged}
                    className="rounded-card border border-accent/25 bg-accent px-3 py-1.5 text-xs font-semibold text-surface-0 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {upsertLifecycle.isPending ? "Saving…" : "Save note"}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setNoteDraft(savedNote ?? ""); setNoteEditing(false); }}
                    className="rounded-card border border-white/8 px-3 py-1.5 text-xs font-semibold text-ink-3"
                  >
                    Cancel
                  </button>
                  {noteDraftChanged ? (
                    <span className="text-xs text-ink-4">Unsaved changes</span>
                  ) : null}
                </div>
              </div>
            ) : savedNote ? (
              <p className="text-sm leading-6 text-ink-2">{savedNote}</p>
            ) : (
              <button
                type="button"
                onClick={() => setNoteEditing(true)}
                className="text-xs text-ink-4 hover:text-ink-3"
              >
                Add a note about this trade…
              </button>
            )}
          </div>
        </div>
      </SectionFrame>

      <SectionFrame
        eyebrow="Execution ticket"
        title="Execution preparation"
        subtitle="Prepare a structured, auditable execution ticket before any broker submission flow is enabled."
      >
        <ExecutionTicketPanel
          tradeId={tradeId}
          scanId={scanId}
          tradeSnapshot={tradeSnapshot}
          lifecycleState={lifecycleState}
        />
      </SectionFrame>

      <section className="grid gap-3 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
        <SectionFrame eyebrow="Trade construction" title="Structure at a glance" subtitle="Read the spread map before making a sizing decision.">
          <div className="space-y-4">
            <MetricStrip items={model.construction.map((item) => ({ ...item, tone: "neutral" as const }))} columns={3} />
            <ChartPanel title="Strike ladder" subtitle="Use this quick visual ordering to anchor the underlying price against the spread legs.">
              <div className="grid gap-2">
                {model.strikeMarkers.map((item) => (
                  <div key={item.label} className="rounded-card border border-white/8 bg-surface-2/70 px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-ink-1">{item.label}</p>
                      <p className="text-sm font-semibold text-ink-1">{item.value}</p>
                    </div>
                    <p className="mt-1 text-xs text-ink-4">{item.detail}</p>
                  </div>
                ))}
              </div>
            </ChartPanel>
          </div>
        </SectionFrame>

        <SectionFrame eyebrow="Execution checklist" title="What to confirm next" subtitle="A concise operator checklist built from the current trade values.">
          <div className="space-y-4">
            <ChartPanel title="Checklist" subtitle="Move through these items before acting on the trade.">
              <div className="grid gap-2">
                {model.executionPrep.map((item) => (
                  <div key={item} className="rounded-card border border-white/8 bg-surface-2/70 px-3 py-2 text-sm text-ink-2">
                    {item}
                  </div>
                ))}
              </div>
            </ChartPanel>
            <ChartPanel title="Risk profile" subtitle="Compact framing for reward, credit, and downside before execution.">
              <div className="space-y-4">
                <MiniPayoffCue reward={detailQuery.data.trade.net_credit} risk={detailQuery.data.trade.max_risk} rewardLabel="Credit" riskLabel="Risk" size="sm" />
                <p className="text-sm leading-6 text-ink-2">Defined risk stays capped; use the checklist and context below to decide whether the setup still deserves attention.</p>
              </div>
            </ChartPanel>
          </div>
        </SectionFrame>
      </section>

      <section className="grid gap-3 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <SectionFrame eyebrow="Supporting case" title="Supporting signals" subtitle="Keep this section tight: it should confirm the setup, not compete with the brief above.">
          {supportNotes.length > 0 ? (
            <ul className="grid gap-2 text-sm text-ink-2">
              {supportNotes.map((line) => (
                <li key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{line}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No supporting rationale" message="No additional explanation rows were returned for this trade." />
          )}
        </SectionFrame>

        <SectionFrame eyebrow="Confidence context" title="History and portfolio context" subtitle="Use repeat context and concentration as confirmation, not as a replacement for the current brief.">
          <div className="space-y-4">
            <MetricStrip items={model.stability.metrics} columns={4} compact />
            <div className="grid gap-2 text-sm text-ink-2">
              {contextNotes.map((note) => (
                <p key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{note}</p>
              ))}
            </div>
          </div>
        </SectionFrame>
      </section>

      <SectionFrame eyebrow="Actions" title="Next review steps" subtitle="Move to the next decision surface without losing the current brief.">
        <ActionRow>
          {model.actions.map((action, index) => (
            <Link
              key={action.to}
              to={action.to}
              className={[
                "rounded-card px-4 py-2.5 text-sm font-semibold",
                index === 0 ? "border border-accent/25 bg-accent text-surface-0" : "border border-white/10 bg-surface-overlay/70 text-ink-2",
              ].join(" ")}
            >
              {action.label}
            </Link>
          ))}
        </ActionRow>
      </SectionFrame>
    </PageShell>
  );
}
