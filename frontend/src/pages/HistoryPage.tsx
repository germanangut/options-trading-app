import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";

export function HistoryPage() {
  const latestScan = useLatestScan();

  if (!latestScan.data) {
    return <EmptyState title="History coming next" message="Run a scan first to inspect the history context payload." />;
  }

  return (
    <Card title="History" subtitle="Coming next in PU-7: screen-friendly history adapters and dedicated views.">
      <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(latestScan.data.history_context, null, 2)}
      </pre>
    </Card>
  );
}
