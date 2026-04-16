import { Link, useParams } from "react-router-dom";

import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";

export function QualifiedTradeDetailPage() {
  const { tradeId } = useParams();

  return (
    <Card
      title="Trade Detail Scaffold"
      subtitle="Temporary route placeholder until the trade-detail contract is formalized."
    >
      {tradeId ? (
        <div className="space-y-4 text-sm text-ink-2">
          <p>
            Temporary trade route id:
            <span className="ml-2 rounded bg-surface-2 px-2 py-1 font-mono text-xs text-ink-1">
              {tradeId}
            </span>
          </p>
          <p>
            This route uses a presentation-safe placeholder id derived from stable display fields.
            It is not a final backend trade identifier.
          </p>
          <Link to="/qualified" className="inline-flex rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white">
            Back to Qualified Trades
          </Link>
        </div>
      ) : (
        <EmptyState title="No trade selected" message="Return to the Qualified Trades screen and choose a trade." />
      )}
    </Card>
  );
}
