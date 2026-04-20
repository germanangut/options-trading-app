import type { ReactNode } from "react";

import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanControls } from "../../features/scans/hooks/useScanControls";
import { useRunScan } from "../../features/scans/hooks/useRunScan";
import { selectSidebarWorkflowModel } from "../../features/scans/selectors/decisionExperienceSelectors";
import {
  PROFILE_OPTIONS,
  STRATEGY_OPTIONS,
  TICKER_GROUP_OPTIONS,
} from "../../lib/constants";
import { describeApiError } from "../../lib/apiErrors";

const fieldClassName = "rounded-card border border-white/10 bg-surface-overlay/70 px-3 py-2 text-sm text-ink-1 outline-none transition focus:border-accent/35";

const toggleButtonClassName = (active: boolean) => [
  "rounded-pill border px-2.5 py-1.5 text-xs font-semibold transition-colors",
  active
    ? "border-accent/30 bg-accent text-surface-0 shadow-elevated"
    : "border-white/8 bg-surface-2/70 text-ink-3 hover:border-white/14 hover:text-ink-1",
].join(" ");

const choiceButtonClassName = (active: boolean) => [
  "min-w-0 rounded-card border px-3 py-2 text-center text-sm leading-tight whitespace-normal transition-colors",
  active
    ? "border-accent/30 bg-accent-soft/70 text-ink-1 shadow-elevated"
    : "border-white/8 bg-surface-overlay/55 text-ink-2 hover:border-white/15 hover:bg-surface-overlay/75",
].join(" ");

const choiceGridClassName = "grid grid-cols-2 gap-1.5";

const choiceSpanClassName = (isLastOdd: boolean) => (isLastOdd ? "col-span-2" : "");

const statusChipClassName = (tone: "info" | "success" | "warning") => [
  "rounded-pill border px-2.5 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.18em]",
  tone === "success"
    ? "border-success/20 bg-success-soft/35 text-success"
    : tone === "warning"
      ? "border-warning/20 bg-warning-soft/35 text-warning"
      : "border-white/8 bg-surface-2/70 text-ink-3",
].join(" ");

type SidebarSectionProps = {
  title: string;
  helper?: string;
  children: ReactNode;
  testId?: string;
  className?: string;
};

