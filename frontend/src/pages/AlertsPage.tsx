import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectAlertsModel } from "../features/scans/selectors/scanSelectors";
import { describeApiError } from "../lib/apiErrors";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function AlertsPage() {
  const latestScan = useLatestScan();

  if (latestScan.isLoading) {
    return <EmptyState title="Loading alerts" message="Waiting for the latest alert list from the backend." />;
  }

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load alerts">
        {describeApiError(latestScan.error, "load", "alerts").message}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return <EmptyState title="No alerts yet" message="Run a scan to populate the alerts placeholder list." />;
  }

  const alerts = selectAlertsModel(latestScan.data);

  return (
    <div className="grid gap-4">
      {alerts.partialNotice ? (
        <Banner tone="warning" title={alerts.partialNotice.title}>
          {alerts.partialNotice.message}
        </Banner>
      ) : null}

      <Card title="Alerts" subtitle={`${alerts.total} alert(s) currently surfaced by the backend.`}>
        {alerts.rows.length === 0 ? (
          <EmptyState
            title={alerts.emptyState.title}
            message={alerts.emptyState.message}
          />
        ) : (
          <div className="grid gap-3">
            {alerts.rows.map(({ id, trade, score, tag }) => (
              <div
                key={id}
                className="rounded-xl border border-slate-200 bg-surface-0 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <h3 className="text-base font-semibold text-ink-1">{formatTradeLabel(trade)}</h3>
                    <p className="text-sm text-ink-2">
                      Score {formatNumber(score)} - POP {formatNumber(trade.POP)} - ROR {formatNumber(trade.ROR)}
                    </p>
                  </div>
                  <Chip tone="neutral">{tag}</Chip>
                </div>
                {trade.decision_summary ? (
                  <p className="mt-3 text-sm text-ink-2">{trade.decision_summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
