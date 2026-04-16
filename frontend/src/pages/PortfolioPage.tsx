import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";

export function PortfolioPage() {
  const latestScan = useLatestScan();

  if (!latestScan.data) {
    return <EmptyState title="Portfolio coming next" message="Run a scan first to inspect backend portfolio summary sections." />;
  }

  return (
    <Card title="Portfolio" subtitle="Coming next in PU-7: backend summary adapters for portfolio views.">
      <pre className="overflow-x-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">
        {JSON.stringify(latestScan.data.portfolio_summary, null, 2)}
      </pre>
    </Card>
  );
}
