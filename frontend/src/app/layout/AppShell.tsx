import { Outlet, useLocation } from "react-router-dom";

import { Banner } from "../../components/ui/Banner";
import { useLatestScan } from "../../features/scans/hooks/useLatestScan";
import { useScanActivity } from "../../features/scans/hooks/useScanActivity";
import { selectScanReliabilityNotice } from "../../features/scans/selectors/scanSelectors";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location = useLocation();
  const latestScan = useLatestScan();
  const scanActivity = useScanActivity();
  const reliabilityNotice = selectScanReliabilityNotice(latestScan.data);

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
                  {latestScan.data
                    ? "A new scan is in progress. The current views stay on the last successful result until the backend returns the next payload."
                    : "The first scan is running. Results will populate automatically when the backend returns."}
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
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
