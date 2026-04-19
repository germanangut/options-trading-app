import { NavLink } from "react-router-dom";

import { ActionRow } from "../../components/ui/ActionRow";
import { Banner } from "../../components/ui/Banner";
import { Chip } from "../../components/ui/Chip";
import { EmptyState } from "../../components/ui/EmptyState";
import { GuidedQuestionCard } from "../../components/ui/GuidedQuestionCard";
import { GuidedSummaryCard } from "../../components/ui/GuidedSummaryCard";
import { MetricStrip } from "../../components/ui/MetricStrip";
import { SectionFrame } from "../../components/ui/SectionFrame";
import { WarningBand } from "../../components/ui/WarningBand";
import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanControls } from "../../features/scans/hooks/useScanControls";
import { useRunScan } from "../../features/scans/hooks/useRunScan";
import { selectSidebarWorkflowModel } from "../../features/scans/selectors/decisionExperienceSelectors";
import {
  NAV_ITEMS,
  PROFILE_OPTIONS,
  STRATEGY_OPTIONS,
  TICKER_GROUP_OPTIONS,
} from "../../lib/constants";
import { describeApiError } from "../../lib/apiErrors";
import { formatDuration } from "../../lib/formatters";

function linkClassName(isActive: boolean) {
  return [
    "flex items-center justify-between rounded-card border px-3 py-2.5 text-sm font-medium transition-colors",
    isActive
      ? "border-accent/25 bg-accent-soft/65 text-accent"
      : "border-white/5 bg-surface-2/40 text-ink-2 hover:border-white/15 hover:bg-surface-2 hover:text-ink-1",
  ].join(" ");
}

const fieldClassName = "rounded-card border border-white/10 bg-surface-overlay/70 px-3 py-2.5 text-sm text-ink-1 outline-none transition focus:border-accent/35";

const toggleButtonClassName = (active: boolean) => [
  "rounded-card border px-3 py-2.5 text-sm font-semibold transition-colors",
  active
    ? "border-accent/30 bg-accent-soft/70 text-accent"
    : "border-white/8 bg-surface-2/70 text-ink-3 hover:border-white/14 hover:text-ink-1",
].join(" ");

const guidedChoiceButtonClassName = (active: boolean) => [
  "rounded-card border px-3 py-3 text-left text-sm transition-colors",
  active
    ? "border-accent/30 bg-accent-soft/70 text-ink-1 shadow-elevated"
    : "border-white/8 bg-surface-overlay/55 text-ink-2 hover:border-white/15 hover:bg-surface-overlay/75",
].join(" ");

