type MiniPayoffCueProps = {
  title?: string;
  subtitle?: string;
  reward?: number | null;
  risk?: number | null;
  rewardLabel?: string;
  riskLabel?: string;
  size?: "sm" | "md";
};

export function MiniPayoffCue({
  title = "Payoff cue",
  subtitle,
  reward,
  risk,
  rewardLabel = "Credit kept",
  riskLabel = "Risk carried",
  size = "md",
}: MiniPayoffCueProps) {
  const rewardValue = Math.max(0, Number(reward ?? 0));
  const riskValue = Math.max(0, Number(risk ?? 0));
  const total = rewardValue + riskValue;
  const rewardWidth = total > 0 ? Math.max(10, Math.min(86, (rewardValue / total) * 100)) : 24;

  return (
    <section className="rounded-card border border-white/8 bg-surface-overlay/60 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="eyebrow-label">{title}</p>
          {subtitle ? <p className="mt-1 text-xs leading-5 text-ink-4">{subtitle}</p> : null}
        </div>
        <div className="text-right text-xs text-ink-4">
          <p>{rewardLabel}</p>
          <p>{riskLabel}</p>
        </div>
      </div>

      <div className="mt-4 overflow-hidden rounded-pill border border-white/8 bg-surface-1/70 p-1">
        <div className={size === "sm" ? "flex h-2.5 gap-1" : "flex h-3 gap-1"}>
          <div className="rounded-pill bg-gradient-to-r from-accent to-success" style={{ width: `${rewardWidth}%` }} />
          <div className="flex-1 rounded-pill bg-gradient-to-r from-warning to-danger" />
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-ink-4">
        <div className="rounded-card border border-white/6 bg-surface-1/70 px-3 py-2">
          <p className="eyebrow-label">{rewardLabel}</p>
          <p className="mt-1 text-sm font-semibold text-ink-1">{rewardValue > 0 ? rewardValue.toFixed(2) : "-"}</p>
        </div>
        <div className="rounded-card border border-white/6 bg-surface-1/70 px-3 py-2">
          <p className="eyebrow-label">{riskLabel}</p>
          <p className="mt-1 text-sm font-semibold text-ink-1">{riskValue > 0 ? riskValue.toFixed(2) : "-"}</p>
        </div>
      </div>
    </section>
  );
}