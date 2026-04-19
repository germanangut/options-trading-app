import clsx from "clsx";


type MetricTone = "neutral" | "accent" | "success" | "warning" | "danger";

type MetricStripItem = {
  label: string;
  value: string | number;
  detail?: string | null;
  tone?: MetricTone;
};

type MetricStripProps = {
  items: MetricStripItem[];
  columns?: number;
  compact?: boolean;
};


const toneClasses: Record<MetricTone, string> = {
  neutral: "border-white/8 bg-surface-2/72",
  accent: "border-accent/25 bg-accent-soft/35",
  success: "border-success/25 bg-success-soft/35",
  warning: "border-warning/25 bg-warning-soft/35",
  danger: "border-danger/25 bg-danger-soft/35",
};


export function MetricStrip({ items, columns, compact = false }: MetricStripProps) {
  const visibleItems = items.filter((item) => item.value !== undefined && item.value !== null && item.value !== "");
  const fallbackColumns = visibleItems.length || 1;
  const resolvedColumns = Math.max(1, Math.min(columns ?? fallbackColumns, 4));

  return (
    <div
      className="grid gap-3"
      style={{ gridTemplateColumns: `repeat(${resolvedColumns}, minmax(0, 1fr))` }}
    >
      {visibleItems.map((item) => (
        <div
          key={`${item.label}-${item.value}`}
          className={clsx(
            "rounded-card relative overflow-hidden border px-4 py-3.5 shadow-elevated",
            toneClasses[item.tone ?? "neutral"],
            compact ? "min-h-[4.5rem]" : "min-h-[5.25rem]",
          )}
        >
          <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/15 to-transparent" aria-hidden="true" />
          <p className="eyebrow-label">{item.label}</p>
          <p className={clsx("mt-1 font-semibold tracking-tight text-ink-1", compact ? "text-xl" : "text-3xl")}>{item.value}</p>
          {item.detail ? <p className="mt-1 text-xs text-ink-4">{item.detail}</p> : null}
        </div>
      ))}
    </div>
  );
}