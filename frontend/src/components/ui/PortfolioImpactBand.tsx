import clsx from "clsx";

type PortfolioImpactBandTone = "neutral" | "accent" | "success" | "warning";

type PortfolioImpactBandProps = {
  title: string;
  message: string;
  tone?: PortfolioImpactBandTone;
};

const toneClasses: Record<PortfolioImpactBandTone, string> = {
  neutral: "border-white/8 bg-surface-overlay/60",
  accent: "border-accent/20 bg-accent-soft/24",
  success: "border-success/20 bg-success-soft/24",
  warning: "border-warning/20 bg-warning-soft/24",
};

export function PortfolioImpactBand({ title, message, tone = "neutral" }: PortfolioImpactBandProps) {
  return (
    <div className={clsx("rounded-card border px-4 py-3", toneClasses[tone])}>
      <p className="eyebrow-label">{title}</p>
      <p className="mt-1 text-sm leading-6 text-ink-2">{message}</p>
    </div>
  );
}