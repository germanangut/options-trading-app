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
    <section className={clsx("panel-shell panel-glow relative overflow-hidden p-5 sm:p-6", className)}>
      <div className="absolute inset-0 app-grid-glow opacity-15" aria-hidden="true" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" aria-hidden="true" />
      <div className="relative mb-5 flex flex-wrap items-start justify-between gap-4 border-b border-white/6 pb-4">
        <div className="space-y-1.5">
          {eyebrow ? <p className="eyebrow-label">{eyebrow}</p> : null}
          <h2 className="text-lg font-semibold tracking-tight text-ink-1 sm:text-xl">{title}</h2>
          {subtitle ? <p className="max-w-3xl text-sm leading-6 text-ink-3">{subtitle}</p> : null}
        </div>
        {actions}
      </div>
      <div className="relative">{children}</div>
    </section>
  );
}