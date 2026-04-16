import { Card } from "./Card";

type MetricCardProps = {
  label: string;
  value: string | number;
  compact?: boolean;
};

export function MetricCard({ label, value, compact = false }: MetricCardProps) {
  return (
    <Card className={compact ? "p-4" : undefined}>
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">{label}</p>
        <p className={compact ? "text-lg font-semibold text-ink-1" : "text-2xl font-semibold text-ink-1"}>
          {value}
        </p>
      </div>
    </Card>
  );
}
