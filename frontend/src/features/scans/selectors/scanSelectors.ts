import type {
  AlertItem,
  QualifiedTradeRow,
  ScanResult,
} from "../../../types/api";

function fallbackScore(trade: Pick<QualifiedTradeRow, "adjusted_score" | "score">) {
  return trade.adjusted_score ?? trade.score ?? null;
}

export function buildTemporaryTradeId(trade: Pick<
  QualifiedTradeRow,
  "ticker" | "strategy_type" | "expiration_date" | "short_strike" | "long_strike"
>) {
  return encodeURIComponent(
    [
      trade.ticker ?? "",
      trade.strategy_type ?? "",
      trade.expiration_date ?? "",
      trade.short_strike ?? "",
      trade.long_strike ?? "",
    ].join("|"),
  );
}

export function selectOverviewModel(scanResult: ScanResult) {
  const topOpportunity = scanResult.summary.top_overall;

  return {
    kpis: [
      { label: "Qualified Trades", value: scanResult.summary.qualified_count },
      { label: "Near Misses", value: scanResult.summary.near_miss_count },
      { label: "Alerts", value: scanResult.alerts.length },
      {
        label: "Runtime",
        value: scanResult.scan_metadata.execution_time_seconds,
      },
    ],
    topOpportunity,
    metadata: {
      profile: scanResult.scan_metadata.profile,
      tickerGroup: scanResult.scan_metadata.ticker_group,
      provider: scanResult.scan_metadata.provider,
      dteRange: scanResult.scan_metadata.dte_range,
      selectedStrategyKeys: scanResult.scan_metadata.selected_strategy_keys,
    },
    coverage: {
      missingTickers: scanResult.diagnostics.missing_tickers,
      providerErrors: scanResult.diagnostics.provider_errors,
    },
  };
}

export function selectQualifiedTradesModel(scanResult: ScanResult) {
  return {
    total: scanResult.qualified_trades.length,
    rows: scanResult.qualified_trades.map((trade) => ({
      id: buildTemporaryTradeId(trade),
      trade,
      score: fallbackScore(trade),
    })),
  };
}

export function selectAlertsModel(scanResult: ScanResult) {
  return {
    total: scanResult.alerts.length,
    providerErrors: scanResult.diagnostics.provider_errors,
    rows: scanResult.alerts.map((alert: AlertItem) => ({
      id: buildTemporaryTradeId(alert),
      trade: alert,
      score: fallbackScore(alert),
      tag: alert.label ?? "Alert",
    })),
  };
}
