import clsx from "clsx";

type EmptyStateProps = {
  title: string;
  message: string;
  tone?: "neutral" | "warning" | "danger";
};

const toneClasses = {
  neutral: "border-white/10 bg-surface-2/65",
  warning: "border-warning/30 bg-warning-soft/55",
  danger: "border-danger/30 bg-danger-soft/55",
};

export function EmptyState({ title, message, tone = "neutral" }: EmptyStateProps) {
  return (
    <div className={clsx("relative overflow-hidden rounded-panel border border-dashed px-6 py-10 text-center shadow-elevated", toneClasses[tone])}>
      <div className="absolute inset-0 app-grid-glow opacity-15" aria-hidden="true" />
      <div className="mx-auto max-w-2xl">
        <p className="eyebrow-label">Decision Support</p>
        <h3 className="mt-2 text-lg font-semibold tracking-tight text-ink-1">{title}</h3>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-ink-3">{message}</p>
      </div>
    </div>
  );
}
