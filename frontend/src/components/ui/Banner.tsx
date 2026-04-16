import type { PropsWithChildren } from "react";
import clsx from "clsx";

type BannerTone = "info" | "success" | "warning" | "danger";

const toneStyles: Record<BannerTone, string> = {
  info: "border-sky-200 bg-sky-50 text-sky-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  danger: "border-rose-200 bg-rose-50 text-rose-900",
};

type BannerProps = PropsWithChildren<{
  title: string;
  tone?: BannerTone;
}>;

export function Banner({ title, tone = "info", children }: BannerProps) {
  return (
    <div className={clsx("rounded-panel border px-4 py-3", toneStyles[tone])}>
      <p className="text-sm font-semibold">{title}</p>
      <div className="mt-1 text-sm opacity-90">{children}</div>
    </div>
  );
}
