import { Link, useParams } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { Banner } from "../components/ui/Banner";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { SectionFrame } from "../components/ui/SectionFrame";
import { Chip } from "../components/ui/Chip";
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
      <Banner tone="danger" title="Unable to load trade detail">
        {describeApiError(error, "load", "trade detail").message}
      </Banner>
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
    <div className="grid gap-6">
      <SectionFrame
        eyebrow="Trade Detail"
        title={model.header.title}
        subtitle={model.header.subtitle}
        actions={
          <div className="flex flex-wrap gap-2">
            <Chip tone={model.header.directionTone}>{model.header.direction}</Chip>
            <Chip tone={model.header.statusTone}>{model.header.statusLabel}</Chip>
          </div>
        }
      >
        <Banner tone={model.diagnostics.tone} title={model.diagnostics.title}>
          {model.diagnostics.message}
        </Banner>
      </SectionFrame>

      <SectionFrame eyebrow="Quick Verdict" title="Execution-prep readout" subtitle="Use the backend-provided explanation before drilling into structure and risk.">
        <p className="text-sm leading-6 text-ink-2">{model.quickVerdict}</p>
      </SectionFrame>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
        <SectionFrame eyebrow="Trade Construction" title="Contract structure" subtitle="Presentation mapping of the current trade-detail payload.">
          <MetricStrip items={model.construction.map((item) => ({ ...item, tone: "neutral" as const }))} columns={3} />
        </SectionFrame>

        <SectionFrame eyebrow="Risk / Reward" title="Primary decision numbers" subtitle="No client-side score or qualification logic is added here.">
          <MetricStrip items={model.riskReward} columns={3} />
        </SectionFrame>
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <SectionFrame eyebrow="Why This Trade" title="Supporting signals" subtitle="Explanation fields and score-breakdown rows already present in the payload.">
          {model.whyThisTrade.length > 0 ? (
            <ul className="grid gap-2 text-sm text-ink-2">
              {model.whyThisTrade.map((line) => (
                <li key={line} className="rounded-xl bg-surface-2 px-3 py-3">{line}</li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No rationale provided" message="The trade-detail payload did not return additional explanation rows." />
          )}
        </SectionFrame>

        <SectionFrame eyebrow="Stability / History" title="Context from this scan and current history payload" subtitle="Uses current backend fields only.">
          <div className="space-y-4">
            <MetricStrip items={model.stability.metrics} columns={4} compact />
            <div className="grid gap-2 text-sm text-ink-2">
              {model.stability.notes.map((note) => (
                <p key={note} className="rounded-xl bg-surface-2 px-3 py-3">{note}</p>
              ))}
            </div>
          </div>
        </SectionFrame>
      </section>

      <SectionFrame eyebrow="Portfolio Impact" title={model.portfolioImpact.posture} subtitle="Portfolio-facing context from the same scan contract.">
        {model.portfolioImpact.notes.length > 0 ? (
          <div className="grid gap-2 text-sm text-ink-2">
            {model.portfolioImpact.notes.map((note) => (
              <p key={note} className="rounded-xl bg-surface-2 px-3 py-3">{note}</p>
            ))}
          </div>
        ) : (
          <EmptyState title="Thin portfolio context" message="The current scan did not return richer portfolio notes for this trade." />
        )}
      </SectionFrame>

      <SectionFrame eyebrow="Actions" title="Complete your review" subtitle="Keep route handling explicit and move to the next decision surface.">
        <ActionRow>
          {model.actions.map((action, index) => (
            <Link
              key={action.to}
              to={action.to}
              className={[
                "rounded-xl px-4 py-2 text-sm font-semibold",
                index === 0 ? "bg-accent text-white" : "border border-slate-200 bg-white text-ink-2",
              ].join(" ")}
            >
              {action.label}
            </Link>
          ))}
        </ActionRow>
      </SectionFrame>
    </div>
  );
}
