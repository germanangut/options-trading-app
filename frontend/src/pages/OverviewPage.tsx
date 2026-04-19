import { Link } from "react-router-dom";

import { ActionRow } from "../components/ui/ActionRow";
import { ChartPanel } from "../components/ui/ChartPanel";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { ScoreRibbon } from "../components/ui/ScoreRibbon";
import { SectionFrame } from "../components/ui/SectionFrame";
import { Chip } from "../components/ui/Chip";
import { WarningBand } from "../components/ui/WarningBand";
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
      <WarningBand tone="danger" title="Unable to load latest scan">
        {describeApiError(latestScan.error, "load", "the latest scan").message}
      </WarningBand>
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
  const topTradeScore = overview.topTradePreview?.metrics.find((metric) => metric.label === "Score")?.value ?? "-";

  return (
    <PageShell
      eyebrow="Overview"
      title="Decision cockpit"
      description="A run command center that tells you what happened, what matters most, and where to review next."
    >
      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.14fr)_minmax(0,0.86fr)]">
        <SectionFrame eyebrow="Run Priority" title={overview.topTradePreview?.title ?? overview.snapshot.title} subtitle="What deserves your attention first in the latest run." actions={<Chip tone={overview.snapshot.directionTone}>{overview.snapshot.direction}</Chip>}>
          {overview.topTradePreview ? (
            <div className="space-y-4">
              <ScoreRibbon score={topTradeScore} detail="Use the lead idea as the first review target only if scan trust and alert pressure still look healthy." size="sm" />
              <ChartPanel
                title="Decision story"
                subtitle="The cockpit keeps the top candidate in narrative form before you drill into the dedicated detail page."
                footer={overview.topTradePreview.notes[0] ?? "No additional top-trade note was returned."}
              >
                <div className="space-y-3">
                  <p className="text-sm leading-6 text-ink-2">{overview.topTradePreview.summary}</p>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {overview.topTradePreview.notes.map((note) => (
                      <div key={note} className="rounded-card border border-white/8 bg-surface-2/70 px-3 py-2 text-sm text-ink-2">
                        {note}
                      </div>
                    ))}
                  </div>
                </div>
              </ChartPanel>
              <ActionRow>
                {overview.topTradePreview.href ? (
                  <Link to={overview.topTradePreview.href} className="rounded-card border border-accent/25 bg-accent px-4 py-2.5 text-sm font-semibold text-surface-0">
                    Review trade
                  </Link>
                ) : null}
                <Link to="/qualified" className="rounded-card border border-white/10 bg-surface-overlay/70 px-4 py-2.5 text-sm font-semibold text-ink-2">
                  Open qualified board
                </Link>
              </ActionRow>
            </div>
          ) : (
            <EmptyState title="No top trade" message="The latest scan did not return a top-ranked opportunity." />
          )}
        </SectionFrame>

        <div className="grid gap-4">
          <SectionFrame eyebrow="Scan Trust" title={overview.trust.title} subtitle="Coverage, provider, and execution cues.">
            <div className="space-y-4">
              <WarningBand tone={overview.trust.tone} title={overview.trust.title}>
                {overview.trust.message}
              </WarningBand>
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

          <SectionFrame eyebrow="Alert Pressure" title={overview.alertsSnapshot.title} subtitle="Decide whether the ranked board is enough or whether this run needs wider review.">
            <div className="grid gap-3 md:grid-cols-[auto_minmax(0,1fr)]">
              <div className="rounded-card border border-accent/20 bg-accent-soft/28 px-5 py-4 text-center">
                <p className="eyebrow-label">Alerts</p>
                <p className="mt-1 text-3xl font-semibold tracking-tight text-ink-1">{overview.alertsSnapshot.total}</p>
              </div>
              <div className="grid gap-2">
                {overview.alertsSnapshot.notes.map((note) => (
                  <div key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm leading-6 text-ink-2">
                    {note}
                  </div>
                ))}
              </div>
            </div>
          </SectionFrame>
        </div>
      </section>

      <SectionFrame
        eyebrow="Decision Snapshot"
        title={overview.snapshot.title}
        subtitle={overview.snapshot.subtitle}
        actions={<Chip tone={overview.snapshot.directionTone}>{overview.snapshot.direction}</Chip>}
      >
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.02fr)_minmax(0,0.98fr)]">
          <MetricStrip items={overview.snapshot.metrics} columns={4} />
          <div className="space-y-4">
            {overview.snapshot.story.map((line) => (
              <div key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm leading-6 text-ink-2">
                {line}
              </div>
            ))}
          </div>
        </div>
      </SectionFrame>

      <section className="grid gap-4 lg:grid-cols-2">
        <SectionFrame eyebrow="Portfolio Posture" title={overview.portfolio.posture} subtitle="Current run interpretation from portfolio-facing summaries.">
          <div className="space-y-3 text-sm text-ink-2">
            <PortfolioImpactBand title="Portfolio read" message={overview.portfolio.summaryLine} tone="neutral" />
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
              <WarningBand title="Portfolio cautions">
                {overview.portfolio.cautions[0]}
              </WarningBand>
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
            <div className="grid gap-2">
              {overview.history.notes.map((note) => (
                <div key={note} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3 text-sm text-ink-2">
                  {note}
                </div>
              ))}
            </div>
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
            <Link key={action.to} to={action.to} className="panel-subtle interactive-border px-4 py-4 text-sm text-ink-2 transition">
              <p className="font-semibold text-ink-1">{action.label}</p>
              <p className="mt-1">Open the corresponding decision surface.</p>
            </Link>
          ))}
        </div>
      </SectionFrame>
    </PageShell>
  );
}
