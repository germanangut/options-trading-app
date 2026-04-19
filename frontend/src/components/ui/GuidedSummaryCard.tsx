type GuidedSummaryCardProps = {
  title: string;
  lines: string[];
  helper?: string;
};

export function GuidedSummaryCard({ title, lines, helper }: GuidedSummaryCardProps) {
  return (
    <section className="panel-subtle relative overflow-hidden p-4 sm:p-5">
      <div className="absolute inset-0 app-grid-glow opacity-15" aria-hidden="true" />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" aria-hidden="true" />
      <div className="relative">
        <p className="eyebrow-label">Live Interpretation</p>
        <h3 className="mt-2 text-base font-semibold tracking-tight text-ink-1">{title}</h3>
        <div className="mt-4 grid gap-2">
          {lines.map((line, index) => (
            <div key={line} className={index === 0 ? "rounded-card border border-accent/20 bg-accent-soft/35 px-3 py-3 text-sm leading-6 text-ink-1" : "rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2.5 text-sm leading-6 text-ink-2"}>
            {line}
          </div>
          ))}
        </div>
        {helper ? <p className="mt-3 text-xs leading-5 text-ink-4">{helper}</p> : null}
      </div>
    </section>
  );
}