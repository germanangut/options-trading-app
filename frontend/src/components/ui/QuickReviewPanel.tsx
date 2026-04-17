import type { PropsWithChildren, ReactNode } from "react";
import clsx from "clsx";


type QuickReviewPanelProps = PropsWithChildren<{
  title: string;
  summary?: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}>;


export function QuickReviewPanel({
  title,
  summary,
  defaultOpen = false,
  className,
  children,
}: QuickReviewPanelProps) {
  return (
    <details
      open={defaultOpen}
      className={clsx("rounded-2xl border border-slate-200 bg-surface-0 p-4", className)}
    >
      <summary className="flex cursor-pointer list-none items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink-1">{title}</p>
          {summary ? <div className="mt-1 text-sm text-ink-2">{summary}</div> : null}
        </div>
        <span className="rounded-full bg-white px-2.5 py-1 text-xs font-semibold text-ink-2">Expand</span>
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  );
}