import clsx from "clsx";

import type { StrategyVariant, VariantSet } from "../../types/api";
import { formatCurrency } from "../../lib/formatters";


type VariantTone = "neutral" | "conservative" | "max_credit";

const VARIANT_TONE_CLASSES: Record<VariantTone, { card: string; badge: string; badgeText: string }> = {
  neutral: {
    card: "border-white/10 bg-surface-overlay/50",
    badge: "bg-surface-2/80 text-ink-3",
    badgeText: "Baseline",
  },
  conservative: {
    card: "border-success/20 bg-success-soft/10",
    badge: "bg-success-soft/30 text-success",
    badgeText: "Conservative",
  },
  max_credit: {
    card: "border-warning/20 bg-warning-soft/10",
    badge: "bg-warning-soft/30 text-warning",
    badgeText: "Max Credit",
  },
};

function variantTone(type: StrategyVariant["variant_type"]): VariantTone {
  if (type === "conservative") return "conservative";
  if (type === "max_credit") return "max_credit";
  return "neutral";
}

type VariantCardProps = {
  variant: StrategyVariant;
};

function VariantCard({ variant }: VariantCardProps) {
  const tone = variantTone(variant.variant_type);
  const toneClass = VARIANT_TONE_CLASSES[tone];
  const breakeven = variant.breakeven;

  return (
    <div
      className={clsx(
        "rounded-card border p-3 space-y-3",
        toneClass.card,
      )}
    >
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <span
          className={clsx(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wider",
            toneClass.badge,
          )}
        >
          {toneClass.badgeText}
        </span>
        {variant.is_credit_estimated && (
          <span className="text-[0.6rem] text-ink-4 italic">credit estimated</span>
        )}
      </div>

      {/* User-facing label */}
      <p className="text-xs leading-5 text-ink-2">{variant.label}</p>

      {/* Key economics grid */}
      <div className="grid grid-cols-3 gap-2">
        <div className="space-y-0.5">
          <p className="eyebrow-label text-[0.6rem]">Net Credit</p>
          <p className="text-sm font-semibold text-success">{formatCurrency(variant.net_credit * 100)}</p>
        </div>
        <div className="space-y-0.5">
          <p className="eyebrow-label text-[0.6rem]">Max Profit</p>
          <p className="text-sm font-semibold text-ink-1">{formatCurrency(variant.max_profit)}</p>
        </div>
        <div className="space-y-0.5">
          <p className="eyebrow-label text-[0.6rem]">Max Loss</p>
          <p className="text-sm font-semibold text-danger">{formatCurrency(variant.max_loss)}</p>
        </div>
      </div>

      {/* Strike / breakeven row */}
      <div className="grid grid-cols-2 gap-2 text-xs text-ink-3">
        <div>
          <span className="eyebrow-label text-[0.6rem] block">Strikes</span>
          <span>${variant.short_strike.toFixed(2)} / ${variant.long_strike.toFixed(2)}</span>
        </div>
        <div>
          <span className="eyebrow-label text-[0.6rem] block">Breakeven</span>
          <span>${breakeven.toFixed(2)}</span>
        </div>
      </div>

      {/* Rationale */}
      <div className="rounded-card border border-white/6 bg-surface-2/40 px-2.5 py-2">
        <p className="text-[0.7rem] leading-4 text-ink-4">{variant.rationale}</p>
      </div>
    </div>
  );
}

type VariantComparisonPanelProps = {
  variantSet: VariantSet | null | undefined;
  isLoading?: boolean;
};

export function VariantComparisonPanel({ variantSet, isLoading = false }: VariantComparisonPanelProps) {
  if (isLoading) {
    return (
      <p className="text-xs text-ink-4">Loading strategy variants...</p>
    );
  }

  if (!variantSet || variantSet.variants.length === 0) {
    return (
      <p className="text-xs text-ink-4">
        No variants available for this trade. Variants require a supported spread strategy with sufficient price data.
      </p>
    );
  }

  const ORDER: StrategyVariant["variant_type"][] = ["baseline", "conservative", "max_credit"];
  const sorted = [...variantSet.variants].sort(
    (a, b) => ORDER.indexOf(a.variant_type) - ORDER.indexOf(b.variant_type),
  );

  return (
    <div className="space-y-3">
      <p className="text-xs leading-5 text-ink-4">
        Compare how small strike adjustments change credit, breakeven, and risk profile. Credits for
        non-baseline variants are estimated from the baseline moneyness — not real chain quotes.
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        {sorted.map((variant) => (
          <VariantCard key={variant.variant_type} variant={variant} />
        ))}
      </div>
    </div>
  );
}
