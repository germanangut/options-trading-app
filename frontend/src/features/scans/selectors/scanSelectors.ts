import type {
  AlertItem,
  DailySummary,
  HistoricalIntelligenceSummary,
  PortfolioSummary,
  QualifiedTradeRow,
  ScanResult,
} from "../../../types/api";


const HIGH_PROVIDER_LATENCY_MS = 750;
const HIGH_PROVIDER_DURATION_MS = 4000;
const LOW_CACHE_HIT_RATE = 0.35;

export type SessionDiagnosticsTone = "success" | "info" | "warning" | "danger";

export type SessionDiagnosticsSection = {
  title: string;
  tone: SessionDiagnosticsTone;
  message: string;
  notes: string[];
};

export type SessionDiagnosticsModel = {
  statusTone: "success" | "info" | "warning";
  statusLabel: string;
  statusDetail: string;
  triggerLabel: string;
  sections: SessionDiagnosticsSection[];
};


function arrayOrEmpty<T>(value: T[] | null | undefined) {
  return Array.isArray(value) ? value : [];
}

function objectOrEmpty<T extends Record<string, unknown>>(value: T | null | undefined) {
  return value && typeof value === "object" ? value : ({} as T);
}


function scanDiagnostics(scanResult: ScanResult) {
  const diagnostics = objectOrEmpty(scanResult?.diagnostics);

  return {
    ...diagnostics,
    missing_tickers: arrayOrEmpty(diagnostics.missing_tickers as string[] | null | undefined),
    provider_errors: arrayOrEmpty(
      diagnostics.provider_errors as Array<Record<string, unknown>> | null | undefined,
    ),
    alerts_export_path: diagnostics.alerts_export_path ?? null,
    top_overall_identity: diagnostics.top_overall_identity ?? null,
    performance: objectOrEmpty(diagnostics.performance as Record<string, unknown> | null | undefined),
    cache: objectOrEmpty(diagnostics.cache as Record<string, unknown> | null | undefined),
  };
}

function numberOrNull(value: unknown) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : null;
}

function resolveFailedTickerCount(
  providerErrors: Array<Record<string, unknown>>,
  missingTickers: string[],
  performance: Record<string, unknown>,
  partialResult: boolean,
) {
  const failedTickerCount = numberOrNull(performance.failed_ticker_count);
  if (failedTickerCount !== null && failedTickerCount >= 0) {
    return failedTickerCount;
  }

  if (providerErrors.length > 0 || missingTickers.length > 0) {
    return Math.max(providerErrors.length, missingTickers.length);
  }

  return partialResult ? 1 : 0;
}

function resolveCacheHitRate(diagnostics: ReturnType<typeof scanDiagnostics>) {
  const performance = (diagnostics.performance ?? {}) as Record<string, unknown>;
  const cache = (diagnostics.cache ?? {}) as Record<string, unknown>;
  const marketDataCache = (cache.market_data ?? {}) as Record<string, unknown>;

  return numberOrNull(performance.cache_hit_rate ?? cache.cache_hit_rate ?? marketDataCache.hit_rate);
}

function degradedRetrievalNotes(diagnostics: ReturnType<typeof scanDiagnostics>) {
  const performance = (diagnostics.performance ?? {}) as Record<string, unknown>;
  const notes: string[] = [];
  const retryCount = numberOrNull(performance.retry_count) ?? 0;
  const averageProviderLatencyMs = numberOrNull(performance.average_provider_latency_ms);
  const providerDurationMs = numberOrNull(performance.provider_duration_ms);
  const cacheHitRate = resolveCacheHitRate(diagnostics);

  if (retryCount > 0) {
    notes.push(`Data retrieved with retries (${retryCount}).`);
  }

  if (
    (averageProviderLatencyMs !== null && averageProviderLatencyMs >= HIGH_PROVIDER_LATENCY_MS)
    || (providerDurationMs !== null && providerDurationMs >= HIGH_PROVIDER_DURATION_MS)
  ) {
    notes.push("Provider response slower than usual.");
  }

  if (cacheHitRate !== null && cacheHitRate < LOW_CACHE_HIT_RATE) {
    notes.push(`Cache reuse lower than usual (${(cacheHitRate * 100).toFixed(0)}% hit rate).`);
  }

  return notes;
}


