import type {
  AlertItem,
  DailySummary,
  HistoricalIntelligenceSummary,
  PortfolioSummary,
  QualifiedTradeRow,
  ScanResult,
} from "../../../types/api";


function scanDiagnostics(scanResult: ScanResult) {
  return scanResult.diagnostics ?? {
    missing_tickers: [],
    provider_errors: [],
    alerts_export_path: null,
    top_overall_identity: null,
  };
}


export function selectScanReliabilityNotice(scanResult?: ScanResult | null) {
  if (!scanResult) {
    return null;
  }

  const diagnostics = scanDiagnostics(scanResult);
  const providerErrors = diagnostics.provider_errors ?? [];
  const missingTickers = diagnostics.missing_tickers ?? [];
  const performance = diagnostics.performance ?? {};
  const cache = diagnostics.cache ?? {};
  const providerDurationMs = Number(performance.provider_duration_ms ?? NaN);
  const retryCount = Number(performance.retry_count ?? 0);
  const retryExhausted = Boolean(performance.retry_exhausted);
  const providerDurationNote = Number.isFinite(providerDurationMs)
    ? `Provider phase completed in ${(providerDurationMs / 1000).toFixed(2)}s.`
    : null;
  const aggregateCacheHit = Boolean((cache as Record<string, unknown>).market_data && ((cache as Record<string, { hit?: boolean }>).market_data?.hit));

  if (providerErrors.length > 0) {
    return {
      tone: "warning" as const,
      title: "Partial provider degradation",
      message: "Some tickers failed during provider retrieval. Successful results remain usable, but coverage is incomplete.",
      notes: [
        `Provider errors: ${providerErrors.length}`,
        retryCount > 0 ? `Retries attempted: ${retryCount}` : null,
        retryExhausted ? "Some provider requests exhausted their retry budget." : null,
        providerDurationNote,
        aggregateCacheHit ? "This response reused short-lived cached market data." : null,
      ].filter(Boolean) as string[],
    };
  }

  if (missingTickers.length > 0 || diagnostics.partial_result) {
    return {
      tone: "warning" as const,
      title: "Partial coverage",
      message: `${missingTickers.length} ticker(s) were unavailable during the latest scan, so empty boards may reflect degraded coverage rather than zero opportunities.`,
      notes: [
        missingTickers.length > 0 ? `Missing: ${missingTickers.join(", ")}` : null,
        retryCount > 0 ? `Retries attempted: ${retryCount}` : null,
        providerDurationNote,
        aggregateCacheHit ? "This response reused short-lived cached market data." : null,
      ].filter(Boolean) as string[],
    };
  }

  return null;
}

function fallbackScore(trade: Pick<QualifiedTradeRow, "adjusted_score" | "score">) {
  return trade.adjusted_score ?? trade.score ?? null;
}

function buildTemporaryTradeKey(trade: Pick<
  QualifiedTradeRow,
  "ticker" | "strategy_type" | "expiration_date" | "short_strike" | "long_strike"
>) {
  return [
    trade.ticker ?? "",
    trade.strategy_type ?? "",
    trade.expiration_date ?? "",
    trade.short_strike ?? "",
    trade.long_strike ?? "",
  ].join("|");
}

export function buildTemporaryTradeId(trade: Pick<
  QualifiedTradeRow,
  "ticker" | "strategy_type" | "expiration_date" | "short_strike" | "long_strike"
>) {
  return encodeURIComponent(buildTemporaryTradeKey(trade));
}

export function selectOverviewModel(scanResult: ScanResult) {
  const diagnostics = scanDiagnostics(scanResult);
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
      missingTickers: diagnostics.missing_tickers ?? [],
      providerErrors: diagnostics.provider_errors ?? [],
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
  const diagnostics = scanDiagnostics(scanResult);
  return {
    total: scanResult.alerts.length,
    providerErrors: diagnostics.provider_errors ?? [],
    missingTickers: diagnostics.missing_tickers ?? [],
    partialResult: Boolean(diagnostics.partial_result),
    rows: scanResult.alerts.map((alert: AlertItem) => ({
      id: buildTemporaryTradeId(alert),
      trade: alert,
      score: fallbackScore(alert),
      tag: alert.label ?? "Alert",
    })),
  };
}

