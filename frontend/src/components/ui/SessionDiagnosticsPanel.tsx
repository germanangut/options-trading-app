import clsx from "clsx";

type SessionDiagnosticsPanelProps = {
  isOpen: boolean;
  onClose: () => void;
  model: {
    sections: Array<{
      title: string;
      tone: "success" | "info" | "warning" | "danger";
      message: string;
      notes: string[];
    }>;
  } | null;
};

const sectionToneClasses: Record<"success" | "info" | "warning" | "danger", string> = {
  success: "border-success/25 bg-success-soft/35",
  info: "border-accent/25 bg-accent-soft/35",
  warning: "border-warning/25 bg-warning-soft/35",
  danger: "border-danger/25 bg-danger-soft/35",
};

export function SessionDiagnosticsPanel({ isOpen, onClose, model }: SessionDiagnosticsPanelProps) {
  if (!model || !isOpen) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        aria-label="Close diagnostics"
        className="fixed inset-0 z-30 bg-surface-0/55 backdrop-blur-sm"
        onClick={onClose}
      />
      <aside
        aria-label="Session diagnostics"
        className={clsx("fixed inset-y-0 right-0 z-40 flex w-full max-w-md flex-col border-l border-white/10 bg-surface-1/96 shadow-panel transition-transform duration-200")}
        data-testid="session-diagnostics-panel"
      >
        <div className="border-b border-white/8 px-5 py-4">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <p className="eyebrow-label">Current Session</p>
              <h2 className="text-lg font-semibold tracking-tight text-ink-1">Diagnostics</h2>
              <p className="text-sm leading-6 text-ink-3">
                Operational metadata for the latest run. Decision content stays in the main workspace.
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-pill border border-white/10 bg-surface-overlay/70 px-3 py-1.5 text-xs font-semibold text-ink-2 transition hover:border-white/20 hover:bg-surface-2"
            >
              Close
            </button>
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-3">
            {model.sections.map((section) => (
              <section
                key={section.title}
                className={clsx(
                  "rounded-card border p-4",
                  sectionToneClasses[section.tone],
                )}
              >
                <div className="space-y-2">
                  <div>
                    <p className="text-sm font-semibold tracking-tight text-ink-1">{section.title}</p>
                    <p className="mt-1 text-sm leading-6 text-ink-2">{section.message}</p>
                  </div>
                  {section.notes.length > 0 ? (
                    <ul className="grid gap-2 text-sm text-ink-2">
                      {section.notes.map((note) => (
                        <li key={note} className="rounded-card border border-white/8 bg-surface-overlay/55 px-3 py-2">
                          {note}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              </section>
            ))}
          </div>
        </div>
      </aside>
    </>
  );
}