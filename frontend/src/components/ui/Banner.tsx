import type { PropsWithChildren } from "react";
import clsx from "clsx";

type BannerTone = "info" | "success" | "warning" | "danger";

const toneStyles: Record<BannerTone, string> = {
  info: "border-accent/35 bg-accent-soft/60 text-ink-1",
  success: "border-success/30 bg-success-soft/60 text-ink-1",
  warning: "border-warning/35 bg-warning-soft/60 text-ink-1",
  danger: "border-danger/35 bg-danger-soft/60 text-ink-1",
};

type BannerProps = PropsWithChildren<{
  title: string;
  tone?: BannerTone;
}>;

export function Banner({ title, tone = "info", children }: BannerProps) {
  return (
    <div className={clsx("relative overflow-hidden rounded-card border px-4 py-3.5 shadow-elevated backdrop-blur", toneStyles[tone])}>
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" aria-hidden="true" />
      <p className="relative text-sm font-semibold tracking-wide">{title}</p>
      <div className="relative mt-1.5 text-sm leading-6 text-ink-2">{children}</div>
    </div>
  );
}
