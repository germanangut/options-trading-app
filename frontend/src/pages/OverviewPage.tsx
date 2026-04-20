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
    return <EmptyState title="Loading latest scan" message="Waiting for the latest run to open the decision cockpit." />;
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
        message="Run the first scan from the sidebar to open the overview briefing."
      />
    );
  }

  const overview = selectOverviewCockpitModel(latestScan.data);
  const topTradeScore = overview.topTradePreview?.metrics.find((metric) => metric.label === "Score")?.value ?? "-";
  const primarySnapshotMetrics = overview.snapshot.metrics.filter((metric) => metric.label === "Qualified" || metric.label === "Alerts");
  const secondarySnapshotMetrics = overview.snapshot.metrics.filter((metric) => metric.label !== "Qualified" && metric.label !== "Alerts");
  const trustMetrics = overview.trust.metrics.map((metric) => ({
    ...metric,
    tone: metric.label === "Missing" || metric.label === "Errors" ? "warning" as const : "neutral" as const,
  }));

  return (
    <PageShell
      eyebrow="Overview"
      title="Decision cockpit"
      description="See what happened in this run, what matters first, and where the next review should go."
      className="gap-4"
    >
      <section className="grid gap-3 lg:grid-cols-[minmax(0,1.14fr)_minmax(0,0.86fr)]">
        <SectionFrame eyebrow="What matters first" title={overview.topTradePreview?.title ?? overview.snapshot.title} subtitle="Start here, then confirm run trust and alert pressure before sizing anything." actions={<Chip tone={overview.snapshot.directionTone}>{overview.snapshot.direction}</Chip>}>
          {overview.topTradePreview ? (
            <div className="space-y-3.5">
              <ScoreRibbon score={topTradeScore} detail="Use the lead idea as the first review target only if scan trust and alert pressure still support it." size="sm" />
              <ChartPanel
                title="Why it leads now"
                subtitle="Read the lead setup in plain language before opening the full execution brief."
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
                    Open trade brief
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

        <div className="grid gap-3">
          <SectionFrame eyebrow="Run trust" title="Can this run be trusted?" subtitle="Coverage and execution cues that decide how hard to lean on the shortlist.">
            <div className="space-y-3">
              <WarningBand tone={overview.trust.tone} title={overview.trust.title}>
                {overview.trust.message}
              </WarningBand>
              <MetricStrip
                items={trustMetrics}
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

          <SectionFrame eyebrow="Alert pressure" title={overview.alertsSnapshot.title} subtitle="Decide whether the ranked board is enough or whether this run needs a wider sweep.">
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
        eyebrow="Run summary"
        title="What the run is telling you"
        subtitle="Read the lead result, the pressure around it, and the implication before you branch into other pages."
        actions={<Chip tone={overview.snapshot.directionTone}>{overview.snapshot.direction}</Chip>}
      >
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1.02fr)_minmax(0,0.98fr)]">
          <div className="space-y-2.5">
            <MetricStrip items={primarySnapshotMetrics} columns={2} />
            <MetricStrip items={secondarySnapshotMetrics} columns={2} compact />
          </div>
          <div className="space-y-4">
            {overview.snapshot.story.map((line) => (
              <div key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-4 py-3 text-sm leading-6 text-ink-2">
                {line}
              </div>
            ))}
          </div>
        </div>
      </SectionFrame>

      <section className="grid gap-3 lg:grid-cols-2">
        <SectionFrame eyebrow="Portfolio posture" title={overview.portfolio.posture} subtitle="What the current book is telling you about this run before you size anything.">
          <div className="space-y-3 text-sm text-ink-2">
            <PortfolioImpactBand title="Portfolio read" message={overview.portfolio.summaryLine} tone="neutral" />
            {overview.portfolio.interpretation.length > 0 ? overview.portfolio.interpretation.map((line) => <p key={line}>{line}</p>) : <p>No portfolio interpretation was returned for this run.</p>}
            {overview.portfolio.keySignals.length > 0 ? (
              <div>
                <p className="mb-2 text-sm font-semibold text-ink-1">What supports the posture</p>
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

        <SectionFrame eyebrow="History context" title="What recent history reinforces" subtitle="Use recurring context to decide how much confidence this board deserves today.">
          <div className="space-y-4">
            <MetricStrip
              items={[
                { label: "Runs Analyzed", value: overview.history.runsAnalyzed, tone: "accent" },
                { label: "Signals Logged", value: overview.history.signalsAnalyzed, tone: "neutral" },
                { label: "Latest Run", value: overview.history.latestRun, tone: "neutral" },
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

      <SectionFrame eyebrow="Workflow guidance" title="Next review steps" subtitle="Move from triage into confirmation without losing the run story.">
        <div className="grid gap-3 md:grid-cols-3">
          {overview.nextActions.map((action) => (
            <Link key={action.to} to={action.to} className="panel-subtle interactive-border px-4 py-4 text-sm text-ink-2 transition">
              <p className="font-semibold text-ink-1">{action.label}</p>
              <p className="mt-1">Carry the current run context into the next decision surface.</p>
            </Link>
          ))}
        </div>
      </SectionFrame>
    </PageShell>
  );
}
