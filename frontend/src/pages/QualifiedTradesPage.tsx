import { Link } from "react-router-dom";

import { Banner } from "../components/ui/Banner";
import { Card } from "../components/ui/Card";
import { Chip } from "../components/ui/Chip";
import { EmptyState } from "../components/ui/EmptyState";
import { useLatestScan } from "../features/scans/hooks/useLatestScan";
import { selectQualifiedTradesModel } from "../features/scans/selectors/scanSelectors";
import { formatNumber, formatTradeLabel } from "../lib/formatters";

export function QualifiedTradesPage() {
  const latestScan = useLatestScan();

  if (latestScan.isError) {
    return (
      <Banner tone="danger" title="Unable to load qualified trades">
        {latestScan.error instanceof Error ? latestScan.error.message : "The latest scan could not be loaded."}
      </Banner>
    );
  }

  if (!latestScan.data) {
    return (
      <EmptyState
        title="No qualified trades yet"
        message="Run a scan first. This page will later evolve into the primary trade review surface."
      />
    );
  }

  const qualifiedTrades = selectQualifiedTradesModel(latestScan.data);

  return (
    <Card
      title="Qualified Trades"
      subtitle={`${qualifiedTrades.total} trade(s) qualified in the latest scan.`}
    >
      {qualifiedTrades.rows.length === 0 ? (
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
                <th className="px-3 py-3 font-medium">Next</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {qualifiedTrades.rows.map(({ id, trade, score }, index) => (
                <tr key={id} className="hover:bg-surface-0">
                  <td className="px-3 py-3">
                    <div className="font-medium text-ink-1">
                      {index + 1}. {formatTradeLabel(trade)}
                    </div>
                    <div className="text-xs text-ink-3">
                      {trade.short_strike ?? "-"} / {trade.long_strike ?? "-"} - DTE {trade.DTE ?? "-"}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-ink-2">
                    {formatNumber(score)}
                  </td>
                  <td className="px-3 py-3 text-ink-2">{formatNumber(trade.POP)}</td>
                  <td className="px-3 py-3 text-ink-2">{formatNumber(trade.ROR)}</td>
                  <td className="px-3 py-3 text-ink-2">{trade.expiration_date ?? "-"}</td>
                  <td className="px-3 py-3">
                    <Chip tone="neutral">{trade.label ?? "Candidate"}</Chip>
                  </td>
                  <td className="px-3 py-3">
                    <Link
                      to={`/qualified/${id}`}
                      className="inline-flex rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-ink-2 transition hover:bg-surface-2"
                    >
                      View
                    </Link>
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
