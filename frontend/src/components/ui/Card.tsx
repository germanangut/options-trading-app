import type { PropsWithChildren, ReactNode } from "react";
import clsx from "clsx";

type CardProps = PropsWithChildren<{
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function Card({ title, subtitle, actions, className, children }: CardProps) {
  return (
    <section className={clsx("rounded-panel border border-slate-200 bg-white p-5 shadow-panel", className)}>
      {(title || subtitle || actions) ? (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            {title ? <h3 className="text-base font-semibold text-ink-1">{title}</h3> : null}
            {subtitle ? <p className="mt-1 text-sm text-ink-2">{subtitle}</p> : null}
          </div>
          {actions}
        </div>
      ) : null}
      {children}
    </section>
  );
}
