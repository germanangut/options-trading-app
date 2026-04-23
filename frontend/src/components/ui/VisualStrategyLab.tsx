import { useMemo, useState } from "react";

import { formatCurrency } from "../../lib/formatters";
import type { StrategyVariant, VariantSet } from "../../types/api";
import { PayoffCurve } from "./PayoffCurve";


type VisualStrategyLabProps = {
  variantSet: VariantSet | null | undefined;
  isLoading?: boolean;
};

function formatSignedCurrency(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatCurrency(value)}`;
}

function formatSignedNumber(value: number, precision = 2) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(precision)}`;
}

function metricTone(delta: number) {
  if (delta > 0) return "text-success";
  if (delta < 0) return "text-danger";
  return "text-ink-4";
}

function VariantDeltaRows({ variant }: { variant: StrategyVariant }) {
  const c = variant.comparison;
  if (!c) {
    return <p className="text-xs text-ink-4">Comparison data unavailable.</p>;
  }

  return (
    <div className="grid gap-2 text-xs sm:grid-cols-2">
      <div className="rounded-card border border-white/8 bg-surface-2/45 px-3 py-2">
        <p className="eyebrow-label">Credit vs Baseline</p>
        <p className={`mt-1 font-semibold ${metricTone(c.delta_net_credit)}`}>{formatSignedCurrency(c.delta_net_credit * 100)}</p>
      </div>
      <div className="rounded-card border border-white/8 bg-surface-2/45 px-3 py-2">
        <p className="eyebrow-label">Max Loss vs Baseline</p>
        <p className={`mt-1 font-semibold ${metricTone(-c.delta_max_loss)}`}>{formatSignedCurrency(c.delta_max_loss)}</p>
      </div>
      <div className="rounded-card border border-white/8 bg-surface-2/45 px-3 py-2">
        <p className="eyebrow-label">Breakeven vs Baseline</p>
        <p className={`mt-1 font-semibold ${metricTone(c.delta_breakeven)}`}>{formatSignedNumber(c.delta_breakeven, 2)}</p>
      </div>
      <div className="rounded-card border border-white/8 bg-surface-2/45 px-3 py-2">
        <p className="eyebrow-label">Width vs Baseline</p>
        <p className={`mt-1 font-semibold ${metricTone(c.delta_spread_width)}`}>{formatSignedNumber(c.delta_spread_width, 2)}</p>
      </div>
    </div>
  );
}

function VariantSummaryCard({ variant, title }: { variant: StrategyVariant; title: string }) {
  return (
    <div className="space-y-3 rounded-card border border-white/10 bg-surface-overlay/45 p-3">
      <div>
        <p className="eyebrow-label">{title}</p>
        <p className="mt-1 text-sm font-semibold text-ink-1">{variant.label}</p>
        <p className="mt-1 text-xs text-ink-4">{variant.rationale}</p>
      </div>
      <div className="grid gap-2 text-xs sm:grid-cols-2">
        <div>
          <p className="eyebrow-label">Net Credit</p>
          <p className="mt-1 text-ink-2">{formatCurrency(variant.net_credit * 100)}</p>
        </div>
        <div>
          <p className="eyebrow-label">Spread Width</p>
          <p className="mt-1 text-ink-2">{variant.spread_width.toFixed(2)}</p>
        </div>
        <div>
          <p className="eyebrow-label">Max Profit</p>
          <p className="mt-1 text-ink-2">{formatCurrency(variant.max_profit)}</p>
        </div>
        <div>
          <p className="eyebrow-label">Max Loss</p>
          <p className="mt-1 text-ink-2">{formatCurrency(variant.max_loss)}</p>
        </div>
        <div>
          <p className="eyebrow-label">Breakeven</p>
          <p className="mt-1 text-ink-2">{variant.breakeven.toFixed(2)}</p>
        </div>
        <div>
          <p className="eyebrow-label">Strikes</p>
          <p className="mt-1 text-ink-2">{variant.short_strike.toFixed(2)} / {variant.long_strike.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}

export function VisualStrategyLab({ variantSet, isLoading = false }: VisualStrategyLabProps) {
  const variants = variantSet?.variants ?? [];
  const baseline = variants.find((variant) => variant.variant_type === "baseline") ?? null;
  const compareTargets = variants.filter((variant) => variant.variant_type !== "baseline");

  const [selectedVariantType, setSelectedVariantType] = useState<string | null>(null);

  const selectedVariant = useMemo(() => {
    if (!compareTargets.length) {
      return null;
    }

    if (selectedVariantType) {
      const found = compareTargets.find((variant) => variant.variant_type === selectedVariantType);
      if (found) return found;
    }

    return compareTargets[0];
  }, [compareTargets, selectedVariantType]);

  if (isLoading) {
    return <p className="text-xs text-ink-4">Loading visual strategy lab...</p>;
  }

  if (!baseline) {
    return (
      <p className="text-xs text-ink-4">
        Visual strategy lab is unavailable because a baseline payoff structure could not be loaded for this trade.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-xs leading-5 text-ink-4">
        Baseline is pinned for reference. Select one variant to compare payoff shape and structural trade-offs without changing the selected trade.
      </p>

      <div className="space-y-2">
        <p className="eyebrow-label">Compare target</p>
        {compareTargets.length === 0 ? (
          <p className="text-xs text-ink-4">No clean variant was found for this setup, so only baseline is available for visual analysis.</p>
        ) : (
          <div className="flex flex-wrap gap-2" role="tablist" aria-label="Variant compare selector">
            {compareTargets.map((variant) => {
              const isSelected = selectedVariant?.variant_type === variant.variant_type;
              return (
                <button
                  key={variant.variant_type}
                  type="button"
                  role="tab"
                  aria-selected={isSelected}
                  onClick={() => setSelectedVariantType(variant.variant_type)}
                  className={[
                    "rounded-card border px-3 py-1.5 text-xs font-semibold",
                    isSelected
                      ? "border-accent/30 bg-accent-soft/35 text-ink-1"
                      : "border-white/10 bg-surface-2/40 text-ink-3",
                  ].join(" ")}
                >
                  {variant.variant_type === "conservative" ? "Conservative" : "Max Credit"}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <VariantSummaryCard variant={baseline} title="Baseline" />
        {selectedVariant ? <VariantSummaryCard variant={selectedVariant} title="Selected Variant" /> : null}
      </div>

      {selectedVariant ? (
        <div className="space-y-3 rounded-card border border-white/10 bg-surface-overlay/35 p-3">
          <p className="text-xs font-semibold text-ink-2">Change vs baseline</p>
          <p className="text-xs text-ink-4">{selectedVariant.comparison?.summary ?? "Variant delta summary unavailable."}</p>
          <VariantDeltaRows variant={selectedVariant} />
        </div>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-2">
        <div>
          <p className="mb-2 text-xs font-semibold text-ink-2">Baseline payoff</p>
          <PayoffCurve points={baseline.payoff?.payoff_points ?? []} />
        </div>
        {selectedVariant ? (
          <div>
            <p className="mb-2 text-xs font-semibold text-ink-2">Selected variant payoff</p>
            <PayoffCurve points={selectedVariant.payoff?.payoff_points ?? []} />
          </div>
        ) : null}
      </div>
    </div>
  );
}
