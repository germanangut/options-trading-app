import clsx from "clsx";
import { Card } from "./Card";

type MetricCardProps = {
  label: string;
  value: string | number;
  detail?: string | null;
  compact?: boolean;
  tone?: "neutral" | "accent" | "success" | "warning" | "danger";
};

const toneStyles = {
  neutral: "border-white/8 bg-surface-2/72",
  accent: "border-accent/25 bg-accent-soft/35",
  success: "border-success/25 bg-success-soft/35",
  warning: "border-warning/25 bg-warning-soft/35",
  danger: "border-danger/25 bg-danger-soft/35",
};

export function MetricCard({ label, value, detail, compact = false, tone = "neutral" }: MetricCardProps) {
  return (
    <Card className={clsx("border p-4 sm:p-5", toneStyles[tone], compact ? "" : "") }>
      <div className="space-y-1.5">
        <p className="eyebrow-label">{label}</p>
        <p className={compact ? "text-xl font-semibold tracking-tight text-ink-1" : "text-3xl font-semibold tracking-tight text-ink-1"}>
          {value}
        </p>
        {detail ? <p className="text-xs text-ink-4">{detail}</p> : null}
      </div>
    </Card>
  );
}
