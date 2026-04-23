import { formatCurrency } from "../../lib/formatters";
import type { PayoffPoint } from "../../types/api";

type PayoffCurveProps = {
  points: PayoffPoint[];
};

function sanitizePoints(points: PayoffPoint[]) {
  return [...points]
    .filter((point) => Number.isFinite(point.underlying_price) && Number.isFinite(point.expiration_payoff))
    .sort((left, right) => left.underlying_price - right.underlying_price);
}

export function PayoffCurve({ points }: PayoffCurveProps) {
  const cleanPoints = sanitizePoints(points);
  if (cleanPoints.length < 2) {
    return (
      <div className="rounded-card border border-white/8 bg-surface-2/40 p-4 text-xs text-ink-4">
        Payoff curve unavailable.
      </div>
    );
  }

  const width = 920;
  const height = 240;
  const padding = 28;

  const xMin = cleanPoints[0].underlying_price;
  const xMax = cleanPoints[cleanPoints.length - 1].underlying_price;

  const yValues = cleanPoints.map((point) => point.expiration_payoff);
  const yMinRaw = Math.min(...yValues, 0);
  const yMaxRaw = Math.max(...yValues, 0);
  const yPadding = Math.max((yMaxRaw - yMinRaw) * 0.12, 40);
  const yMin = yMinRaw - yPadding;
  const yMax = yMaxRaw + yPadding;

  const xScale = (x: number) => {
    const domain = Math.max(xMax - xMin, 0.0001);
    return padding + ((x - xMin) / domain) * (width - padding * 2);
  };

  const yScale = (y: number) => {
    const domain = Math.max(yMax - yMin, 0.0001);
    return height - padding - ((y - yMin) / domain) * (height - padding * 2);
  };

  const linePoints = cleanPoints.map((point) => `${xScale(point.underlying_price)},${yScale(point.expiration_payoff)}`).join(" ");
  const zeroY = yScale(0);
  const positiveAreaHeight = Math.max(0, zeroY - padding);
  const negativeAreaHeight = Math.max(0, height - padding - zeroY);

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-card border border-white/8 bg-surface-2/40 p-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-52 w-full" role="img" aria-label="Expiration payoff curve">
          <defs>
            <linearGradient id="payoffPositive" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgba(50, 196, 141, 0.3)" />
              <stop offset="100%" stopColor="rgba(50, 196, 141, 0.06)" />
            </linearGradient>
            <linearGradient id="payoffNegative" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="rgba(255, 132, 132, 0.08)" />
              <stop offset="100%" stopColor="rgba(255, 132, 132, 0.32)" />
            </linearGradient>
          </defs>

          <rect x={padding} y={padding} width={width - padding * 2} height={positiveAreaHeight} fill="url(#payoffPositive)" />
          <rect x={padding} y={zeroY} width={width - padding * 2} height={negativeAreaHeight} fill="url(#payoffNegative)" />

          <line x1={padding} y1={zeroY} x2={width - padding} y2={zeroY} stroke="rgba(255,255,255,0.55)" strokeWidth="1" strokeDasharray="4 4" />

          <polyline fill="none" stroke="rgba(94, 234, 212, 0.95)" strokeWidth="3" points={linePoints} />
        </svg>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-ink-4 sm:grid-cols-4">
        <div className="rounded-card border border-white/8 bg-surface-2/50 px-3 py-2">
          <p className="eyebrow-label">Price range</p>
          <p className="mt-1 text-sm text-ink-2">
            ${xMin.toFixed(2)} to ${xMax.toFixed(2)}
          </p>
        </div>
        <div className="rounded-card border border-white/8 bg-surface-2/50 px-3 py-2">
          <p className="eyebrow-label">Payoff range</p>
          <p className="mt-1 text-sm text-ink-2">
            {formatCurrency(Math.min(...yValues))} to {formatCurrency(Math.max(...yValues))}
          </p>
        </div>
        <div className="rounded-card border border-white/8 bg-surface-2/50 px-3 py-2">
          <p className="eyebrow-label">Positive region</p>
          <p className="mt-1 text-sm text-ink-2">Above zero line</p>
        </div>
        <div className="rounded-card border border-white/8 bg-surface-2/50 px-3 py-2">
          <p className="eyebrow-label">Risk region</p>
          <p className="mt-1 text-sm text-ink-2">Below zero line</p>
        </div>
      </div>
    </div>
  );
}
