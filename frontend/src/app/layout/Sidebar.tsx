import { NavLink } from "react-router-dom";

import { Banner } from "../../components/ui/Banner";
import { Chip } from "../../components/ui/Chip";
import { Card } from "../../components/ui/Card";
import { EmptyState } from "../../components/ui/EmptyState";
import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanControls } from "../../features/scans/hooks/useScanControls";
import { useRunScan } from "../../features/scans/hooks/useRunScan";
import {
  NAV_ITEMS,
  PROFILE_OPTIONS,
  STRATEGY_OPTIONS,
  TICKER_GROUP_OPTIONS,
} from "../../lib/constants";
import { formatDuration, formatTradeLabel } from "../../lib/formatters";

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
  const latestSummary = latestScan.data?.summary;
  const latestMetadata = latestScan.data?.scan_metadata;

  const disableRun = runScan.isPending || controls.request.selected_strategy_keys.length === 0;

  return (
    <aside className="border-b border-slate-200 bg-surface-1 lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col gap-5 p-4 sm:p-5">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-ink-3">
            Options Platform
          </p>
          <div>
            <h1 className="text-xl font-semibold text-ink-1">React Foundation</h1>
            <p className="text-sm text-ink-2">
              Thin frontend shell over the existing backend scan contract.
            </p>
          </div>
        </div>

        <nav className="grid gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => linkClassName(isActive)}>
              <span>{item.label}</span>
              <span className="text-xs text-ink-3">{item.shortcut}</span>
            </NavLink>
          ))}
        </nav>

        <Card title="Scan Controls" subtitle="First product-ready scan control surface for the React shell.">
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
                Guided mode keeps the full backend scan request but surfaces only the highest-value controls.
              </div>
            )}

            <div className="flex gap-2">
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
            </div>

            {runScan.isError ? (
              <Banner tone="danger" title="Scan failed">
                {runScan.error instanceof Error ? runScan.error.message : "Unable to run scan."}
              </Banner>
            ) : null}
          </div>
        </Card>

        <Card title="Latest Scan Snapshot" subtitle="Most recent backend response context.">
          {latestScan.isLoading ? (
            <EmptyState title="Loading latest scan" message="Waiting for the current summary from the backend." />
          ) : latestSummary && latestMetadata ? (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Chip tone="neutral">{latestMetadata.profile}</Chip>
                <Chip tone="neutral">{latestMetadata.ticker_group}</Chip>
                <Chip tone="neutral">{formatDuration(latestMetadata.execution_time_seconds)}</Chip>
              </div>
              <div className="grid gap-2 text-sm text-ink-2">
                <div className="flex items-center justify-between">
                  <span>Qualified</span>
                  <span className="font-medium text-ink-1">{latestSummary.qualified_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Near Misses</span>
                  <span className="font-medium text-ink-1">{latestSummary.near_miss_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span>Alerts</span>
                  <span className="font-medium text-ink-1">{latestScan.data?.alerts.length ?? 0}</span>
                </div>
              </div>
              {latestSummary.top_overall ? (
                <div className="rounded-xl bg-surface-2 p-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-3">Top Opportunity</p>
                  <p className="mt-1 text-sm font-semibold text-ink-1">
                    {formatTradeLabel(latestSummary.top_overall)}
                  </p>
                </div>
              ) : null}
            </div>
          ) : (
            <EmptyState title="No scan yet" message="Run a scan to populate the latest snapshot block." />
          )}
        </Card>

        <Card title="Guardrails" subtitle="Frontend stays presentation-only.">
          <ul className="space-y-2 text-sm text-ink-2">
            <li>No score calculations in React.</li>
            <li>No alert logic duplicated client-side.</li>
            <li>No portfolio decision inference in the UI.</li>
          </ul>
        </Card>
      </div>
    </aside>
  );
}
