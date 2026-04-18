import { Link } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { Banner } from "../components/ui/Banner";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { SectionFrame } from "../components/ui/SectionFrame";
import { Chip } from "../components/ui/Chip";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectOverviewCockpitModel } from "../features/scans/selectors/decisionExperienceSelectors";
import { describeApiError } from "../lib/apiErrors";

export function OverviewPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading latest scan" message="Waiting for the backend to return the current ScanResult." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load latest scan">
        {describeApiError(latestScan.error, "load", "the latest scan").message}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No scan available yet"
        message="Run the first scan from the sidebar to populate the overview placeholders."
      />
    );
  }

  const overview = selectOverviewCockpitModel(latestScan.data);

  return (
    <div className="grid gap-6">
      <SectionFrame
        eyebrow="Decision Snapshot"
        title={overview.snapshot.title}
        subtitle={overview.snapshot.subtitle}
        actions={<Chip tone={overview.snapshot.directionTone}>{overview.snapshot.direction}</Chip>}
      >
        <MetricStrip items={overview.snapshot.metrics} columns={4} />
      </SectionFrame>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <SectionFrame
          eyebrow="Top Trade Preview"
          title={overview.topTradePreview?.title ?? "No top trade"}
          subtitle="Most actionable candidate under the current filters."
        >
          {overview.topTradePreview ? (
            <div className="space-y-4">
              <MetricStrip items={overview.topTradePreview.metrics} columns={3} compact />
              <div className="space-y-2 text-sm text-ink-2">
                <p>{overview.topTradePreview.summary}</p>
                {overview.topTradePreview.notes.map((note) => (
                  <p key={note}>{note}</p>
                ))}
              </div>
              <ActionRow>
                {overview.topTradePreview.href ? (
                  <Link to={overview.topTradePreview.href} className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">
                    Review trade
                  </Link>
                ) : null}
                <Link to="/qualified" className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-ink-2">
                  Open qualified board
                </Link>
              </ActionRow>
            </div>
          ) : (
            <EmptyState title="No top trade" message="The latest scan did not return a top-ranked opportunity." />
          )}
        </SectionFrame>

        <SectionFrame eyebrow="Scan Trust" title={overview.trust.title} subtitle="Coverage, provider, and execution cues.">
          <div className="space-y-4">
            <Banner tone={overview.trust.tone} title={overview.trust.title}>
              {overview.trust.message}
            </Banner>
            <MetricStrip
              items={overview.trust.metrics.map((metric) => ({ ...metric, tone: "neutral" as const }))}
              columns={3}
              compact
            />
            {overview.trust.notes.length > 0 ? (
              <div className="space-y-2 text-sm text-ink-2">
                {overview.trust.notes.map((note) => (
                  <p key={note}>{note}</p>
                ))}
              </div>
            ) : null}
          </div>
        </SectionFrame>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <SectionFrame eyebrow="Portfolio Posture" title={overview.portfolio.posture} subtitle="Current run interpretation from portfolio-facing summaries.">
          <div className="space-y-3 text-sm text-ink-2">
            {overview.portfolio.interpretation.length > 0 ? overview.portfolio.interpretation.map((line) => <p key={line}>{line}</p>) : <p>No portfolio interpretation was returned for this run.</p>}
            {overview.portfolio.keySignals.length > 0 ? (
              <div>
                <p className="mb-2 text-sm font-semibold text-ink-1">Key Signals</p>
                <ul className="grid gap-2">
                  {overview.portfolio.keySignals.slice(0, 3).map((signal) => (
                    <li key={signal} className="rounded-xl bg-surface-2 px-3 py-2">{signal}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            <p className="rounded-xl bg-surface-2 px-3 py-2">{overview.portfolio.concentration}</p>
            {overview.portfolio.cautions.length > 0 ? (
              <Banner tone="warning" title="Portfolio cautions">
                {overview.portfolio.cautions[0]}
              </Banner>
            ) : null}
          </div>
        </SectionFrame>

        <SectionFrame eyebrow="Historical Activity" title="Current context from stored runs" subtitle="Use recurring patterns as context, not prediction.">
          <div className="space-y-4">
            <MetricStrip
              items={[
                { label: "Runs Analyzed", value: overview.history.runsAnalyzed, tone: "neutral" },
                { label: "Signals Logged", value: overview.history.signalsAnalyzed, tone: "neutral" },
                { label: "Latest Run", value: overview.history.latestRun, tone: "accent" },
              ]}
              columns={3}
              compact
            />
            {overview.history.recurringPatterns.length > 0 ? (
              <div className="grid gap-2">
                {overview.history.recurringPatterns.map((pattern) => (
                  <div key={pattern.pattern} className="rounded-xl bg-surface-2 px-3 py-3 text-sm text-ink-2">
                    <p className="font-semibold text-ink-1">{pattern.pattern}</p>
                    <p className="mt-1">Count {pattern.count}</p>
                    <p>Avg Score {pattern.average_adjusted_score ?? "-"}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-ink-2">History context is still thin for recurring-pattern guidance.</p>
            )}
          </div>
        </SectionFrame>
      </section>

      <SectionFrame eyebrow="Workflow Guidance" title="What to review next" subtitle="Move from triage into confirmation without losing context.">
        <div className="grid gap-3 md:grid-cols-3">
          {overview.nextActions.map((action) => (
            <Link key={action.to} to={action.to} className="rounded-2xl border border-slate-200 bg-surface-0 px-4 py-4 text-sm text-ink-2 transition hover:bg-white">
              <p className="font-semibold text-ink-1">{action.label}</p>
              <p className="mt-1">Open the corresponding decision surface.</p>
            </Link>
          ))}
        </div>
      </SectionFrame>
    </div>
  );
}