export function selectScanReliabilityNotice(scanResult?: ScanResult | null) {
  if (!scanResult) {
    return null;
  }

  const diagnostics = scanDiagnostics(scanResult);
  const providerErrors = diagnostics.provider_errors;
  const missingTickers = diagnostics.missing_tickers;
  const performance = diagnostics.performance;
  const cache = diagnostics.cache;
  const providerDurationMs = Number(performance.provider_duration_ms ?? NaN);
  const retryCount = Number(performance.retry_count ?? 0);
  const retryExhausted = Boolean(performance.retry_exhausted);
  const failedTickerCount = resolveFailedTickerCount(
    providerErrors,
    missingTickers,
    performance as Record<string, unknown>,
    Boolean(diagnostics.partial_result),
  );
  const degradedNotes = degradedRetrievalNotes(diagnostics);
  const providerDurationNote = Number.isFinite(providerDurationMs)
    ? `Provider phase completed in ${(providerDurationMs / 1000).toFixed(2)}s.`
    : null;
  const aggregateCacheHit = Boolean((cache as Record<string, unknown>).market_data && ((cache as Record<string, { hit?: boolean }>).market_data?.hit));

  if (providerErrors.length > 0 || missingTickers.length > 0 || diagnostics.partial_result) {
    return {
      tone: "warning" as const,
      title: "Partial results available",
      message: `${failedTickerCount} ticker(s) failed or were unavailable during the latest scan. Successful results remain visible, but coverage is incomplete.`,
      notes: [
        failedTickerCount > 0 ? `Failed or unavailable tickers: ${failedTickerCount}` : null,
        `Provider errors: ${providerErrors.length}`,
        missingTickers.length > 0 ? `Missing: ${missingTickers.join(", ")}` : null,
        retryCount > 0 ? `Retries attempted: ${retryCount}` : null,
        retryExhausted ? "Some provider requests exhausted their retry budget." : null,
        providerDurationNote,
        aggregateCacheHit ? "This response reused short-lived cached market data." : null,
        ...degradedNotes,
      ].filter(Boolean) as string[],
    };
  }

  if (degradedNotes.length > 0) {
    return {
      tone: "info" as const,
      title: "Degraded retrieval signals",
      message: "The latest scan completed, but data retrieval needed extra work. Review these signals before treating the run as fully healthy.",
      notes: [
        ...degradedNotes,
        providerDurationNote,
        aggregateCacheHit ? "This response reused short-lived cached market data." : null,
      ].filter(Boolean) as string[],
    };
  }

  return null;
}

