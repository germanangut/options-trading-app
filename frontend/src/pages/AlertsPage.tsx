import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function AlertsPage() {
  const latestScan = useLatestScan();

  if (!latestScan.data) {
    return <EmptyState title="No alerts yet" message="Run a scan to populate the alerts placeholder list." />;
  }

  const { alerts, diagnostics } = latestScan.data;

  return (
    <div className="grid gap-4">
      {diagnostics.provider_errors.length > 0 ? (
        <Banner tone="warning" title="Provider issues detected">
          The latest scan reported provider errors, so the alert list may be incomplete.
        </Banner>
      ) : null}

      <Card title="Alerts" subtitle="Placeholder alert list from the canonical alerts array.">
        {alerts.length === 0 ? (
          <EmptyState title="No alerts" message="Nothing currently cleared the strongest alert thresholds." />
        ) : (
          <div className="grid gap-3">
            {alerts.map((alert) => (
              <div
                key={`${alert.ticker}-${alert.strategy_type}-${alert.expiration_date}-${alert.short_strike}-${alert.long_strike}`}
                className="rounded-xl border border-slate-200 bg-surface-0 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <h3 className="text-base font-semibold text-ink-1">{formatTradeLabel(alert)}</h3>
                    <p className="text-sm text-ink-2">
                      Score {formatNumber(alert.adjusted_score ?? alert.score)} - POP {formatNumber(alert.POP)} - ROR {formatNumber(alert.ROR)}
                    </p>
                  </div>
                  <Chip tone="accent">{alert.label ?? "Alert"}</Chip>
                </div>
                {alert.decision_summary ? (
                  <p className="mt-3 text-sm text-ink-2">{alert.decision_summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
