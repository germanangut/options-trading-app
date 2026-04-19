import clsx from "clsx";

type ScoreBadgeProps = {
  score: string | number;
  detail?: string | null;
  size?: "sm" | "md";
};

export function ScoreBadge({ score, detail, size = "md" }: ScoreBadgeProps) {
  return (
    <div
      className={clsx(
        "rounded-card border border-accent/25 bg-accent-soft/50 text-accent shadow-elevated",
        size === "sm" ? "px-3 py-2" : "px-4 py-3",
      )}
    >
      <p className="eyebrow-label text-accent/70">Adjusted Score</p>
      <p className={clsx("font-semibold tracking-tight", size === "sm" ? "text-xl" : "text-3xl")}>{score}</p>
      {detail ? <p className="mt-1 text-xs text-ink-4">{detail}</p> : null}
    </div>
  );
}