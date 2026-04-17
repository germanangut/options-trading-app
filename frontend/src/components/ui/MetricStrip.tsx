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
  neutral: "border-slate-200 bg-white",
  accent: "border-teal-200 bg-teal-50/80",
  success: "border-emerald-200 bg-emerald-50/80",
  warning: "border-amber-200 bg-amber-50/80",
  danger: "border-rose-200 bg-rose-50/80",
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
            "rounded-2xl border px-4 py-3",
            toneClasses[item.tone ?? "neutral"],
            compact ? "min-h-[4.5rem]" : "min-h-[5.25rem]",
          )}
        >
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-ink-3">{item.label}</p>
          <p className={clsx("mt-1 font-semibold text-ink-1", compact ? "text-lg" : "text-2xl")}>{item.value}</p>
          {item.detail ? <p className="mt-1 text-xs text-ink-2">{item.detail}</p> : null}
        </div>
      ))}
    </div>
  );
}