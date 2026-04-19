import type { PropsWithChildren } from "react";
import clsx from "clsx";

type ChipTone = "neutral" | "accent" | "success" | "warning" | "danger";

const toneClasses: Record<ChipTone, string> = {
  neutral: "border border-white/10 bg-neutral-soft/70 text-ink-2",
  accent: "border border-accent/25 bg-accent-soft/70 text-accent",
  success: "border border-success/25 bg-success-soft/70 text-success",
  warning: "border border-warning/25 bg-warning-soft/70 text-warning",
  danger: "border border-danger/25 bg-danger-soft/70 text-danger",
};

type ChipProps = PropsWithChildren<{
  tone?: ChipTone;
}>;

export function Chip({ tone = "neutral", children }: ChipProps) {
  return (
    <span className={clsx("inline-flex items-center rounded-pill px-3 py-1.5 text-[0.72rem] font-semibold uppercase tracking-[0.14em]", toneClasses[tone])}>
      {children}
    </span>
  );
}
