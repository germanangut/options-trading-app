import clsx from "clsx";

/**
 * Visual badge for trade lifecycle state.
 *
 * Each state gets a distinct dot color and chip treatment so the operator
 * can identify review status at a glance without reading the full label.
 *
 * States: new (neutral) | saved (accent) | watching (warning/amber) |
 *         execution_ready (success/green) | dismissed (danger/muted) |
 *         paper_* (deferred phase states, shown with neutral styles)
 */

type LifecycleBadgeProps = {
  state?: string | null;
  /** sm = compact in-card use; md = default section display */
  size?: "sm" | "md";
};

type StateConfig = {
  label: string;
  dot: string;
  chip: string;
};

const STATE_CONFIG: Record<string, StateConfig> = {
  new: {
    label: "New",
    dot: "bg-ink-4",
    chip: "border border-white/10 bg-surface-overlay/50 text-ink-3",
  },
  saved: {
    label: "Saved",
    dot: "bg-accent",
    chip: "border border-accent/25 bg-accent-soft/40 text-accent",
  },
  watching: {
    label: "Watching",
    dot: "bg-warning",
    chip: "border border-warning/25 bg-warning-soft/40 text-warning",
  },
  execution_ready: {
    label: "Ready",
    dot: "bg-success",
    chip: "border border-success/25 bg-success-soft/40 text-success",
  },
  dismissed: {
    label: "Dismissed",
    dot: "bg-danger",
    chip: "border border-danger/20 bg-danger-soft/30 text-danger",
  },
  paper_submitted: {
    label: "Submitted",
    dot: "bg-accent",
    chip: "border border-accent/25 bg-accent-soft/40 text-accent",
  },
  paper_filled: {
    label: "Filled",
    dot: "bg-success",
    chip: "border border-success/25 bg-success-soft/40 text-success",
  },
  paper_closed: {
    label: "Closed",
    dot: "bg-ink-3",
    chip: "border border-white/10 bg-surface-overlay/50 text-ink-3",
  },
};

export function LifecycleBadge({ state, size = "md" }: LifecycleBadgeProps) {
  const config = STATE_CONFIG[state ?? "new"] ?? STATE_CONFIG.new;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-pill font-semibold uppercase tracking-[0.12em]",
        size === "sm" ? "px-2 py-1 text-[0.65rem]" : "px-3 py-1.5 text-[0.72rem]",
        config.chip,
      )}
    >
      <span className={clsx("h-1.5 w-1.5 flex-none rounded-full", config.dot)} aria-hidden="true" />
      {config.label}
    </span>
  );
}