export function selectScanPerformanceSummary(scanResult?: ScanResult | null) {
  if (!scanResult) {
    return null;
  }

  const diagnostics = scanDiagnostics(scanResult);
  const performance = diagnostics.performance ?? {};
  const scanDurationMs = Number(performance.scan_duration_ms ?? NaN);
  const successfulTickerCount = Number(performance.successful_ticker_count ?? NaN);
  const failedTickerCount = Number(performance.failed_ticker_count ?? NaN);
  const totalProviderCalls = Number(performance.total_provider_calls ?? NaN);
  const averageProviderLatencyMs = Number(performance.average_provider_latency_ms ?? NaN);
  const retryLatencyImpactMs = Number(performance.retry_latency_impact_ms ?? NaN);
  const estimatedCacheSavedDurationMs = Number(
    performance.estimated_cache_saved_duration_ms ?? NaN,
  );

  if (
    !Number.isFinite(scanDurationMs)
    && !Number.isFinite(successfulTickerCount)
    && !Number.isFinite(failedTickerCount)
  ) {
    return null;
  }

  return {
    title: "Performance summary",
    message: Number.isFinite(scanDurationMs)
      ? `Latest scan completed in ${(scanDurationMs / 1000).toFixed(2)}s.`
      : "Latest scan performance metrics are available.",
    notes: [
      Number.isFinite(successfulTickerCount) && Number.isFinite(failedTickerCount)
        ? `Tickers processed successfully: ${successfulTickerCount}. Failed: ${failedTickerCount}.`
        : null,
      Number.isFinite(totalProviderCalls)
        ? `Provider calls issued: ${totalProviderCalls}.`
        : null,
      Number.isFinite(averageProviderLatencyMs)
        ? `Average provider latency: ${averageProviderLatencyMs.toFixed(2)}ms.`
        : null,
      Number.isFinite(retryLatencyImpactMs) && retryLatencyImpactMs > 0
        ? `Retry backoff added ${retryLatencyImpactMs.toFixed(2)}ms.`
        : null,
      Number.isFinite(estimatedCacheSavedDurationMs) && estimatedCacheSavedDurationMs > 0
        ? `Cache reuse saved an estimated ${estimatedCacheSavedDurationMs.toFixed(2)}ms.`
        : null,
    ].filter(Boolean) as string[],
  };
}

