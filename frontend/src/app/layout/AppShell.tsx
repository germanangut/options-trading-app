import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { Banner } from "../../components/ui/Banner";
import { SessionDiagnosticsPanel } from "../../components/ui/SessionDiagnosticsPanel";
import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanActivity } from "../../features/scans/hooks/useScanActivity";
import { useElapsedTimer } from "../../features/scans/hooks/useElapsedTimer";
import {
  selectSessionDiagnosticsModel,
} from "../../features/scans/selectors/scanSelectors";
import { formatDuration } from "../../lib/formatters";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location = useLocation();
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const latestScan = useLatestScan();
  const scanActivity = useScanActivity();
  const elapsedScanRunMs = useElapsedTimer(scanActivity.latestSubmittedAt, scanActivity.isRunning);
  const diagnosticsModel = selectSessionDiagnosticsModel(latestScan.data);

  return (
    <div className="min-h-screen bg-surface-0 text-ink-1">
      <div className="grid min-h-screen lg:grid-cols-[376px_minmax(0,1fr)] xl:grid-cols-[392px_minmax(0,1fr)]">
        <Sidebar />
        <div className="flex min-h-screen min-w-0 flex-col">
          <Topbar
            pathname={location.pathname}
            diagnosticsStatus={diagnosticsModel ? {
              tone: diagnosticsModel.statusTone,
              label: diagnosticsModel.statusLabel,
              detail: diagnosticsModel.statusDetail,
              triggerLabel: diagnosticsModel.triggerLabel,
            } : null}
            onToggleDiagnostics={() => setDiagnosticsOpen((current) => !current)}
          />
          <main className="relative flex-1 overflow-hidden p-4 sm:p-6 lg:p-8">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,189,89,0.08),transparent_18%),radial-gradient(circle_at_center_left,rgba(57,192,187,0.08),transparent_24%)]" aria-hidden="true" />
            <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
              {scanActivity.isRunning ? (
                <Banner tone="info" title="Scan running">
                  <div className="space-y-1">
                    <p>
                      {latestScan.data
                        ? "A new scan is in progress. The current views stay on the last successful result until the backend returns the next payload."
                        : "The first scan is running. Results will populate automatically when the backend returns."}
                    </p>
                    {elapsedScanRunMs > 0 ? (
                      <p>Elapsed time: {formatDuration(elapsedScanRunMs / 1000)}</p>
                    ) : null}
                    {scanActivity.latestRequest ? (
                      <p>
                        Running {scanActivity.latestRequest.profile} on {scanActivity.latestRequest.ticker_group} with {scanActivity.latestRequest.selected_strategy_keys.length} strategy{scanActivity.latestRequest.selected_strategy_keys.length === 1 ? "" : "ies"}.
                      </p>
                    ) : null}
                  </div>
                </Banner>
              ) : null}
              <Outlet />
            </div>
          </main>
          <SessionDiagnosticsPanel
            isOpen={diagnosticsOpen}
            onClose={() => setDiagnosticsOpen(false)}
            model={diagnosticsModel}
          />
        </div>
      </div>
    </div>
  );
}
