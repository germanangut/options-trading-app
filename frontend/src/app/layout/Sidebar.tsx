import { NavLink } from "react-router-dom";

import { SectionFrame } from "../../components/ui/SectionFrame";
import { MetricStrip } from "../../components/ui/MetricStrip";
import { ActionRow } from "../../components/ui/ActionRow";
import { Banner } from "../../components/ui/Banner";
import { Chip } from "../../components/ui/Chip";
import { EmptyState } from "../../components/ui/EmptyState";
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
import { formatDuration } from "../../lib/formatters";

function linkClassName(isActive: boolean) {
  return [
    "flex items-center justify-between rounded-xl px-3 py-2 text-sm font-medium transition-colors",
    isActive
      ? "bg-accent-soft text-accent"
      : "text-ink-2 hover:bg-surface-2 hover:text-ink-1",
  ].join(" ");
}

export function Sidebar() {
  const latestScan = useLatestScan();
  const runScan = useRunScan();
  const controls = useScanControls(latestScan.data);
  const workflow = selectSidebarWorkflowModel(latestScan.data, controls.request, controls.mode, runScan.isPending);

  const disableRun = runScan.isPending || controls.request.selected_strategy_keys.length === 0;

  return (
    <aside className="border-b border-slate-200 bg-surface-1 lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col gap-5 p-4 sm:p-5">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-3">
            Options Platform
          </p>
          <div>
            <h1 className="text-xl font-semibold text-ink-1">Decision Workflow</h1>
            <p className="text-sm text-ink-2">
              Reconstructed scan workflow over the existing backend contract.
            </p>
          </div>
        </div>

        <Banner tone={workflow.readiness.tone} title={workflow.readiness.title}>
          {workflow.readiness.message}
        </Banner>

        <nav className="grid gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClassName(isActive)}>
              <span>{item.label}</span>
              <span className="text-xs text-ink-3">{item.shortcut}</span>
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
                className={[
                  "rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                  controls.mode === "guided" ? "bg-accent text-white" : "bg-surface-2 text-ink-2",
                ].join(" ")}
              >
                Guided
              </button>
              <button
                type="button"
                onClick={() => controls.setMode("expert")}
                className={[
                  "rounded-xl px-3 py-2 text-sm font-semibold transition-colors",
                  controls.mode === "expert" ? "bg-accent text-white" : "bg-surface-2 text-ink-2",
                ].join(" ")}
              >
                Expert
              </button>
            </div>

            {controls.mode === "guided" ? (
              <div className="rounded-xl border border-teal-200 bg-teal-50/70 px-3 py-3 text-sm text-ink-2">
                Guided mode emphasizes the small set of controls that most directly change what gets reviewed first.
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-surface-0 px-3 py-3 text-sm text-ink-2">
                Expert mode exposes the full request surface without changing backend truth or ranking behavior.
              </div>
            )}

            <SectionFrame eyebrow="Plan Summary" title={workflow.planSummary.title} subtitle="Confirm the current setup before you run.">
              <div className="grid gap-2 text-sm text-ink-2">
                {workflow.planSummary.lines.map((line) => (
                  <p key={line} className="rounded-xl bg-surface-2 px-3 py-3">{line}</p>
                ))}
              </div>
            </SectionFrame>

            <label className="grid gap-1 text-sm text-ink-2">
              <span className="font-medium">Profile</span>
              <select
                value={controls.request.profile}
                onChange={(event) => controls.updateField("profile", event.target.value)}
                className="rounded-xl border bg-white px-3 py-2 text-ink-1"
              >
                {PROFILE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm text-ink-2">
              <span className="font-medium">Ticker Group</span>
              <select
                value={controls.request.ticker_group}
                onChange={(event) => controls.updateField("ticker_group", event.target.value)}
                className="rounded-xl border bg-white px-3 py-2 text-ink-1"
              >
                {TICKER_GROUP_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="space-y-2">
              <p className="text-sm font-medium text-ink-2">Strategies</p>
              <div className="grid gap-2">
                {STRATEGY_OPTIONS.map((strategy) => {
                  const checked = controls.request.selected_strategy_keys.includes(strategy.value);

                  return (
                    <label
                      key={strategy.value}
                      className="flex items-center gap-3 rounded-xl border bg-white px-3 py-2 text-sm text-ink-2"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => controls.toggleStrategy(strategy.value)}
                        className="h-4 w-4 rounded border-slate-300 text-accent focus:ring-accent"
                      />
                      <span>{strategy.label}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {controls.mode === "expert" ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Min Score</span>
                  <input
                    type="number"
                    value={controls.request.min_score}
                    onChange={(event) => controls.updateField("min_score", Number(event.target.value))}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                  />
                </label>
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">Min Consistency</span>
                  <input
                    type="number"
                    value={controls.request.min_consistency}
                    onChange={(event) => controls.updateField("min_consistency", Number(event.target.value))}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                  />
                </label>
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">DTE Min</span>
                  <input
                    type="number"
                    value={controls.request.dte_min}
                    onChange={(event) => controls.updateField("dte_min", Number(event.target.value))}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                  />
                </label>
                <label className="grid gap-1 text-sm text-ink-2">
                  <span className="font-medium">DTE Max</span>
                  <input
                    type="number"
                    value={controls.request.dte_max}
                    onChange={(event) => controls.updateField("dte_max", Number(event.target.value))}
                    className="rounded-xl border bg-white px-3 py-2 text-ink-1"
                  />
                </label>
              </div>
            ) : (
              <div className="rounded-xl bg-surface-2 p-3 text-sm text-ink-2">
                Guided mode keeps the current request stable while presenting the clearest controls first.
              </div>
            )}

            <ActionRow>
              <button
                type="button"
                onClick={() => runScan.mutate(controls.request)}
                disabled={disableRun}
                className="flex-1 rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {runScan.isPending ? "Running scan..." : "Run scan"}
              </button>
              <button
                type="button"
                onClick={controls.resetToDefaults}
                className="rounded-xl border bg-white px-4 py-2.5 text-sm font-semibold text-ink-2"
              >
                Reset
              </button>
            </ActionRow>

            {runScan.isError ? (
              <Banner tone="danger" title="Scan failed">
                {runScan.error instanceof Error ? runScan.error.message : "Unable to run scan."}
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
                <div className="rounded-xl bg-surface-2 p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Top Opportunity</p>
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

        <SectionFrame eyebrow="Guardrails" title="Presentation-only UI" subtitle="The React migration keeps backend truth intact.">
          <ul className="space-y-2 text-sm text-ink-2">
            <li>No score calculations in React.</li>
            <li>No alert logic duplicated client-side.</li>
            <li>No portfolio decision inference in the UI.</li>
          </ul>
        </SectionFrame>
      </div>
    </aside>
  );
}
