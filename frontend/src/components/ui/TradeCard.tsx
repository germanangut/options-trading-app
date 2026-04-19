import { Link } from "react-router-dom";
import clsx from "clsx";

import type { ReactNode } from "react";
import { Chip } from "./Chip";
import { MiniPayoffCue } from "./MiniPayoffCue";
import { PortfolioImpactBand } from "./PortfolioImpactBand";
import { ScoreRibbon } from "./ScoreRibbon";
import { SignalChipGroup } from "./SignalChipGroup";
import { StrategyChip } from "./StrategyChip";

type TradeCardMetric = {
  label: string;
  value: string | number;
  detail?: string | null;
  tone?: "accent" | "success" | "warning" | "danger" | "neutral";
};

type TradeCardProps = {
  href?: string | null;
  rank: number;
  title: string;
  subtitle: string;
  direction: string;
  directionTone: "accent" | "success" | "warning" | "danger" | "neutral";
  label: string;
  labelTone: "accent" | "success" | "warning" | "danger" | "neutral";
  freshnessLabel?: string;
  freshnessTone?: "accent" | "success" | "warning" | "danger" | "neutral";
  score: string | number;
  scoreDetail?: string | null;
  strategyLabel?: string;
  metrics: TradeCardMetric[];
  summary: string;
  structure: string[];
  narrative: string[];
  chartLabel?: string;
  riskNote?: string;
  portfolioNote?: string;
  riskProfile?: {
    reward?: number | null;
    risk?: number | null;
  };
  actionLabel?: string;
  footer?: ReactNode;
};

const metricToneClassName = {
  accent: "border-accent/20 bg-accent-soft/28",
  success: "border-success/20 bg-success-soft/28",
  warning: "border-warning/20 bg-warning-soft/28",
  danger: "border-danger/20 bg-danger-soft/28",
  neutral: "border-white/8 bg-surface-2/70",
};

export function TradeCard({
  href,
  rank,
  title,
  subtitle,
  direction,
  directionTone,
  label,
  labelTone,
  freshnessLabel,
  freshnessTone = "neutral",
  score,
  scoreDetail,
  strategyLabel,
  metrics,
  summary,
  structure,
  narrative,
  chartLabel,
  riskNote,
  portfolioNote,
  riskProfile,
  actionLabel,
  footer,
}: TradeCardProps) {
  const rewardValue = Math.max(0, Number(riskProfile?.reward ?? 0));
  const riskValue = Math.max(0, Number(riskProfile?.risk ?? 0));

  return (
    <article className="group relative overflow-hidden rounded-panel border border-white/10 bg-surface-1/88 p-5 shadow-panel transition duration-200 hover:border-white/20 hover:bg-surface-1">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" aria-hidden="true" />
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex h-10 min-w-10 items-center justify-center rounded-pill border border-white/10 bg-surface-overlay/70 px-3 text-sm font-semibold text-ink-2">
              #{rank}
            </span>
            {strategyLabel ? <StrategyChip label={strategyLabel} /> : null}
            <Chip tone={directionTone}>{direction}</Chip>
            <Chip tone={labelTone}>{label}</Chip>
            {freshnessLabel ? <Chip tone={freshnessTone}>{freshnessLabel}</Chip> : null}
          </div>
          <div>
            <h3 className="text-xl font-semibold tracking-tight text-ink-1">{title}</h3>
            <p className="mt-1 text-sm text-ink-3">{subtitle}</p>
          </div>
        </div>
        <div className="w-full max-w-sm">
          <ScoreRibbon score={score} detail={scoreDetail} label="Quality ribbon" size="sm" tone={directionTone === "success" ? "success" : directionTone === "warning" ? "warning" : "accent"} />
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="space-y-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
            <div className="rounded-card border border-white/8 bg-surface-overlay/60 p-4">
              <p className="eyebrow-label">Why It Qualified</p>
              <p className="mt-2 text-sm leading-6 text-ink-2">{summary}</p>
            </div>
            {portfolioNote ? (
              <PortfolioImpactBand
                title="Portfolio Impact"
                message={portfolioNote}
                tone={portfolioNote.toLowerCase().includes("represents") ? "warning" : "neutral"}
              />
            ) : null}
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <div key={metric.label} className={clsx("rounded-card border px-3 py-3", metricToneClassName[metric.tone ?? "neutral"])}>
                <p className="eyebrow-label">{metric.label}</p>
                <p className="mt-1 text-xl font-semibold tracking-tight text-ink-1">{metric.value}</p>
                {metric.detail ? <p className="mt-1 text-xs text-ink-4">{metric.detail}</p> : null}
              </div>
            ))}
          </div>
          {riskNote ? (
            <PortfolioImpactBand title="Risk Frame" message={riskNote} tone="warning" />
          ) : null}
        </div>

        <div className="space-y-4">
          <MiniPayoffCue title="Risk Shape" subtitle={chartLabel ?? "Read the payoff cue before opening detail."} reward={rewardValue} risk={riskValue} rewardLabel="Credit kept" riskLabel="Defined risk" size="sm" />
          <div className="rounded-card border border-white/8 bg-surface-overlay/60 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="eyebrow-label">Structure</p>
              <span className="text-xs text-ink-4">{structure.length} framing point{structure.length === 1 ? "" : "s"}</span>
            </div>
            <div className="mt-3 grid gap-2">
              {structure.map((item) => (
                <div key={item} className="rounded-card border border-white/6 bg-surface-1/70 px-3 py-2 text-sm text-ink-2">
                  {item}
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-card border border-white/8 bg-surface-overlay/60 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="eyebrow-label">Signal Cluster</p>
              <span className="text-xs text-ink-4">{narrative.length} cues</span>
            </div>
            <div className="mt-3">
              <SignalChipGroup items={narrative} />
            </div>
            <p className="mt-3 text-xs leading-5 text-ink-4">These chips summarize why the setup belongs on the ranked board before you inspect the full detail route.</p>
          </div>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/8 pt-4">
        <p className="text-sm text-ink-4">Read the ribbon, check the payoff cue, then use the execution brief only for the cards that still fit your risk and concentration view.</p>
        {href ? (
          <Link to={href} className="rounded-card border border-accent/25 bg-accent px-4 py-2.5 text-sm font-semibold text-surface-0 shadow-elevated">
            {actionLabel ?? "Open trade"}
          </Link>
        ) : null}
      </div>

      {footer ? <div className="mt-3 text-sm text-ink-3">{footer}</div> : null}
    </article>
  );
}