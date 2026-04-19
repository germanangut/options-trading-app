import type { ReactNode } from "react";
import clsx from "clsx";

type GuidedQuestionCardProps = {
  step: string;
  title: string;
  description: string;
  helper?: string;
  children: ReactNode;
  className?: string;
};

export function GuidedQuestionCard({ step, title, description, helper, children, className }: GuidedQuestionCardProps) {
  return (
    <section className={clsx("panel-subtle relative overflow-hidden p-4 sm:p-5", className)}>
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" aria-hidden="true" />
      <div className="mb-4 space-y-1.5">
        <p className="eyebrow-label">{step}</p>
        <h3 className="text-base font-semibold tracking-tight text-ink-1">{title}</h3>
        <p className="text-sm leading-6 text-ink-3">{description}</p>
        {helper ? <p className="text-xs leading-5 text-ink-4">{helper}</p> : null}
      </div>
      {children}
    </section>
  );
}