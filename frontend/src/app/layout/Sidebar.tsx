import { NavLink } from "react-router-dom";

import { Banner } from "../../components/ui/Banner";
import { Card } from "../../components/ui/Card";
import { DEFAULT_SCAN_REQUEST, NAV_ITEMS } from "../../lib/constants";
import { useRunScan } from "../../features/scans/hooks/useRunScan";

function linkClassName(isActive: boolean) {
  return [
    "flex items-center justify-between rounded-xl px-3 py-2 text-sm font-medium transition-colors",
    isActive
      ? "bg-accent-soft text-accent"
      : "text-ink-2 hover:bg-surface-2 hover:text-ink-1",
  ].join(" ");
}

export function Sidebar() {
  const runScan = useRunScan();

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

        <Card title="Quick Scan" subtitle="Temporary shell action using backend defaults.">
          <div className="space-y-4">
            <div className="grid gap-2 text-sm text-ink-2">
              <div className="flex items-center justify-between">
                <span>Profile</span>
                <span className="font-medium text-ink-1">{DEFAULT_SCAN_REQUEST.profile}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Group</span>
                <span className="font-medium text-ink-1">{DEFAULT_SCAN_REQUEST.ticker_group}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>DTE</span>
                <span className="font-medium text-ink-1">
                  {DEFAULT_SCAN_REQUEST.dte_min}-{DEFAULT_SCAN_REQUEST.dte_max}
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => runScan.mutate(DEFAULT_SCAN_REQUEST)}
              disabled={runScan.isPending}
              className="w-full rounded-xl bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {runScan.isPending ? "Running scan..." : "Run scan"}
            </button>

            {runScan.isError ? (
              <Banner tone="danger" title="Scan failed">
                {runScan.error instanceof Error ? runScan.error.message : "Unable to run scan."}
              </Banner>
            ) : null}

            {runScan.isSuccess ? (
              <Banner tone="success" title="Scan complete">
                The latest scan result is now available to the pages in this shell.
              </Banner>
            ) : null}
          </div>
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
