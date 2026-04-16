import type { PropsWithChildren } from "react";
import clsx from "clsx";

type ChipTone = "neutral" | "accent" | "success" | "warning" | "danger";

const toneClasses: Record<ChipTone, string> = {
  neutral: "bg-slate-100 text-slate-700",
  accent: "bg-accent-soft text-accent",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-rose-100 text-rose-700",
};

type ChipProps = PropsWithChildren<{
  tone?: ChipTone;
}>;

export function Chip({ tone = "neutral", children }: ChipProps) {
  return (
    <span className={clsx("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold", toneClasses[tone])}>
      {children}
    </span>
  );
}
