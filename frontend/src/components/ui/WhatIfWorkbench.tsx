/**
 * WhatIfWorkbench — PU-15B.4 compact what-if strategy workbench.
 *
 * Lets the user explore controlled analytical changes to the current spread
 * (short-strike shift, spread-width adjustment) and immediately see how
 * payoff and trade structure change relative to the baseline.
 *
 * Design constraints:
 * - Guided segmented controls only; no free-form strike entry.
 * - Backend owns all scenario math.
 * - Baseline always stays visible alongside the current scenario.
 * - Delta-neutral is deferred; expiration-shift is deferred.
 * - This is analytical only — never execution-ready.
 */

import { useState } from "react";
import clsx from "clsx";

import { PayoffCurve } from "./PayoffCurve";
import { MetricStrip } from "./MetricStrip";
import type {
  WorkbenchResult,
  WorkbenchScenario,
  WorkbenchStrikeShift,
  WorkbenchWidthAdjustment,
} from "../../types/api";
import { formatCurrency } from "../../lib/formatters";


// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function DeltaBadge({ value, unit = "$", invert = false }: { value: number; unit?: string; invert?: boolean }) {
  if (Math.abs(value) < 0.005) {
    return <span className="text-ink-4 text-xs">—</span>;
  }
  const positive = invert ? value < 0 : value > 0;
  return (
    <span className={clsx("text-xs font-semibold", positive ? "text-success" : "text-danger")}>
      {value > 0 ? "+" : ""}
      {unit}{Math.abs(value).toFixed(2)}
    </span>
  );
}

