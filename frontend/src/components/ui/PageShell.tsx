import type { PropsWithChildren, ReactNode } from "react";
import clsx from "clsx";

type PageShellProps = PropsWithChildren<{
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function PageShell({ eyebrow, title, description, actions, className, children }: PageShellProps) {
  return (
    <div className={clsx("grid gap-5", className)}>
      <section className="relative overflow-hidden rounded-panel border border-white/10 bg-surface-1/86 px-5 py-5 shadow-panel backdrop-blur sm:px-6 sm:py-6">
        <div className="absolute inset-0 app-grid-glow opacity-25" aria-hidden="true" />
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" aria-hidden="true" />
        <div className="relative flex flex-wrap items-start justify-between gap-3">
          <div className="max-w-2xl space-y-1.5">
            {eyebrow ? <p className="eyebrow-label">{eyebrow}</p> : null}
            <h1 className="text-2xl font-semibold tracking-tight text-ink-1 sm:text-3xl">{title}</h1>
            {description ? <p className="text-sm leading-6 text-ink-3 sm:text-[0.95rem]">{description}</p> : null}
          </div>
          {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
        </div>
      </section>
      {children}
    </div>
  );
}