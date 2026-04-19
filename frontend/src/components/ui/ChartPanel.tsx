import type { ReactNode } from "react";
import clsx from "clsx";

type ChartPanelProps = {
  title: string;
  subtitle?: string;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function ChartPanel({ title, subtitle, footer, children, className }: ChartPanelProps) {
  return (
    <section className={clsx("panel-subtle p-4", className)}>
      <div className="mb-3 space-y-1">
        <p className="text-sm font-semibold text-ink-1">{title}</p>
        {subtitle ? <p className="text-xs leading-5 text-ink-4">{subtitle}</p> : null}
      </div>
      <div className="rounded-card border border-white/6 bg-surface-overlay/65 p-3">{children}</div>
      {footer ? <div className="mt-3 text-xs text-ink-4">{footer}</div> : null}
    </section>
  );
}