export function Sidebar() {
  const latestScan = useLatestScan();
  const runScan = useRunScan();
  const controls = useScanControls(latestScan.data);
  const workflow = selectSidebarWorkflowModel(latestScan.data, controls.request, controls.mode, runScan.isPending);

  const disableRun = runScan.isPending || controls.request.selected_strategy_keys.length === 0;
  const directionSelection = controls.request.selected_strategy_keys.includes("bull_put_spread") && controls.request.selected_strategy_keys.includes("bear_call_spread")
    ? "either"
    : controls.request.selected_strategy_keys.includes("bull_put_spread")
      ? "bullish"
      : controls.request.selected_strategy_keys.includes("bear_call_spread")
        ? "bearish"
        : "either";
  const timeframeSelection = controls.request.dte_max <= 14
    ? "soon"
    : controls.request.dte_min >= 35
      ? "later"
      : "balanced";
  const strictnessSelection = controls.request.min_score >= 75
    ? "strict"
    : controls.request.min_score <= 55
      ? "broad"
      : "moderate";
  const familiaritySelection = controls.request.min_consistency >= 5
    ? "repeat"
    : controls.request.min_consistency <= 1
      ? "fresh"
      : "balanced";

  function applyDirectionSelection(direction: "bullish" | "bearish" | "either") {
    if (direction === "bullish") {
      controls.updateField("selected_strategy_keys", ["bull_put_spread"]);
      return;
    }

    if (direction === "bearish") {
      controls.updateField("selected_strategy_keys", ["bear_call_spread"]);
      return;
    }

    controls.updateField("selected_strategy_keys", STRATEGY_OPTIONS.map((strategy) => strategy.value));
  }

  function applyTimeframeSelection(timeframe: "soon" | "balanced" | "later") {
    if (timeframe === "soon") {
      controls.updateField("dte_min", 7);
      controls.updateField("dte_max", 14);
      return;
    }

    if (timeframe === "later") {
      controls.updateField("dte_min", 35);
      controls.updateField("dte_max", 56);
      return;
    }

    controls.updateField("dte_min", 20);
    controls.updateField("dte_max", 35);
  }

  function applyStrictnessSelection(strictness: "broad" | "moderate" | "strict") {
    controls.updateField("min_score", strictness === "broad" ? 55 : strictness === "strict" ? 75 : 65);
  }

  function applyFamiliaritySelection(choice: "fresh" | "balanced" | "repeat") {
    controls.updateField("min_consistency", choice === "fresh" ? 1 : choice === "repeat" ? 5 : 3);
  }

  return (
    <aside className="border-b border-white/8 bg-surface-1/92 lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col gap-5 p-4 sm:p-5 lg:gap-6">
        <div className="space-y-3">
          <p className="eyebrow-label">
            Options Platform
          </p>
          <div className="space-y-1.5">
            <h1 className="text-xl font-semibold tracking-tight text-ink-1">Decision Workflow</h1>
            <p className="text-sm leading-6 text-ink-3">
              Premium operator surface over the same backend scan contract and ranking truth.
            </p>
          </div>
        </div>

        <Banner tone={workflow.readiness.tone} title={workflow.readiness.title}>
          {workflow.readiness.message}
        </Banner>

        <nav className="grid gap-2">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClassName(isActive)}>
              <span>{item.label}</span>
              <span className="text-xs text-ink-4">{item.shortcut}</span>
            </NavLink>
          ))}
        </nav>

        <SectionFrame
          eyebrow={workflow.modeFrame.eyebrow}
          title={workflow.modeFrame.title}
          subtitle={workflow.modeFrame.description}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => controls.setMode("guided")}
                className={toggleButtonClassName(controls.mode === "guided")}
                data-testid="mode-guided"
              >
                Guided
              </button>
              <button
                type="button"
                onClick={() => controls.setMode("expert")}
                className={toggleButtonClassName(controls.mode === "expert")}
                data-testid="mode-expert"
              >
                Expert
              </button>
            </div>

            {controls.mode === "guided" ? (
              <>
                <GuidedSummaryCard title={workflow.interpretedSummary.title} lines={workflow.interpretedSummary.lines} helper={workflow.interpretedSummary.helper} />

                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {workflow.guidedQuestions.map((question) => (
                    <div key={question.step} className="rounded-card border border-white/8 bg-surface-overlay/50 px-3 py-2.5 text-left">
                      <p className="text-xs font-semibold tracking-[0.18em] text-ink-4">{question.step}</p>
                      <p className="mt-1 text-xs leading-5 text-ink-3">{question.title}</p>
                    </div>
                  ))}
                </div>

                <GuidedQuestionCard
                  step={workflow.guidedQuestions[0].step}
                  title={workflow.guidedQuestions[0].title}
                  description={workflow.guidedQuestions[0].description}
                  helper="This changes the overall posture of the shortlist without exposing score math."
                >
                  <div className="grid gap-3">
                    <div className="grid gap-2">
                      {PROFILE_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => controls.updateField("profile", option.value)}
                          className={guidedChoiceButtonClassName(controls.request.profile === option.value)}
                          data-testid={option.value === "balanced" ? "profile-select" : undefined}
                        >
                          <span className="block font-semibold text-ink-1">{option.label}</span>
                          <span className="mt-1 block text-xs leading-5 text-ink-4">
                            {option.value === "conservative"
                              ? "Defensive premium ideas with tighter tolerance for noise."
                              : option.value === "aggressive"
                                ? "Higher-conviction ideas when you want more assertive setups."
                                : "A middle ground between defensive filtering and idea breadth."}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </GuidedQuestionCard>

                <GuidedQuestionCard
                  step={workflow.guidedQuestions[1].step}
                  title={workflow.guidedQuestions[1].title}
                  description={workflow.guidedQuestions[1].description}
                  helper="Market area and direction map to the same ticker-group and strategy filters used in Expert Mode."
                >
                  <div className="grid gap-3">
                    <div className="grid gap-2">
                      {TICKER_GROUP_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => controls.updateField("ticker_group", option.value)}
                          className={guidedChoiceButtonClassName(controls.request.ticker_group === option.value)}
                          data-testid={option.value === "tech" ? "ticker-group-select" : undefined}
                        >
                          <span className="block font-semibold text-ink-1">{option.label}</span>
                          <span className="mt-1 block text-xs leading-5 text-ink-4">
                            {option.value === "tech"
                              ? "Focus on big tech leaders where premium and liquidity are usually strongest."
                              : option.value === "index"
                                ? "Stay close to index names and broad-market leaders."
                                : "Use a broader mixed watchlist when you want more variety."}
                          </span>
                        </button>
                      ))}
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm font-medium text-ink-2">Which direction are you open to?</p>
                      <div className="grid gap-2 sm:grid-cols-3">
                        {[
                          { value: "bullish", label: "Bullish setups", detail: "Focus on supportive premium trades." },
                          { value: "bearish", label: "Bearish setups", detail: "Focus on defensive premium trades." },
                          { value: "either", label: "Either direction", detail: "Let PRIS look both ways and rank the best result." },
                        ].map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => applyDirectionSelection(option.value as "bullish" | "bearish" | "either")}
                            className={guidedChoiceButtonClassName(directionSelection === option.value)}
                          >
                            <span className="block font-semibold text-ink-1">{option.label}</span>
                            <span className="mt-1 block text-xs leading-5 text-ink-4">{option.detail}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </GuidedQuestionCard>

                <GuidedQuestionCard
                  step={workflow.guidedQuestions[2].step}
                  title={workflow.guidedQuestions[2].title}
                  description={workflow.guidedQuestions[2].description}
                  helper="These timing choices update the same expiration window that Expert Mode exposes directly."
                >
                  <div className="grid gap-2">
                    {[
                      { value: "soon", label: "Soon", detail: "About 1-2 weeks out for faster feedback." },
                      { value: "balanced", label: "In a few weeks", detail: "About 3-5 weeks out for the default premium cadence." },
                      { value: "later", label: "Later", detail: "About 5-8 weeks out when you want more time in the trade." },
                    ].map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => applyTimeframeSelection(option.value as "soon" | "balanced" | "later")}
                        className={guidedChoiceButtonClassName(timeframeSelection === option.value)}
                      >
                        <span className="block font-semibold text-ink-1">{option.label}</span>
                        <span className="mt-1 block text-xs leading-5 text-ink-4">{option.detail}</span>
                      </button>
                    ))}
                  </div>
                </GuidedQuestionCard>

                <GuidedQuestionCard
                  step={workflow.guidedQuestions[3].step}
                  title={workflow.guidedQuestions[3].title}
                  description={workflow.guidedQuestions[3].description}
                  helper="Quality filtering and signal familiarity still map to score and consistency behind the scenes."
                >
                  <div className="grid gap-4">
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-ink-2">Would you rather see stricter ideas or a broader set?</p>
                      <div className="grid gap-2 sm:grid-cols-3">
                        {[
                          { value: "broad", label: "Broader set", detail: "Cast a wider net and let more candidates in." },
                          { value: "moderate", label: "Moderate filter", detail: "Balance idea breadth with quality control." },
                          { value: "strict", label: "Stricter ideas", detail: "Favor tighter quality filtering and a shorter shortlist." },
                        ].map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => applyStrictnessSelection(option.value as "broad" | "moderate" | "strict")}
                            className={guidedChoiceButtonClassName(strictnessSelection === option.value)}
                          >
                            <span className="block font-semibold text-ink-1">{option.label}</span>
                            <span className="mt-1 block text-xs leading-5 text-ink-4">{option.detail}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <p className="text-sm font-medium text-ink-2">Do you prefer repeat signals, or are you open to fresher ones?</p>
                      <div className="grid gap-2 sm:grid-cols-3">
                        {[
                          { value: "fresh", label: "Open to fresh signals", detail: "Allow newer setups into the shortlist." },
                          { value: "balanced", label: "Prefer some history", detail: "A middle ground between fresh and repeated signals." },
                          { value: "repeat", label: "Lean on repeat setups", detail: "Favor ideas that have shown up more consistently." },
                        ].map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => applyFamiliaritySelection(option.value as "fresh" | "balanced" | "repeat")}
                            className={guidedChoiceButtonClassName(familiaritySelection === option.value)}
                          >
                            <span className="block font-semibold text-ink-1">{option.label}</span>
                            <span className="mt-1 block text-xs leading-5 text-ink-4">{option.detail}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </GuidedQuestionCard>
              </>
            ) : (
              <>
                <WarningBand title="Expert control surface" tone="info">
                  {workflow.expertNotes[0]}
                </WarningBand>

                <SectionFrame eyebrow="Current Interpretation" title={workflow.interpretedSummary.title} subtitle="Direct mapping of the current request fields.">
                  <div className="grid gap-2 text-sm text-ink-2">
                    {workflow.interpretedSummary.lines.map((line) => (
                      <p key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{line}</p>
                    ))}
                  </div>
                </SectionFrame>

                <div className="grid gap-4">
                  <div className="rounded-card border border-white/8 bg-surface-overlay/55 p-4">
                    <p className="eyebrow-label">Scope</p>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">Profile</span>
                        <select
                          value={controls.request.profile}
                          onChange={(event) => controls.updateField("profile", event.target.value)}
                          className={fieldClassName}
                          data-testid="profile-select"
                        >
                          {PROFILE_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>

                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">Ticker Group</span>
                        <select
                          value={controls.request.ticker_group}
                          onChange={(event) => controls.updateField("ticker_group", event.target.value)}
                          className={fieldClassName}
                          data-testid="ticker-group-select"
                        >
                          {TICKER_GROUP_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </label>
                    </div>
                  </div>

                  <div className="rounded-card border border-white/8 bg-surface-overlay/55 p-4">
                    <p className="eyebrow-label">Strategies</p>
                    <div className="mt-3 grid gap-2">
                      {STRATEGY_OPTIONS.map((strategy) => {
                        const checked = controls.request.selected_strategy_keys.includes(strategy.value);

                        return (
                          <label
                            key={strategy.value}
                            className="flex items-center gap-3 rounded-card border border-white/8 bg-surface-overlay/55 px-3 py-3 text-sm text-ink-2"
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => controls.toggleStrategy(strategy.value)}
                              className="h-4 w-4 rounded border-white/20 bg-surface-1 text-accent focus:ring-accent"
                            />
                            <span>{strategy.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="rounded-card border border-white/8 bg-surface-overlay/55 p-4" data-testid="expert-fields">
                    <p className="eyebrow-label">Thresholds</p>
                    <div className="mt-3 grid gap-3 sm:grid-cols-2">
                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">Min Score</span>
                        <input
                          type="number"
                          value={controls.request.min_score}
                          onChange={(event) => controls.updateField("min_score", Number(event.target.value))}
                          className={fieldClassName}
                        />
                      </label>
                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">Min Consistency</span>
                        <input
                          type="number"
                          value={controls.request.min_consistency}
                          onChange={(event) => controls.updateField("min_consistency", Number(event.target.value))}
                          className={fieldClassName}
                        />
                      </label>
                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">DTE Min</span>
                        <input
                          type="number"
                          value={controls.request.dte_min}
                          onChange={(event) => controls.updateField("dte_min", Number(event.target.value))}
                          className={fieldClassName}
                        />
                      </label>
                      <label className="grid gap-1 text-sm text-ink-2">
                        <span className="font-medium text-ink-2">DTE Max</span>
                        <input
                          type="number"
                          value={controls.request.dte_max}
                          onChange={(event) => controls.updateField("dte_max", Number(event.target.value))}
                          className={fieldClassName}
                        />
                      </label>
                    </div>
                  </div>
                </div>
              </>
            )}

            <SectionFrame eyebrow="Plan Summary" title={workflow.planSummary.title} subtitle="Confirm the exact plan that will be sent to the backend scan contract.">
              <div className="grid gap-2 text-sm text-ink-2">
                {workflow.planSummary.lines.map((line) => (
                  <p key={line} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{line}</p>
                ))}
              </div>
            </SectionFrame>

            <ActionRow>
              <button
                type="button"
                onClick={() => runScan.mutate(controls.request)}
                disabled={disableRun}
                className="flex-1 rounded-card border border-accent/25 bg-accent px-4 py-3 text-sm font-semibold text-surface-0 transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {runScan.isPending ? "Running scan..." : controls.mode === "guided" ? "Run current plan" : "Run scan"}
              </button>
              <button
                type="button"
                onClick={controls.resetToDefaults}
                className="rounded-card border border-white/10 bg-surface-overlay/70 px-4 py-3 text-sm font-semibold text-ink-2"
              >
                Reset
              </button>
            </ActionRow>

            {runScan.isError ? (
              <Banner tone="danger" title="Scan failed">
                {describeApiError(runScan.error, "run", "the scan").message}
              </Banner>
            ) : null}
          </div>
        </SectionFrame>

        <SectionFrame eyebrow="Latest Scan" title="Snapshot" subtitle="Most recent backend response context for the workflow.">
          {latestScan.isLoading ? (
            <EmptyState title="Loading latest scan" message="Waiting for the current summary from the backend." />
          ) : workflow.latestSnapshot ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Chip tone="neutral">{workflow.latestSnapshot.profile}</Chip>
                <Chip tone="neutral">{workflow.latestSnapshot.tickerGroup}</Chip>
                <Chip tone="neutral">{formatDuration(workflow.latestSnapshot.runtime)}</Chip>
              </div>
              <MetricStrip
                items={[
                  { label: "Qualified", value: workflow.latestSnapshot.qualified, tone: "success" },
                  { label: "Alerts", value: workflow.latestSnapshot.alerts, tone: "warning" },
                  { label: "Runtime", value: formatDuration(workflow.latestSnapshot.runtime), tone: "accent" },
                ]}
                columns={3}
                compact
              />
              {workflow.latestSnapshot.topTrade ? (
                <div className="rounded-card border border-white/8 bg-surface-overlay/60 p-3">
                  <p className="eyebrow-label">Top Opportunity</p>
                  <p className="mt-1 text-sm font-semibold text-ink-1">
                    {workflow.latestSnapshot.topTrade}
                  </p>
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No scan yet" message="Run a scan to populate the latest snapshot block." />
          )}
        </SectionFrame>

        <SectionFrame eyebrow="Guardrails" title="Presentation-only UI" subtitle="The React workflow stays aligned with backend truth.">
          <ul className="space-y-2 text-sm text-ink-2">
            {workflow.guardrails.map((item) => (
              <li key={item} className="rounded-card border border-white/8 bg-surface-overlay/60 px-3 py-3">{item}</li>
            ))}
          </ul>
        </SectionFrame>
      </div>
    </aside>
  );
}