export function selectSessionDiagnosticsModel(scanResult?: ScanResult | null): SessionDiagnosticsModel | null {
  if (!scanResult) {
    return null;
  }

  const diagnostics = scanDiagnostics(scanResult);
  const performance = diagnostics.performance ?? {};
  const reliabilityNotice = selectScanReliabilityNotice(scanResult);
  const performanceSummary = selectScanPerformanceSummary(scanResult);
  const degradedNotes = degradedRetrievalNotes(diagnostics);
  const providerDurationMs = numberOrNull(performance.provider_duration_ms);
  const averageProviderLatencyMs = numberOrNull(performance.average_provider_latency_ms);
  const totalProviderCalls = numberOrNull(performance.total_provider_calls);
  const retryCount = numberOrNull(performance.retry_count) ?? 0;
  const retryLatencyImpactMs = numberOrNull(performance.retry_latency_impact_ms);
  const estimatedCacheSavedDurationMs = numberOrNull(performance.estimated_cache_saved_duration_ms);
  const cacheHitRate = resolveCacheHitRate(diagnostics);
  const partialCoverage = Boolean(diagnostics.partial_result)
    || diagnostics.provider_errors.length > 0
    || diagnostics.missing_tickers.length > 0;

  let statusTone: "success" | "info" | "warning" = "success";
  let statusLabel = "Healthy";
  let statusDetail = "Latest run operational checks look normal.";

  if (partialCoverage) {
    statusTone = "warning";
    statusLabel = "Degraded";
    statusDetail = "Coverage is incomplete in the latest run.";
  } else if (degradedNotes.includes("Provider response slower than usual.")) {
    statusTone = "warning";
    statusLabel = "Provider slower than usual";
    statusDetail = "The latest run completed, but provider timing exceeded the normal range.";
  } else if (reliabilityNotice) {
    statusTone = "info";
    statusLabel = "Degraded";
    statusDetail = "The latest run completed with retrieval caveats worth reviewing.";
  }

  const retrievalSection: SessionDiagnosticsSection = reliabilityNotice
    ? {
        title: reliabilityNotice.title,
        tone: reliabilityNotice.tone,
        message: reliabilityNotice.message,
        notes: reliabilityNotice.notes,
      }
    : {
        title: "Retrieval health",
        tone: "success" as const,
        message: "The latest run completed without degraded retrieval signals.",
        notes: [] as string[],
      };

  const providerTimingNotes = [
    providerDurationMs !== null
      ? `Provider phase completed in ${(providerDurationMs / 1000).toFixed(2)}s.`
      : null,
    averageProviderLatencyMs !== null
      ? `Average provider latency: ${averageProviderLatencyMs.toFixed(2)}ms.`
      : null,
    totalProviderCalls !== null
      ? `Provider calls issued: ${totalProviderCalls}.`
      : null,
  ].filter(Boolean) as string[];

  const retryAndCacheNotes = [
    retryCount > 0 ? `Retries attempted: ${retryCount}.` : null,
    retryLatencyImpactMs !== null && retryLatencyImpactMs > 0
      ? `Retry backoff added ${retryLatencyImpactMs.toFixed(2)}ms.`
      : null,
    cacheHitRate !== null ? `Cache hit rate: ${(cacheHitRate * 100).toFixed(0)}%.` : null,
    estimatedCacheSavedDurationMs !== null && estimatedCacheSavedDurationMs > 0
      ? `Cache reuse saved an estimated ${estimatedCacheSavedDurationMs.toFixed(2)}ms.`
      : null,
  ].filter(Boolean) as string[];

  return {
    statusTone,
    statusLabel,
    statusDetail,
    triggerLabel: "View diagnostics",
    sections: [
      retrievalSection,
      {
        title: "Provider timing",
        tone: providerTimingNotes.length > 0 ? "info" : "success",
        message: providerTimingNotes.length > 0
          ? "Latest provider timing for the current session."
          : "No provider timing metrics were returned for the latest run.",
        notes: providerTimingNotes,
      },
      {
        title: "Retry and cache notes",
        tone: retryAndCacheNotes.length > 0 ? "info" : "success",
        message: retryAndCacheNotes.length > 0
          ? "Operational retry and cache metadata for the latest run."
          : "No retry or cache caveats were recorded for the latest run.",
        notes: retryAndCacheNotes,
      },
      {
        title: "Session metadata",
        tone: "info" as const,
        message: "Current latest-run operational metadata.",
        notes: [
          scanResult.scan_metadata?.scan_id ? `Scan ID: ${scanResult.scan_metadata.scan_id}` : null,
          scanResult.scan_metadata?.generated_at ? `Generated at: ${scanResult.scan_metadata.generated_at}` : null,
          scanResult.scan_metadata?.provider ? `Provider: ${scanResult.scan_metadata.provider}` : null,
          scanResult.scan_metadata?.profile ? `Profile: ${scanResult.scan_metadata.profile}` : null,
          scanResult.scan_metadata?.ticker_group ? `Ticker group: ${scanResult.scan_metadata.ticker_group}` : null,
          scanResult.scan_metadata?.execution_time_seconds !== undefined
            ? `Execution time: ${Number(scanResult.scan_metadata.execution_time_seconds).toFixed(2)}s.`
            : null,
          performanceSummary?.message ?? null,
        ].filter(Boolean) as string[],
      },
    ],
  };
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
  const summary = objectOrEmpty(scanResult?.summary);
  const alerts = arrayOrEmpty(scanResult?.alerts);
  const topOpportunity = (summary.top_overall as QualifiedTradeRow | null | undefined) ?? null;

  return {
    kpis: [
      { label: "Qualified Trades", value: Number(summary.qualified_count ?? 0) },
      { label: "Near Misses", value: Number(summary.near_miss_count ?? 0) },
      { label: "Alerts", value: alerts.length },
      {
        label: "Runtime",
        value: scanResult.scan_metadata?.execution_time_seconds ?? null,
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
  const qualifiedTrades = arrayOrEmpty(scanResult?.qualified_trades);

  return {
    total: qualifiedTrades.length,
    rows: qualifiedTrades.map((trade) => ({
      id: buildTemporaryTradeId(trade),
      trade,
      score: fallbackScore(trade),
    })),
  };
}

export function selectAlertsModel(scanResult: ScanResult) {
  const diagnostics = scanDiagnostics(scanResult);
  const performance = (diagnostics.performance ?? {}) as Record<string, unknown>;
  const alerts = arrayOrEmpty(scanResult?.alerts);
  const qualifiedCount = Number(scanResult?.summary?.qualified_count ?? 0);
  const failedTickerCount = resolveFailedTickerCount(
    diagnostics.provider_errors,
    diagnostics.missing_tickers,
    performance,
    Boolean(diagnostics.partial_result),
  );
  const partialCoverage = Boolean(diagnostics.partial_result)
    || diagnostics.provider_errors.length > 0
    || diagnostics.missing_tickers.length > 0;

  const cleanEmptyState = qualifiedCount > 0
    ? {
        title: "No alerts this run",
        message: "Qualified trades were found, but none passed the tighter alert filters. Alerts surface only the strongest candidates — not every qualified trade. To see more signal volume, adjust score and signal-history filters in Expert mode.",
      }
    : {
        title: "No alerts this run",
        message: "No qualified trades or alerts were produced in this run. Review Overview and Daily Summary, or widen the scan before adjusting alert filters.",
      };

  return {
    total: alerts.length,
    providerErrors: diagnostics.provider_errors,
    missingTickers: diagnostics.missing_tickers,
    partialResult: Boolean(diagnostics.partial_result),
    failedTickerCount,
    partialNotice: partialCoverage
      ? {
          title: "Partial results available",
          message: `${failedTickerCount} ticker(s) failed or were unavailable during the latest scan, so the alert list may be incomplete.`,
        }
      : null,
    emptyState: partialCoverage
      ? {
          title: "No alerts under partial coverage",
          message: "Some tickers were unavailable during the scan, so review diagnostics before treating this as a fully clean market pass.",
        }
      : cleanEmptyState,
    rows: alerts.map((alert: AlertItem) => ({
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

  const allTrades = [
    ...arrayOrEmpty(scanResult?.qualified_trades),
    ...arrayOrEmpty(scanResult?.alerts),
  ];
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
  const historyContext = objectOrEmpty(scanResult?.history_context);
  const intelligence: HistoricalIntelligenceSummary =
    (historyContext.historical_intelligence_summary as HistoricalIntelligenceSummary | undefined) ?? {};
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
  const summary: DailySummary = scanResult?.daily_summary ?? {};
  const metadata = objectOrEmpty(scanResult?.scan_metadata);
  const baseSummary = objectOrEmpty(scanResult?.summary);
  const alerts = arrayOrEmpty(scanResult?.alerts);

  return {
    headline: {
      profile: summary.profile ?? metadata.profile,
      tickerGroup: summary.ticker_group ?? metadata.ticker_group,
      qualifiedCount: summary.qualified_count ?? Number(baseSummary.qualified_count ?? 0),
      nearMissCount: summary.near_miss_count ?? Number(baseSummary.near_miss_count ?? 0),
      alertsCount: summary.alerts_count ?? alerts.length,
      executionTimeSeconds:
        summary.execution_time_seconds ?? metadata.execution_time_seconds ?? null,
    },
    topOpportunity: summary.top_overall ?? baseSummary.top_overall ?? null,
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
  const baseSummary = objectOrEmpty(scanResult?.summary);

  return {
    summaryCards: [
      {
        label: "Qualified Trades",
        value: exposure.metadata?.qualified_trade_count ?? Number(baseSummary.qualified_count ?? 0),
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
    exposureNotes: arrayOrEmpty(exposure.notes),
    topTickerConcentration: arrayOrEmpty(exposure.qualified?.top_ticker_concentration),
    directionalExposure: arrayOrEmpty(exposure.qualified?.directional_exposure),
    positions: arrayOrEmpty(positionSizing.trade_sizing),
    warnings: arrayOrEmpty(positionSizing.warnings),
    interpretation: arrayOrEmpty(decision.interpretation),
    cautions: arrayOrEmpty(decision.cautions),
    keySignals: arrayOrEmpty(decision.key_portfolio_signals),
  };
}
