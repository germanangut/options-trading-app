import { Outlet, useLocation } from "react-router-dom";

import { Banner } from "../../components/ui/Banner";
import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanActivity } from "../../features/scans/hooks/useScanActivity";
import { useElapsedTimer } from "../../features/scans/hooks/useElapsedTimer";
import {
  selectScanPerformanceSummary,
  selectScanReliabilityNotice,
} from "../../features/scans/selectors/scanSelectors";
import { formatDuration } from "../../lib/formatters";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location = useLocation();
  const latestScan = useLatestScan();
  const scanActivity = useScanActivity();
  const elapsedScanRunMs = useElapsedTimer(scanActivity.latestSubmittedAt, scanActivity.isRunning);
  const reliabilityNotice = selectScanReliabilityNotice(latestScan.data);
  const performanceSummary = selectScanPerformanceSummary(latestScan.data);

  return (
    <div className="min-h-screen bg-surface-0 text-ink-1">
      <div className="grid min-h-screen lg:grid-cols-[280px_minmax(0,1fr)]">
        <Sidebar />
        <div className="flex min-h-screen min-w-0 flex-col">
          <Topbar pathname={location.pathname} />
          <main className="flex-1 p-4 sm:p-6 lg:p-8">
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
              {reliabilityNotice ? (
                <Banner tone={reliabilityNotice.tone} title={reliabilityNotice.title}>
                  <div className="space-y-1">
                    <p>{reliabilityNotice.message}</p>
                    {reliabilityNotice.notes.map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                  </div>
                </Banner>
              ) : null}
              {performanceSummary ? (
                <Banner tone="info" title={performanceSummary.title}>
                  <div className="space-y-1">
                    <p>{performanceSummary.message}</p>
                    {performanceSummary.notes.map((note) => (
                      <p key={note}>{note}</p>
                    ))}
                  </div>
                </Banner>
              ) : null}
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
