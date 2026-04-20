import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { MetricStrip } from "../components/ui/MetricStrip";
import { PageShell } from "../components/ui/PageShell";
import { PortfolioImpactBand } from "../components/ui/PortfolioImpactBand";
import { WarningBand } from "../components/ui/WarningBand";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectHistoryModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";

export function HistoryPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading history" message="Waiting for history context from the latest scan." />;
  }

  if (latestScan.isError) {
    return (
      <WarningBand tone="danger" title="Unable to load history">
        {describeApiError(latestScan.error, "load", "history").message}
      </WarningBand>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No history available yet" message="Run a scan first to populate history context." />;
  }

  const history = selectHistoryModel(latestScan.data);
  const runsAnalyzed = history.summaryCards.find((card) => card.label === "Runs Analyzed")?.value ?? 0;
  const historyAvailable = history.summaryCards.find((card) => card.label === "History Available")?.value ?? "No";
  const historySummary = history.recentPatterns[0]
    ? `${history.recentPatterns[0].pattern} is repeating often enough to add familiarity to the current board.`
    : history.topTickers[0]
      ? `${history.topTickers[0].ticker ?? "This ticker"} has shown up repeatedly enough to be useful context for today's board.`
      : "History is still light, so today's board should be judged mostly on the current run.";
  return (
    <PageShell eyebrow="History" title="Historical context" description="Use recurring patterns as confidence context for the current board, not as a report to read in isolation." className="gap-4">
      <Card eyebrow="Decision context" title="What history adds to today's board" subtitle="Look for familiarity and repetition that help you judge confidence in the current shortlist.">
        <div className="space-y-3">
          <MetricStrip
            items={history.summaryCards.map((card) => ({
              ...card,
              tone: card.label === "Runs Analyzed" ? "accent" as const : card.label === "History Available" && card.value === "Yes" ? "success" as const : "neutral" as const,
            }))}
            columns={4}
            compact
          />
          <PortfolioImpactBand
            title="History read"
            message={historySummary}
            tone={historyAvailable === "Yes" && Number(runsAnalyzed) > 0 ? "accent" : "neutral"}
          />
        </div>
      </Card>

      <section className="grid gap-3 lg:grid-cols-2">
        <Card eyebrow="Recurring quality" title="Patterns worth carrying forward" subtitle="These repeat setups add familiarity to the current board and help frame confidence.">
          {history.recentPatterns.length > 0 ? (
            <div className="grid gap-3">
              {history.recentPatterns.map((pattern) => (
                <div key={pattern.pattern} className="rounded-card border border-white/8 bg-surface-overlay/60 p-4 text-sm text-ink-2">
                  <p className="font-semibold text-ink-1">{pattern.pattern}</p>
                  <p className="mt-1">Count: {pattern.count}</p>
                  <p>Avg Score: {pattern.average_adjusted_score ?? "-"}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No recurring patterns" message="The latest history context did not include recurring trade patterns." />
          )}
        </Card>

        <Card eyebrow="Frequency leaders" title="What tends to repeat" subtitle="Use repeating names and structures as context for review priority, not as a replacement for current-run evidence.">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-3 text-sm font-semibold text-ink-1">Tickers showing up repeatedly</p>
              {history.topTickers.length > 0 ? (
                <ul className="grid gap-2 text-sm text-ink-2">
                  {history.topTickers.map((row, index) => (
                    <li key={`${row.ticker}-${index}`} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                      {row.ticker ?? "Unknown"} - {row.count}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No ticker history" message="No ticker frequency data was included." />
              )}
            </div>
            <div>
              <p className="mb-3 text-sm font-semibold text-ink-1">Structures showing up repeatedly</p>
              {history.topStrategies.length > 0 ? (
                <ul className="grid gap-2 text-sm text-ink-2">
                  {history.topStrategies.map((row, index) => (
                    <li key={`${row.strategy}-${index}`} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-2">
                      {row.strategy ?? "Unknown"} - {row.count}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState title="No strategy history" message="No strategy frequency data was included." />
              )}
            </div>
          </div>
          <PortfolioImpactBand title="How to use this" message="Let repeat names and structures raise or lower confidence, but keep the current board and trade brief as the main decision surfaces." tone="neutral" />
        </Card>
      </section>
    </PageShell>
  );
}