function SidebarSection({ title, helper, children, testId, className }: SidebarSectionProps) {
  return (
    <section className={["rounded-card border border-white/8 bg-surface-overlay/55 p-3", className].filter(Boolean).join(" ")} data-testid={testId}>
      <div className="mb-2.5 flex items-start justify-between gap-3">
        <div className="space-y-1">
          <h2 className="text-sm font-semibold tracking-tight text-ink-1">{title}</h2>
          {helper ? <p className="text-xs leading-5 text-ink-4">{helper}</p> : null}
        </div>
      </div>
      {children}
    </section>
  );
}

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
  const runErrorMessage = runScan.isError ? describeApiError(runScan.error, "run", "the scan").message : null;

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
    <aside aria-label="Scan command center" className="border-b border-white/8 bg-surface-1/92 lg:border-b-0 lg:border-r" data-testid="scan-sidebar">
      <div className="flex h-full min-h-0 flex-col">
        <div className="border-b border-white/8 px-4 py-4 sm:px-5">
          <div className="space-y-3">
            <div className="space-y-1">
              <p className="eyebrow-label">Scan Command Center</p>
              <h1 className="text-lg font-semibold tracking-tight text-ink-1">Next Scan</h1>
            </div>
            <div className="inline-grid grid-cols-2 gap-1 self-start rounded-pill border border-white/8 bg-surface-overlay/65 p-1" data-testid="sidebar-mode-switch">
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
          </div>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-5">
          <div className="space-y-2.5" data-testid="sidebar-config-stack">
            <div className="rounded-panel border border-white/8 bg-surface-1/96 px-4 py-3 shadow-panel backdrop-blur" data-testid="sidebar-action-zone">
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-[0.7rem] font-bold uppercase tracking-[0.18em] text-ink-3">Run Controls</p>
                  <span className={statusChipClassName(workflow.readiness.tone)}>{runScan.isPending ? "Running" : workflow.readiness.title}</span>
                </div>

                <section className="rounded-card border border-white/8 bg-surface-overlay/70 p-2.5" data-testid="sidebar-plan-summary">
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-4">{workflow.planSummary.title}</p>
                  <div className="mt-2 space-y-1.5 text-sm leading-5 text-ink-2">
                    {workflow.planSummary.lines.slice(0, 2).map((line) => (
                      <p key={line}>{line}</p>
                    ))}
                  </div>
                </section>

                {disableRun ? <p className="text-xs leading-5 text-ink-4">Choose at least one direction before running the scan.</p> : null}

                <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-2">
                  <button
                    type="button"
                    onClick={() => runScan.mutate(controls.request)}
                    disabled={disableRun}
                    className="rounded-card border border-accent/25 bg-accent px-3.5 py-2.25 text-sm font-semibold text-surface-0 shadow-elevated transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
                    data-testid="run-scan-button"
                  >
                    {runScan.isPending ? "Running Scan..." : "Run Scan"}
                  </button>
                  <button
                    type="button"
                    onClick={controls.resetToDefaults}
                    className="rounded-card border border-white/10 bg-surface-overlay/70 px-3.5 py-2.25 text-sm font-semibold text-ink-2"
                    data-testid="reset-scan-button"
                  >
                    Reset
                  </button>
                </div>

                {runErrorMessage ? (
                  <div
                    className="rounded-card border border-danger/18 bg-danger-soft/18 px-3 py-2.5"
                    data-testid="sidebar-run-error"
                  >
                    <div className="flex items-start gap-2.5">
                      <span className="mt-1 h-2 w-2 rounded-full bg-danger" aria-hidden="true" />
                      <div className="min-w-0 space-y-1">
                        <p className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-danger">Scan status</p>
                        <p className="text-sm font-semibold tracking-tight text-ink-1">Latest run did not complete</p>
                        <p className="text-xs leading-5 text-ink-3">{runErrorMessage}</p>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            </div>

            <SidebarSection title="Posture" testId="sidebar-section-posture">
              {controls.mode === "guided" ? (
                <div className={choiceGridClassName}>
                  {PROFILE_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => controls.updateField("profile", option.value)}
                      className={[choiceButtonClassName(controls.request.profile === option.value), choiceSpanClassName(option === PROFILE_OPTIONS[PROFILE_OPTIONS.length - 1] && PROFILE_OPTIONS.length % 2 !== 0)].join(" ")}
                      data-testid={option.value === "balanced" ? "profile-select" : undefined}
                    >
                      <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Profile</span>
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
              )}
            </SidebarSection>

            <SidebarSection title="Market Focus" testId="sidebar-section-market-focus">
              {controls.mode === "guided" ? (
                <div className={choiceGridClassName}>
                  {TICKER_GROUP_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => controls.updateField("ticker_group", option.value)}
                      className={[choiceButtonClassName(controls.request.ticker_group === option.value), choiceSpanClassName(option === TICKER_GROUP_OPTIONS[TICKER_GROUP_OPTIONS.length - 1] && TICKER_GROUP_OPTIONS.length % 2 !== 0)].join(" ")}
                      data-testid={option.value === "tech" ? "ticker-group-select" : undefined}
                    >
                      <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Ticker Group</span>
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
              )}
            </SidebarSection>

            <SidebarSection
              title="Direction"
              helper={controls.mode === "expert" ? "Maps directly to strategy filters." : undefined}
              testId="sidebar-section-direction"
            >
              <div className={choiceGridClassName}>
                {[
                  { value: "bullish", label: "Bullish" },
                  { value: "bearish", label: "Bearish" },
                  { value: "either", label: "Either" },
                ].map((option, index, options) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => applyDirectionSelection(option.value as "bullish" | "bearish" | "either")}
                    className={[choiceButtonClassName(directionSelection === option.value), choiceSpanClassName(index === options.length - 1 && options.length % 2 !== 0)].join(" ")}
                  >
                    <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                  </button>
                ))}
              </div>
            </SidebarSection>

            <SidebarSection
              title="Timing"
              helper={controls.mode === "expert" ? "Presets update DTE, fields stay editable." : undefined}
              testId="sidebar-section-timing"
            >
              <div className="space-y-3">
                <div className={choiceGridClassName}>
                  {[
                    { value: "soon", label: "Soon", detail: "1-2 wks" },
                    { value: "balanced", label: "In a few weeks", detail: "3-5 wks" },
                    { value: "later", label: "Later", detail: "5-8 wks" },
                  ].map((option, index, options) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => applyTimeframeSelection(option.value as "soon" | "balanced" | "later")}
                      className={[choiceButtonClassName(timeframeSelection === option.value), choiceSpanClassName(index === options.length - 1 && options.length % 2 !== 0)].join(" ")}
                    >
                      <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                      <span className="mt-1 block min-w-0 text-xs text-ink-4 whitespace-normal">{option.detail}</span>
                    </button>
                  ))}
                </div>

                {controls.mode === "expert" ? (
                  <div className="grid gap-2" data-testid="expert-fields">
                    <label className="grid gap-1 text-sm text-ink-2">
                      <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">DTE Min</span>
                      <input
                        type="number"
                        value={controls.request.dte_min}
                        onChange={(event) => controls.updateField("dte_min", Number(event.target.value))}
                        className={fieldClassName}
                      />
                    </label>
                    <label className="grid gap-1 text-sm text-ink-2">
                      <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">DTE Max</span>
                      <input
                        type="number"
                        value={controls.request.dte_max}
                        onChange={(event) => controls.updateField("dte_max", Number(event.target.value))}
                        className={fieldClassName}
                      />
                    </label>
                  </div>
                ) : null}
              </div>
            </SidebarSection>

            <SidebarSection
              title="Shortlist Style"
              helper={controls.mode === "expert" ? "Presets update score and consistency, then you can fine-tune." : undefined}
              testId="sidebar-section-shortlist-style"
              className="p-3"
            >
              <div className="space-y-2.5">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Breadth</p>
                    {controls.mode === "expert" ? (
                      <span className="text-xs text-ink-4">Min score</span>
                    ) : null}
                  </div>
                  <div className={choiceGridClassName}>
                    {[
                      { value: "broad", label: "Broader" },
                      { value: "moderate", label: "Moderate" },
                      { value: "strict", label: "Stricter" },
                    ].map((option, index, options) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => applyStrictnessSelection(option.value as "broad" | "moderate" | "strict")}
                        className={[choiceButtonClassName(strictnessSelection === option.value), choiceSpanClassName(index === options.length - 1 && options.length % 2 !== 0)].join(" ")}
                      >
                        <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                      </button>
                    ))}
                  </div>
                  {controls.mode === "expert" ? (
                    <label className="grid gap-1 text-sm text-ink-2">
                      <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Min Score</span>
                      <input
                        type="number"
                        value={controls.request.min_score}
                        onChange={(event) => controls.updateField("min_score", Number(event.target.value))}
                        className={fieldClassName}
                      />
                    </label>
                  ) : null}
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Familiarity</p>
                    {controls.mode === "expert" ? (
                      <span className="text-xs text-ink-4">Min consistency</span>
                    ) : null}
                  </div>
                  <div className={choiceGridClassName}>
                    {[
                      { value: "fresh", label: "Fresh" },
                      { value: "balanced", label: "Some history" },
                      { value: "repeat", label: "Repeat setups" },
                    ].map((option, index, options) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => applyFamiliaritySelection(option.value as "fresh" | "balanced" | "repeat")}
                        className={[choiceButtonClassName(familiaritySelection === option.value), choiceSpanClassName(index === options.length - 1 && options.length % 2 !== 0)].join(" ")}
                      >
                        <span className="block min-w-0 font-semibold text-ink-1 whitespace-normal">{option.label}</span>
                      </button>
                    ))}
                  </div>
                  {controls.mode === "expert" ? (
                    <label className="grid gap-1 text-sm text-ink-2">
                      <span className="text-xs font-medium uppercase tracking-[0.18em] text-ink-4">Min Consistency</span>
                      <input
                        type="number"
                        value={controls.request.min_consistency}
                        onChange={(event) => controls.updateField("min_consistency", Number(event.target.value))}
                        className={fieldClassName}
                      />
                    </label>
                  ) : null}
                </div>
              </div>
            </SidebarSection>
          </div>
        </div>
      </div>
    </aside>
  );
}
