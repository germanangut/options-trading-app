import { Link, useParams } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { ChartPanel } from "../components/ui/ChartPanel";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { MiniPayoffCue } from "../components/ui/MiniPayoffCue";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { ScoreRibbon } from "../components/ui/ScoreRibbon";
import { SectionFrame } from "../components/ui/SectionFrame";
import { Chip } from "../components/ui/Chip";
import { WarningBand } from "../components/ui/WarningBand";
import { useScanById } from "../features/scans/hooks/useScanById";
import { useTradeDetail } from "../features/scans/hooks/useTradeDetail";
import { selectTradeDetailExperienceModel } from "../features/scans/selectors/decisionExperienceSelectors";
import { describeApiError } from "../lib/apiErrors";

export function QualifiedTradeDetailPage() {
  const { scanId, tradeId } = useParams();
  const scanQuery = useScanById(scanId);
  const detailQuery = useTradeDetail(scanId, tradeId);

  if (scanQuery.isLoading || detailQuery.isLoading) {
    return <EmptyState title="Loading trade detail" message="Waiting for the trade detail contract and scan context." />;
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
      <EmptyState title="Trade not found" message="The trade detail route is explicit, but the backend did not return a matching trade for this scan." />
    );
  }

  const model = selectTradeDetailExperienceModel(scanQuery.data, detailQuery.data);

  return (
    <PageShell
      eyebrow="Trade Detail"
      title={model.header.title}
      description={model.header.subtitle}
      actions={
        <ActionRow>
          <Chip tone={model.header.directionTone}>{model.header.direction}</Chip>
          <Chip tone={model.header.statusTone}>{model.header.statusLabel}</Chip>
        </ActionRow>
      }
    >
      <SectionFrame eyebrow="Execution Briefing" title="One-glance trade brief" subtitle="Understand the setup immediately, then move deeper without losing the story.">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <div className="space-y-4">
            <ChartPanel title="Why this trade surfaced" subtitle="The backend-provided explanation remains the authority for why this idea is on the board." className="bg-surface-1/92">
              <div className="space-y-4">
                <p className="text-base leading-7 text-ink-1">{model.quickVerdict}</p>
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
                subtitle="The cue is explanatory only; the trade-detail payload remains the source of truth."
              />
            </ChartPanel>
          </div>

          <div className="space-y-4">
            <ScoreRibbon score={model.riskReward.find((item) => item.label === "Score")?.value ?? "-"} detail="Read this first, then confirm structure, payout, and concentration." label="Decision Quality" />
            <ChartPanel title="Primary decision numbers" subtitle="Read the score and risk block before going deeper into structure.">
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

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
        <SectionFrame eyebrow="Trade Construction" title="Contract structure" subtitle="Read the spread map before making a sizing decision.">
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

        <SectionFrame eyebrow="Execution Checklist" title="What to confirm next" subtitle="A concise operator checklist built only from current trade-detail values.">
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
                <p className="text-sm leading-6 text-ink-2">Defined risk stays capped; use the checklist and history context to decide whether the setup still deserves attention.</p>
              </div>
            </ChartPanel>
          </div>
        </SectionFrame>
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <SectionFrame eyebrow="Why This Trade" title="Supporting signals" subtitle="Explanation fields and score-breakdown rows already present in the payload.">
          {model.whyThisTrade.length > 0 ? (
            <ul className="grid gap-2 text-sm text-ink-2">
              {model.whyThisTrade.map((line) => (
                <li key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{line}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No rationale provided" message="The trade-detail payload did not return additional explanation rows." />
          )}
        </SectionFrame>

        <SectionFrame eyebrow="History / Portfolio" title="Context from this scan and current history payload" subtitle="Use history and portfolio notes as decision context, not as separate ranking logic.">
          <div className="space-y-4">
            <MetricStrip items={model.stability.metrics} columns={4} compact />
            <div className="grid gap-2 text-sm text-ink-2">
              {[...model.stability.notes, ...model.historyStory, ...model.portfolioImpact.notes.slice(1)].map((note) => (
                <p key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{note}</p>
              ))}
            </div>
          </div>
        </SectionFrame>
      </section>

      <SectionFrame eyebrow="Actions" title="Complete your review" subtitle="Keep route handling explicit and move to the next decision surface.">
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
