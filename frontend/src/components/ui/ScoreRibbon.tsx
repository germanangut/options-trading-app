import clsx from "clsx";

type ScoreRibbonTone = "accent" | "success" | "warning";

type ScoreRibbonProps = {
  score: string | number;
  detail?: string | null;
  label?: string;
  tone?: ScoreRibbonTone;
  size?: "sm" | "md";
};

const toneClasses: Record<ScoreRibbonTone, string> = {
  accent: "border-accent/25 bg-accent-soft/45 text-accent",
  success: "border-success/25 bg-success-soft/45 text-success",
  warning: "border-warning/25 bg-warning-soft/45 text-warning",
};

function parseScore(score: string | number) {
  const numeric = Number(String(score).replace(/[^0-9.-]/g, ""));
  if (Number.isNaN(numeric)) {
    return null;
  }

  return Math.max(0, Math.min(100, numeric));
}

export function ScoreRibbon({
  score,
  detail,
  label = "Decision Quality",
  tone = "accent",
  size = "md",
}: ScoreRibbonProps) {
  const parsedScore = parseScore(score);
  const fillWidth = parsedScore === null ? 18 : Math.max(12, parsedScore);

  return (
    <div className={clsx("rounded-card border p-4 shadow-elevated", toneClasses[tone])}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="eyebrow-label text-current/80">{label}</p>
          <p className={clsx("mt-2 font-semibold tracking-tight text-ink-1", size === "sm" ? "text-2xl" : "text-3xl")}>
            {score}
          </p>
        </div>
        <div className="min-w-0 flex-1 pt-1">
          <div className="overflow-hidden rounded-pill border border-white/10 bg-surface-1/60 p-1">
            <div className="h-2 rounded-pill bg-gradient-to-r from-accent via-white/15 to-success" style={{ width: `${fillWidth}%` }} />
          </div>
          <p className="mt-2 text-xs leading-5 text-ink-3">
            {detail ?? (parsedScore === null ? "Score detail unavailable." : parsedScore >= 75 ? "High-conviction quality signal." : parsedScore >= 60 ? "Clear but selective setup quality." : "Borderline quality; read the context before acting." )}
          </p>
        </div>
      </div>
    </div>
  );
}