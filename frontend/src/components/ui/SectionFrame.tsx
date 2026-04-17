import type { PropsWithChildren, ReactNode } from "react";
import clsx from "clsx";


type SectionFrameProps = PropsWithChildren<{
  eyebrow?: string;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}>;


export function SectionFrame({ eyebrow, title, subtitle, actions, className, children }: SectionFrameProps) {
  return (
    <section className={clsx("rounded-panel border border-slate-200 bg-white p-5 shadow-panel", className)}>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          {eyebrow ? <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-ink-3">{eyebrow}</p> : null}
          <h2 className="mt-1 text-lg font-semibold text-ink-1">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm text-ink-2">{subtitle}</p> : null}
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}