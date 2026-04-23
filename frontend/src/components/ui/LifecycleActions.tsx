import clsx from "clsx";

/**
 * Lifecycle action buttons for the trade review workflow.
 *
 * Action semantics:
 *   Save         — keep for later review (low-commitment bookmark)
 *   Watch        — actively monitor this setup across scans
 *   Mark Ready   — approve as candidate for execution consideration
 *   Dismiss      — remove from active consideration (quiet, separated)
 *
 * The active state is highlighted so the operator knows what the trade is
 * currently set to without looking at the badge separately.
 * Dismiss is visually isolated on the trailing edge to reduce the chance of
 * an accidental tap.
 */

export type LifecycleTransitionState =
  | "saved"
  | "watching"
  | "execution_ready"
  | "dismissed";

type ActionDef = {
  state: LifecycleTransitionState;
  label: string;
  title: string;
};

const PRIMARY_ACTIONS: ActionDef[] = [
  { state: "saved", label: "Save", title: "Keep for later review" },
  { state: "watching", label: "Watch", title: "Actively monitor this setup" },
  {
    state: "execution_ready",
    label: "Mark Ready",
    title: "Approve for execution consideration",
  },
];

const DISMISS_ACTION: ActionDef = {
  state: "dismissed",
  label: "Dismiss",
  title: "Remove from active consideration",
};

type LifecycleActionsProps = {
  currentState?: string | null;
  onTransition: (state: LifecycleTransitionState) => void;
  isPending?: boolean;
  errorMessage?: string | null;
  /** sm = compact card footer; md = full section display */
  size?: "sm" | "md";
};

function buttonClass(
  action: ActionDef,
  currentState: string | null | undefined,
  isPending: boolean,
  size: "sm" | "md",
): string {
  const isActive = currentState === action.state;
  const padding = size === "sm" ? "px-3 py-1.5" : "px-4 py-2";
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  const base = clsx(
    "rounded-card font-semibold transition-opacity",
    padding,
    textSize,
    isActive && "cursor-default",
    isPending && !isActive && "opacity-50 pointer-events-none",
  );

  if (action.state === "execution_ready") {
    return clsx(
      base,
      isActive
        ? "border border-success/30 bg-success-soft/50 text-success"
        : "border border-accent/25 bg-accent text-surface-0",
    );
  }

  if (action.state === "dismissed") {
    return clsx(
      base,
      isActive
        ? "border border-danger/25 bg-danger-soft/40 text-danger"
        : "border border-white/8 bg-transparent text-ink-4",
    );
  }

  return clsx(
    base,
    isActive
      ? "border border-accent/20 bg-accent-soft/40 text-accent"
      : "border border-white/10 bg-surface-overlay/70 text-ink-2",
  );
}

export function LifecycleActions({
  currentState,
  onTransition,
  isPending = false,
  errorMessage,
  size = "md",
}: LifecycleActionsProps) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        {PRIMARY_ACTIONS.map((action) => (
          <button
            key={action.state}
            type="button"
            onClick={() => onTransition(action.state)}
            disabled={isPending || currentState === action.state}
            title={action.title}
            className={buttonClass(action, currentState, isPending, size)}
          >
            {action.label}
          </button>
        ))}

        {/* Spacer pushes Dismiss to the trailing edge */}
        <div className="flex-1" />

        <button
          type="button"
          onClick={() => onTransition(DISMISS_ACTION.state)}
          disabled={isPending || currentState === DISMISS_ACTION.state}
          title={DISMISS_ACTION.title}
          className={buttonClass(DISMISS_ACTION, currentState, isPending, size)}
        >
          {isPending ? "Saving…" : DISMISS_ACTION.label}
        </button>
      </div>

      {errorMessage ? (
        <p className="text-xs text-danger" role="alert">
          {errorMessage}
        </p>
      ) : null}
    </div>
  );
}