function SegmentedControl<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-4">{label}</p>
      <div className="flex gap-1.5 flex-wrap">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={clsx(
              "rounded-card border px-3 py-1.5 text-xs font-semibold transition-colors",
              value === opt.value
                ? "border-accent/40 bg-accent/15 text-accent"
                : "border-white/8 bg-surface-2/60 text-ink-3 hover:border-white/15 hover:text-ink-2",
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ScenarioCard({
  scenario,
  label,
  eyebrow,
  tone = "neutral",
}: {
  scenario: WorkbenchScenario;
  label?: string;
  eyebrow: string;
  tone?: "neutral" | "accent";
}) {
  const metrics = [
    { label: "Net Credit", value: formatCurrency(scenario.net_credit), tone: "success" as const },
    { label: "Max Profit", value: formatCurrency(scenario.max_profit), tone: "success" as const },
    { label: "Max Loss", value: formatCurrency(scenario.max_loss), tone: "danger" as const },
    { label: "Breakeven", value: `$${scenario.breakeven.toFixed(2)}`, tone: "accent" as const },
    { label: "Width", value: `$${scenario.spread_width.toFixed(2)}`, tone: "neutral" as const },
  ];

  return (
    <div
      className={clsx(
        "rounded-card border p-4 space-y-3",
        tone === "accent"
          ? "border-accent/20 bg-accent/5"
          : "border-white/8 bg-surface-2/60",
      )}
    >
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-ink-4">{eyebrow}</p>
          <p className="mt-0.5 text-sm font-semibold text-ink-1">{label ?? scenario.label}</p>
        </div>
        <div className="flex gap-1.5 text-xs text-ink-4">
          <span>${scenario.short_strike.toFixed(2)}</span>
          <span>/</span>
          <span>${scenario.long_strike.toFixed(2)}</span>
        </div>
      </div>
      <MetricStrip items={metrics} columns={5} compact />
      {scenario.is_credit_estimated && (
        <p className="text-[0.7rem] text-ink-4">Credit estimated — analytical only, not from live chain.</p>
      )}
    </div>
  );
}


// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

type WhatIfWorkbenchProps = {
  scanId: string | undefined;
  tradeId: string | undefined;
  result: WorkbenchResult | null | undefined;
  isLoading: boolean;
  strikeShift: WorkbenchStrikeShift;
  widthAdjustment: WorkbenchWidthAdjustment;
  onStrikeShiftChange: (v: WorkbenchStrikeShift) => void;
  onWidthAdjustmentChange: (v: WorkbenchWidthAdjustment) => void;
};

export function WhatIfWorkbench({
  result,
  isLoading,
  strikeShift,
  widthAdjustment,
  onStrikeShiftChange,
  onWidthAdjustmentChange,
}: WhatIfWorkbenchProps) {
  // Fallback option lists when the API hasn't returned yet (or is loading)
  const strikeShiftOptions: { value: WorkbenchStrikeShift; label: string }[] =
    result?.strike_shift_options?.length
      ? (result.strike_shift_options as { value: WorkbenchStrikeShift; label: string }[])
      : [
          { value: "further_otm", label: "Further out-of-the-money" },
          { value: "baseline", label: "Baseline" },
          { value: "closer_atm", label: "Closer for more credit" },
        ];

  const widthOptions: { value: WorkbenchWidthAdjustment; label: string }[] =
    result?.width_options?.length
      ? (result.width_options as { value: WorkbenchWidthAdjustment; label: string }[])
      : [
          { value: "narrower", label: "Narrower spread" },
          { value: "baseline", label: "Baseline" },
          { value: "wider", label: "Wider spread" },
        ];

  const isBaselineSelected = strikeShift === "baseline" && widthAdjustment === "baseline";

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="space-y-3">
          <SegmentedControl<WorkbenchStrikeShift>
            label="Short strike"
            options={strikeShiftOptions}
            value={strikeShift}
            onChange={onStrikeShiftChange}
          />
          <SegmentedControl<WorkbenchWidthAdjustment>
            label="Spread width"
            options={widthOptions}
            value={widthAdjustment}
            onChange={onWidthAdjustmentChange}
          />
        </div>
        <p className="text-xs text-ink-4">Loading scenario...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="space-y-4">
        <div className="space-y-3">
          <SegmentedControl<WorkbenchStrikeShift>
            label="Short strike"
            options={strikeShiftOptions}
            value={strikeShift}
            onChange={onStrikeShiftChange}
          />
          <SegmentedControl<WorkbenchWidthAdjustment>
            label="Spread width"
            options={widthOptions}
            value={widthAdjustment}
            onChange={onWidthAdjustmentChange}
          />
        </div>
        <p className="text-xs text-ink-4">Workbench is unavailable for this trade.</p>
      </div>
    );
  }

  const baseline = result.baseline;
  const scenario = result.scenario;
  const comparison = result.comparison;
  const baselinePoints = baseline.payoff?.payoff_points ?? [];
  const scenarioPoints = scenario?.payoff?.payoff_points ?? [];

  return (
    <div className="space-y-5">
      {/* Controls */}
      <div className="grid gap-3 sm:grid-cols-2">
        <SegmentedControl<WorkbenchStrikeShift>
          label="Short strike"
          options={strikeShiftOptions}
          value={strikeShift}
          onChange={onStrikeShiftChange}
        />
        <SegmentedControl<WorkbenchWidthAdjustment>
          label="Spread width"
          options={widthOptions}
          value={widthAdjustment}
          onChange={onWidthAdjustmentChange}
        />
      </div>

      {/* Baseline-only state */}
      {isBaselineSelected && (
        <div className="space-y-3">
          <ScenarioCard scenario={baseline} eyebrow="Baseline" label="Current scanned setup" />
          {baselinePoints.length >= 2 && (
            <div>
              <p className="eyebrow-label mb-2">Payoff curve</p>
              <PayoffCurve points={baselinePoints} />
            </div>
          )}
          <p className="text-xs text-ink-4">
            Select a different short strike or spread width above to explore what-if scenarios.
          </p>
        </div>
      )}

      {/* Unavailable state */}
      {!isBaselineSelected && !scenario && result.unavailable_reason && (
        <div className="space-y-3">
          <ScenarioCard scenario={baseline} eyebrow="Baseline" label="Current scanned setup" />
          <div className="rounded-card border border-warning/20 bg-warning/5 px-4 py-3">
            <p className="text-xs font-semibold text-warning mb-1">No clean alternative found</p>
            <p className="text-xs text-ink-3">{result.unavailable_reason}</p>
          </div>
        </div>
      )}

      {/* Active scenario comparison */}
      {!isBaselineSelected && scenario && (
        <div className="space-y-4">
          {/* Scenario cards side by side */}
          <div className="grid gap-3 sm:grid-cols-2">
            <ScenarioCard scenario={baseline} eyebrow="Baseline" label="Current scanned setup" />
            <ScenarioCard scenario={scenario} eyebrow="What-if scenario" tone="accent" />
          </div>

          {/* Comparison summary */}
          {comparison && (
            <div className="rounded-card border border-white/8 bg-surface-overlay/40 p-4 space-y-3">
              <p className="eyebrow-label">Change vs. baseline</p>
              <p className="text-sm text-ink-2">{comparison.summary}</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 text-xs">
                <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2 space-y-1">
                  <p className="text-ink-4">Credit</p>
                  <DeltaBadge value={comparison.delta_net_credit} />
                </div>
                <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2 space-y-1">
                  <p className="text-ink-4">Max profit</p>
                  <DeltaBadge value={comparison.delta_max_profit} />
                </div>
                <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2 space-y-1">
                  <p className="text-ink-4">Max loss</p>
                  {/* More loss is bad, so invert positive = bad */}
                  <DeltaBadge value={comparison.delta_max_loss} invert />
                </div>
                <div className="rounded-card border border-white/8 bg-surface-2/60 px-3 py-2 space-y-1">
                  <p className="text-ink-4">Spread width</p>
                  <DeltaBadge value={comparison.delta_spread_width} unit="$" />
                </div>
              </div>
            </div>
          )}

          {/* Side-by-side payoff curves */}
          {(baselinePoints.length >= 2 || scenarioPoints.length >= 2) && (
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <p className="eyebrow-label mb-2">Baseline payoff</p>
                {baselinePoints.length >= 2 ? (
                  <PayoffCurve points={baselinePoints} />
                ) : (
                  <p className="text-xs text-ink-4">Payoff curve unavailable for baseline.</p>
                )}
              </div>
              <div>
                <p className="eyebrow-label mb-2">Scenario payoff</p>
                {scenarioPoints.length >= 2 ? (
                  <PayoffCurve points={scenarioPoints} />
                ) : (
                  <p className="text-xs text-ink-4">Payoff curve unavailable for this scenario.</p>
                )}
              </div>
            </div>
          )}

          <p className="text-[0.7rem] text-ink-4">
            Scenarios are analytical only. Credit is estimated using moneyness approximation — not from live
            chain data. Do not use for execution decisions.
          </p>
        </div>
      )}
    </div>
  );
}
