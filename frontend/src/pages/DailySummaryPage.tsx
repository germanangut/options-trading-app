import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";

export function DailySummaryPage() {
  const latestScan = useLatestScan();

  if (!latestScan.data) {
    return <EmptyState title="Daily summary coming next" message="Run a scan first to inspect the daily summary payload." />;
  }

  return (
    <Card title="Daily Summary" subtitle="Coming next in PU-7: richer summary panels and language-focused presentation.">
      <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(latestScan.data.daily_summary, null, 2)}
      </pre>
    </Card>
  );
}
