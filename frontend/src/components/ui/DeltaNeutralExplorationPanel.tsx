import { MetricStrip } from "./MetricStrip";
import { PayoffCurve } from "./PayoffCurve";
import { formatCurrency } from "../../lib/formatters";
import type { DeltaNeutralExploration } from "../../types/api";


type DeltaNeutralExplorationPanelProps = {
  data: DeltaNeutralExploration | null | undefined;
  isLoading: boolean;
};


function formatSigned(value: number, decimals = 3): string {
  if (!Number.isFinite(value)) return "-";
  if (value > 0) return `+${value.toFixed(decimals)}`;
  return value.toFixed(decimals);
}


export function DeltaNeutralExplorationPanel({ data, isLoading }: DeltaNeutralExplorationPanelProps) {
  if (isLoading) {
    return <p className="text-xs text-ink-4">Loading directional comparison...</p>;
  }

  if (!data) {
    return <p className="text-xs text-ink-4">Delta-neutral exploration is unavailable for this trade.</p>;
  }

  const baseline = data.baseline;
  const candidate = data.neutral_candidate;
  const comparison = data.comparison;

  const baselineItems = [
    { label: "Directional exposure", value: formatSigned(baseline.net_delta), tone: "accent" as const },
    { label: "Max Profit", value: formatCurrency(baseline.max_profit), tone: "success" as const },
    { label: "Max Loss", value: formatCurrency(baseline.max_loss), tone: "danger" as const },
    { label: "Breakeven", value: `$${baseline.breakeven.toFixed(2)}`, tone: "neutral" as const },
  ];

  const candidateItems = candidate
    ? [
        { label: "Directional exposure", value: formatSigned(candidate.net_delta), tone: "accent" as const },
        { label: "Max Profit", value: formatCurrency(candidate.max_profit), tone: "success" as const },
        { label: "Max Loss", value: formatCurrency(candidate.max_loss), tone: "danger" as const },
        { label: "Breakeven", value: `$${candidate.breakeven.toFixed(2)}`, tone: "neutral" as const },
      ]
    : [];

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-card border border-white/8 bg-surface-2/60 p-3 space-y-2">
          <p className="eyebrow-label">Baseline</p>
          <p className="text-sm text-ink-2">Current directional spread</p>
          <MetricStrip items={baselineItems} columns={2} compact />
        </div>

        <div className="rounded-card border border-white/8 bg-surface-2/60 p-3 space-y-2">
          <p className="eyebrow-label">Closer to neutral</p>
          {candidate ? (
            <>
              <p className="text-sm text-ink-2">Reduced directional bias candidate</p>
              <MetricStrip items={candidateItems} columns={2} compact />
            </>
          ) : (
            <>
              <p className="text-sm text-ink-2">No clean delta-neutral alternative found.</p>
              <p className="text-xs text-ink-4">{data.unavailable_reason ?? "Directional reduction candidate was unavailable."}</p>
            </>
          )}
        </div>
      </div>

      {comparison ? (
        <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-3 space-y-2">
          <p className="eyebrow-label">Trade-off summary</p>
          <p className="text-sm text-ink-2">{comparison.summary}</p>
          <div className="grid gap-2 sm:grid-cols-3 text-xs">
            <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2">
              <p className="text-ink-4">Delta reduction</p>
              <p className="text-ink-2 font-semibold">{comparison.delta_reduction_pct.toFixed(1)}%</p>
            </div>
            <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2">
              <p className="text-ink-4">Max profit change</p>
              <p className="text-ink-2 font-semibold">{formatCurrency(comparison.delta_max_profit)}</p>
            </div>
            <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2">
              <p className="text-ink-4">Max loss change</p>
              <p className="text-ink-2 font-semibold">{formatCurrency(comparison.delta_max_loss)}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="eyebrow-label mb-2">Baseline payoff</p>
          {baseline.payoff?.payoff_points?.length ? (
            <PayoffCurve points={baseline.payoff.payoff_points} />
          ) : (
            <p className="text-xs text-ink-4">Payoff curve unavailable for baseline.</p>
          )}
        </div>
        <div>
          <p className="eyebrow-label mb-2">Neutral candidate payoff</p>
          {candidate?.payoff?.payoff_points?.length ? (
            <PayoffCurve points={candidate.payoff.payoff_points} />
          ) : (
            <p className="text-xs text-ink-4">No payoff curve available for neutral candidate.</p>
          )}
        </div>
      </div>

      <p className="text-xs text-ink-4">{data.rationale}</p>
      {data.limitation_note ? <p className="text-[0.7rem] text-ink-4">{data.limitation_note}</p> : null}
    </div>
  );
}
