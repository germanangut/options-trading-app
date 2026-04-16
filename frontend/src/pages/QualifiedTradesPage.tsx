import { Card } from "../components/ui/Card";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function QualifiedTradesPage() {
  const latestScan = useLatestScan();

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No qualified trades yet"
        message="Run a scan first. This page will later evolve into the primary trade review surface."
      />
    );
  }

  const trades = latestScan.data.qualified_trades;

  return (
    <Card title="Qualified Trades" subtitle="Placeholder table scaffold from qualified_trades.">
      {trades.length === 0 ? (
        <EmptyState title="No qualified trades" message="The latest scan did not produce any qualified opportunities." />
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-ink-3">
                <th className="px-3 py-3 font-medium">Trade</th>
                <th className="px-3 py-3 font-medium">Score</th>
                <th className="px-3 py-3 font-medium">POP</th>
                <th className="px-3 py-3 font-medium">ROR</th>
                <th className="px-3 py-3 font-medium">Expiration</th>
                <th className="px-3 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {trades.map((trade) => (
                <tr key={`${trade.ticker}-${trade.strategy_type}-${trade.expiration_date}-${trade.short_strike}-${trade.long_strike}`}>
                  <td className="px-3 py-3">
                    <div className="font-medium text-ink-1">{formatTradeLabel(trade)}</div>
                    <div className="text-xs text-ink-3">
                      {trade.short_strike ?? "-"} / {trade.long_strike ?? "-"} - DTE {trade.DTE ?? "-"}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-ink-2">
                    {formatNumber(trade.adjusted_score ?? trade.score)}
                  </td>
                  <td className="px-3 py-3 text-ink-2">{formatNumber(trade.POP)}</td>
                  <td className="px-3 py-3 text-ink-2">{formatNumber(trade.ROR)}</td>
                  <td className="px-3 py-3 text-ink-2">{trade.expiration_date ?? "-"}</td>
                  <td className="px-3 py-3">
                    <Chip tone="neutral">{trade.label ?? "Candidate"}</Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