export function selectTradeDetailModel(scanResult: ScanResult, tradeId?: string) {
  if (!tradeId) {
    return {
      routeType: "missing" as const,
      trade: null,
      title: "No trade selected",
      notes: ["No route parameter was provided."],
    };
  }

  const allTrades = [...scanResult.qualified_trades, ...scanResult.alerts];
  const trade = allTrades.find((candidate) => {
    const rawKey = buildTemporaryTradeKey(candidate);
    return tradeId === rawKey || tradeId === encodeURIComponent(rawKey);
  }) ?? null;

  if (!trade) {
    return {
      routeType: "not-found" as const,
      trade: null,
      title: "Trade not found",
      notes: [
        "The route id is temporary and derived from display fields.",
        "The latest scan may have changed since the link was created.",
      ],
    };
  }

  return {
    routeType: "resolved" as const,
    trade,
    title: `${trade.ticker} - ${trade.strategy_label ?? trade.strategy_type}`,
    notes: [
      "This page resolves the selected trade from the latest scan payload.",
      "The current route id is temporary and not a final backend identifier.",
    ],
  };
}

export function selectHistoryModel(scanResult: ScanResult) {
  const intelligence: HistoricalIntelligenceSummary =
    scanResult.history_context.historical_intelligence_summary ?? {};
  const metadata = intelligence.metadata ?? {};
  const signalQuality = intelligence.signal_quality_summary ?? {};
  const featureSummary = intelligence.feature_summary ?? {};

  return {
    summaryCards: [
      { label: "Runs Analyzed", value: metadata.runs_analyzed ?? 0 },
      { label: "Signals Analyzed", value: metadata.signals_analyzed ?? 0 },
      { label: "History Available", value: metadata.history_available ? "Yes" : "No" },
      {
        label: "Latest Run",
        value: metadata.latest_run_timestamp ?? "No history yet",
      },
    ],
    recentPatterns: signalQuality.recurring_high_quality_patterns ?? [],
    topTickers: signalQuality.most_frequent_qualified_tickers ?? [],
    topStrategies: signalQuality.most_frequent_qualified_strategies ?? [],
    topPairs: featureSummary.average_adjusted_score_by_ticker_strategy_pair ?? [],
  };
}

export function selectDailySummaryModel(scanResult: ScanResult) {
  const diagnostics = scanDiagnostics(scanResult);
  const summary: DailySummary = scanResult.daily_summary ?? {};

  return {
    headline: {
      profile: summary.profile ?? scanResult.scan_metadata.profile,
      tickerGroup: summary.ticker_group ?? scanResult.scan_metadata.ticker_group,
      qualifiedCount: summary.qualified_count ?? scanResult.summary.qualified_count,
      nearMissCount: summary.near_miss_count ?? scanResult.summary.near_miss_count,
      alertsCount: summary.alerts_count ?? scanResult.alerts.length,
      executionTimeSeconds:
        summary.execution_time_seconds ?? scanResult.scan_metadata.execution_time_seconds,
    },
    topOpportunity: summary.top_overall ?? scanResult.summary.top_overall,
    alertSignals: [
      { label: "Stable Alerts", value: summary.stable_alert_count ?? 0 },
      { label: "Emerging Alerts", value: summary.emerging_alert_count ?? 0 },
      { label: "New Alerts", value: summary.new_alert_count ?? 0 },
    ],
    mostStableAlert: summary.most_stable_alert ?? null,
    notes: [
      (diagnostics.missing_tickers ?? []).length > 0
        ? `Missing tickers: ${(diagnostics.missing_tickers ?? []).join(", ")}`
        : null,
      (diagnostics.provider_errors ?? []).length > 0
        ? "Provider errors were reported in the latest scan."
        : null,
    ].filter(Boolean) as string[],
  };
}

export function selectPortfolioModel(scanResult: ScanResult) {
  const portfolio: PortfolioSummary = scanResult.portfolio_summary ?? {};
  const exposure = portfolio.exposure ?? {};
  const positionSizing = portfolio.position_sizing ?? {};
  const decision = portfolio.decision ?? {};

  return {
    summaryCards: [
      {
        label: "Qualified Trades",
        value: exposure.metadata?.qualified_trade_count ?? scanResult.summary.qualified_count,
      },
      {
        label: "Fits Budget",
        value: positionSizing.summary?.fits_budget_count ?? 0,
      },
      {
        label: "Oversized",
        value: positionSizing.summary?.oversized_count ?? 0,
      },
      {
        label: "Portfolio Posture",
        value: decision.posture_label ?? "Portfolio View",
      },
    ],
    exposureNotes: exposure.notes ?? [],
    topTickerConcentration: exposure.qualified?.top_ticker_concentration ?? [],
    directionalExposure: exposure.qualified?.directional_exposure ?? [],
    positions: positionSizing.trade_sizing ?? [],
    warnings: positionSizing.warnings ?? [],
    interpretation: decision.interpretation ?? [],
    cautions: decision.cautions ?? [],
    keySignals: decision.key_portfolio_signals ?? [],
  };
}
