import {
  PROFILE_OPTIONS,
  STRATEGY_OPTIONS,
  TICKER_GROUP_OPTIONS,
} from "../../../lib/constants";
import {
  formatCurrency,
  formatNumber,
  formatTradeLabel,
  formatValueLabel,
} from "../../../lib/formatters";
import type {
  HistoricalIntelligenceSummary,
  HistoryMetadata,
  PortfolioSummary,
  ScanRequest,
  ScanResult,
  TradeDetailResponse,
  TradeIdentityFields,
} from "../../../types/api";


type ChipTone = "neutral" | "accent" | "success" | "warning" | "danger";

type WorkflowMode = "guided" | "expert";


const profileLookup = Object.fromEntries(PROFILE_OPTIONS.map((option) => [option.value, option.label]));
const tickerLookup = Object.fromEntries(TICKER_GROUP_OPTIONS.map((option) => [option.value, option.label]));
const strategyLookup = Object.fromEntries(STRATEGY_OPTIONS.map((option) => [option.value, option.label]));


function arrayOrEmpty<T>(value: T[] | null | undefined) {
  return Array.isArray(value) ? value : [];
}

function objectOrEmpty<T extends Record<string, unknown>>(value: T | null | undefined) {
  return value && typeof value === "object" ? value : ({} as T);
}


function fallbackScore(trade: Pick<TradeIdentityFields, "adjusted_score" | "score">) {
  return trade.adjusted_score ?? trade.score ?? null;
}


function thresholdDelta(value: number | string | null | undefined, threshold: number | null | undefined) {
  if (value === null || value === undefined || value === "" || threshold === null || threshold === undefined) {
    return null;
  }

  const numericValue = Number(value);
  const numericThreshold = Number(threshold);
  if (Number.isNaN(numericValue) || Number.isNaN(numericThreshold)) {
    return null;
  }

  const delta = numericValue - numericThreshold;
  return `${delta >= 0 ? "+" : ""}${delta.toFixed(1)} vs floor`;
}


function toneFromDirection(direction?: string | null): ChipTone {
  const normalized = String(direction ?? "").trim().toLowerCase();
  if (normalized === "bullish") {
    return "success";
  }
  if (normalized === "bearish") {
    return "warning";
  }
  return "neutral";
}


function toneFromStability(value?: string | null): ChipTone {
  const normalized = String(value ?? "").trim().toLowerCase();
  if (normalized === "stable") {
    return "success";
  }
  if (normalized === "emerging") {
    return "warning";
  }
  if (normalized === "new") {
    return "accent";
  }
  return "neutral";
}


function labelFromValue(value?: string | null, fallback = "-") {
  const raw = String(value ?? "").trim();
  return raw ? formatValueLabel(raw) : fallback;
}


function describeProfileIntent(profile?: string | null) {
  switch (String(profile ?? "").trim().toLowerCase()) {
    case "conservative":
      return "defensive premium";
    case "aggressive":
      return "higher-conviction premium";
    case "balanced":
    default:
      return "balanced premium";
  }
}


function describeTickerUniverse(tickerGroup?: string | null) {
  switch (String(tickerGroup ?? "").trim().toLowerCase()) {
    case "tech":
      return "big tech";
    case "index":
      return "index leaders";
    case "mixed":
      return "a mixed watchlist";
    default:
      return labelFromValue(tickerGroup, "the current watchlist").toLowerCase();
  }
}


function describeDirectionIntent(strategyKeys: string[]) {
  const hasBull = strategyKeys.includes("bull_put_spread");
  const hasBear = strategyKeys.includes("bear_call_spread");

  if (hasBull && hasBear) {
    return "either bullish or bearish setups";
  }

  if (hasBull) {
    return "bullish setups";
  }

  if (hasBear) {
    return "bearish setups";
  }

  return "the currently selected setup types";
}


function describeDteWindow(min?: number | null, max?: number | null) {
  if (typeof min !== "number" || typeof max !== "number") {
    return "within the current expiration window";
  }

  if (max <= 14) {
    return "expiring soon, around 1-2 weeks out";
  }

  if (min >= 20 && max <= 35) {
    return "expiring in about 3-5 weeks";
  }

  if (min >= 35) {
    return "expiring later, around 5-8 weeks out";
  }

  return `expiring in about ${Math.max(1, Math.round(min / 7))}-${Math.max(1, Math.round(max / 7))} weeks`;
}


function describeQualityIntent(minScore?: number | null) {
  if (typeof minScore !== "number") {
    return "the current quality filter";
  }

  if (minScore >= 75) {
    return "strict quality filtering";
  }

  if (minScore <= 55) {
    return "a broader opportunity filter";
  }

  return "moderate quality filtering";
}


function describeConsistencyIntent(minConsistency?: number | null) {
  if (typeof minConsistency !== "number") {
    return "keeping the current signal-history preference";
  }

  if (minConsistency >= 5) {
    return "leaning on setups that have shown up repeatedly";
  }

  if (minConsistency <= 1) {
    return "staying open to fresher signals";
  }

  return "preferring setups that have appeared before";
}


function describeFreshnessLabel(stabilityLevel?: string | null, stabilityCount?: number | null) {
  if (typeof stabilityCount === "number" && stabilityCount >= 3) {
    return `Seen ${stabilityCount} times`;
  }

  const normalized = String(stabilityLevel ?? "").trim().toLowerCase();
  if (normalized === "stable") {
    return "Repeated signal";
  }
  if (normalized === "emerging") {
    return "Building history";
  }
  if (normalized === "new") {
    return "Fresh signal";
  }

  return "Current setup";
}


function summarizeDirection(strategyKeys: string[]) {
  const hasBull = strategyKeys.includes("bull_put_spread");
  const hasBear = strategyKeys.includes("bear_call_spread");

  if (hasBull && hasBear) {
    return "either direction";
  }

  if (hasBull) {
    return "bullish direction";
  }

  if (hasBear) {
    return "bearish direction";
  }

  return "current direction filters";
}


function summarizeTimingWindow(min?: number | null, max?: number | null) {
  if (typeof min !== "number" || typeof max !== "number") {
    return "the current timing window";
  }

  if (max <= 14) {
    return "1-2 weeks";
  }

  if (min >= 20 && max <= 35) {
    return "3-5 weeks";
  }

  if (min >= 35) {
    return "5-8 weeks";
  }

  return `${Math.max(1, Math.round(min / 7))}-${Math.max(1, Math.round(max / 7))} weeks`;
}


function summarizeBreadth(minScore?: number | null) {
  if (typeof minScore !== "number") {
    return "current filtering";
  }

  if (minScore >= 75) {
    return "stricter filtering";
  }

  if (minScore <= 55) {
    return "broader filtering";
  }

  return "moderate filtering";
}


function summarizeFamiliarity(minConsistency?: number | null) {
  if (typeof minConsistency !== "number") {
    return "current familiarity settings";
  }

  if (minConsistency >= 5) {
    return "repeat setups";
  }

  if (minConsistency <= 1) {
    return "fresh setups";
  }

  return "some history";
}


function buildSidebarPlanSummary(request: ScanRequest) {
  const profile = profileLookup[request.profile] ?? labelFromValue(request.profile);
  const market = tickerLookup[request.ticker_group] ?? labelFromValue(request.ticker_group);

  return [
    `${profile} scan across ${market} for ${summarizeDirection(request.selected_strategy_keys)}.`,
    `Expiring in ${summarizeTimingWindow(request.dte_min, request.dte_max)} with ${summarizeBreadth(request.min_score)} and ${summarizeFamiliarity(request.min_consistency)}.`,
  ];
}


function buildTradeDetailPath(scanId?: string | null, tradeId?: string | null) {
  if (!scanId || !tradeId) {
    return null;
  }

  return `/scans/${encodeURIComponent(scanId)}/trades/${encodeURIComponent(tradeId)}`;
}


function currentScanThresholds(scanResult: ScanResult) {
  return {
    minScore:
      scanResult.scan_metadata.alert_thresholds?.min_score ??
      scanResult.scan_metadata.request?.min_score ??
      null,
    minPop: scanResult.scan_metadata.request?.min_pop ?? null,
    minRor: scanResult.scan_metadata.request?.min_ror ?? null,
  };
}


function firstNonEmpty(values: Array<string | null | undefined>) {
  return values.find((value) => String(value ?? "").trim()) ?? null;
}


function portfolioPosture(portfolioSummary: PortfolioSummary | undefined) {
  const decision = portfolioSummary?.decision ?? {};
  const exposure = portfolioSummary?.exposure ?? {};
  const topTicker = exposure.qualified?.top_ticker_concentration?.[0] ?? null;
  return {
    posture: decision.posture_label ?? "Portfolio View",
    interpretation: decision.interpretation ?? [],
    keySignals: decision.key_portfolio_signals ?? [],
    cautions: decision.cautions ?? [],
    topTicker,
  };
}


export function selectOverviewCockpitModel(scanResult: ScanResult) {
  const diagnostics = objectOrEmpty(scanResult.diagnostics) as ScanResult["diagnostics"];
  const qualifiedTrades = arrayOrEmpty(scanResult.qualified_trades);
  const alerts = arrayOrEmpty(scanResult.alerts);
  const summary = objectOrEmpty(scanResult.summary);
  const topTrade = (summary.top_overall as TradeIdentityFields | null | undefined) ?? qualifiedTrades[0] ?? null;
  const providerErrors = arrayOrEmpty(diagnostics.provider_errors).length;
  const missingTickers = arrayOrEmpty(diagnostics.missing_tickers);
  const qualifiedCount = Number(summary.qualified_count ?? qualifiedTrades.length);
  const alertsCount = alerts.length;
  const historyContext = objectOrEmpty(scanResult.history_context);
  const historySummary = (historyContext.historical_intelligence_summary ?? {}) as HistoricalIntelligenceSummary;
  const historyMetadata: HistoryMetadata = historySummary.metadata ?? {};
  const recurringPatterns = arrayOrEmpty(
    historySummary.signal_quality_summary?.recurring_high_quality_patterns,
  );
  const portfolio = portfolioPosture(scanResult.portfolio_summary);
  const performance = (diagnostics.performance ?? {}) as Record<string, unknown>;
  const cache = (diagnostics.cache ?? {}) as Record<string, unknown>;

  let trustTone: "info" | "success" | "warning" = "info";
  let trustTitle = "Healthy run, no strong candidates";
  let trustMessage = "The current scan completed cleanly, but nothing surfaced strongly under the active thresholds.";

  if (providerErrors > 0) {
    trustTone = "warning";
    trustTitle = "Provider issues detected";
    trustMessage = "This run reported provider errors, so treat candidate coverage as partial before making a decision.";
  } else if (missingTickers.length > 0) {
    trustTone = "warning";
    trustTitle = "Partial market coverage";
    trustMessage = `${missingTickers.length} ticker(s) were unavailable, so the scan is directionally useful but not fully complete.`;
  } else if (qualifiedCount > 0 || alertsCount > 0) {
    trustTone = "success";
    trustTitle = "Healthy run with actionable output";
    trustMessage = "The scan completed without coverage issues and returned candidates worth review.";
  }

  return {
    snapshot: {
      title: topTrade ? formatTradeLabel(topTrade) : "No top opportunity",
      subtitle: topTrade
        ? `Top current candidate under the active ${scanResult.scan_metadata.profile} profile.`
        : "No trade currently leads the latest scan.",
      metrics: [
        { label: "Qualified", value: qualifiedCount, tone: "success" as const },
        { label: "Alerts", value: alerts.length, tone: "warning" as const },
        {
          label: "Stable Names",
          value: qualifiedTrades.filter((trade) => trade.stability_level === "stable").length,
          tone: "neutral" as const,
        },
        {
          label: "Runtime",
          value: scanResult.scan_metadata.execution_time_seconds !== null
            ? `${Number(scanResult.scan_metadata.execution_time_seconds).toFixed(2)}s`
            : "-",
          tone: "accent" as const,
        },
      ],
      direction: labelFromValue(topTrade?.directional_bias, "Neutral"),
      directionTone: toneFromDirection(topTrade?.directional_bias),
      href: buildTradeDetailPath(scanResult.scan_metadata.scan_id, topTrade?.trade_id),
      story: [
        qualifiedCount > 0
          ? `${qualifiedCount} qualified idea(s) cleared the current run and should be reviewed in ranked order.`
          : "No qualified ideas cleared the current run, so scan health matters more than raw volume today.",
        alertsCount > 0
          ? `${alertsCount} alert(s) also surfaced, which may widen the review set beyond the shortlist.`
          : "No separate alert pressure is building beyond the ranked board right now.",
        trustTone === "warning"
          ? "Coverage caveats are present, so treat this cockpit as directional rather than complete."
          : "Coverage appears healthy, so the top opportunity can be reviewed with higher confidence.",
      ],
    },
    topTradePreview: topTrade
      ? {
          title: formatTradeLabel(topTrade),
          summary: firstNonEmpty([
            topTrade.decision_summary,
            topTrade.status_reason,
            topTrade.explanation,
          ]),
          metrics: [
            { label: "POP", value: formatNumber(topTrade.POP), tone: "success" as const },
            { label: "ROR", value: formatNumber(topTrade.ROR), tone: "warning" as const },
            {
              label: "Score",
              value: formatNumber(fallbackScore(topTrade)),
              detail: thresholdDelta(fallbackScore(topTrade), currentScanThresholds(scanResult).minScore),
              tone: "accent" as const,
            },
          ],
          notes: [
            `Expiration ${topTrade.expiration_date ?? "-"} • DTE ${formatNumber(topTrade.DTE)}`,
            `Premium context ${labelFromValue(topTrade.volatility_context, "Unspecified")}`,
            `${labelFromValue(topTrade.directional_bias, "Neutral")} posture with ${labelFromValue(topTrade.stability_level, "current").toLowerCase()} signal context.`,
          ],
          href: buildTradeDetailPath(scanResult.scan_metadata.scan_id, topTrade.trade_id),
        }
      : null,
    trust: {
      tone: trustTone,
      title: trustTitle,
      message: trustMessage,
      metrics: [
        { label: "Provider", value: scanResult.scan_metadata.provider ?? "Unknown" },
        { label: "Missing", value: missingTickers.length },
        { label: "Errors", value: providerErrors },
      ],
      notes: [
        missingTickers.length > 0 ? `Missing tickers: ${missingTickers.join(", ")}` : null,
        providerErrors > 0 ? "Provider errors are present in the latest scan diagnostics." : null,
        typeof performance.provider_duration_ms === "number"
          ? `Provider duration ${(Number(performance.provider_duration_ms) / 1000).toFixed(2)}s.`
          : null,
        ((cache.market_data as { hit?: boolean } | undefined)?.hit)
          ? "The latest scan reused short-lived cached market data."
          : null,
      ].filter(Boolean) as string[],
    },
    portfolio: {
      posture: portfolio.posture,
      interpretation: portfolio.interpretation,
      keySignals: portfolio.keySignals,
      cautions: portfolio.cautions,
      concentration: portfolio.topTicker
        ? `${portfolio.topTicker.ticker} ${portfolio.topTicker.share_pct ?? 0}% of current qualified set`
        : "No concentration signal returned.",
      summaryLine: portfolio.topTicker
        ? `${portfolio.topTicker.ticker} currently leads concentration inside the qualified set.`
        : "Portfolio posture is available, but no single ticker concentration was returned.",
    },
    history: {
      runsAnalyzed: historyMetadata.runs_analyzed ?? 0,
      signalsAnalyzed: historyMetadata.signals_analyzed ?? 0,
      latestRun: historyMetadata.latest_run_timestamp ?? "No history yet",
      recurringPatterns: recurringPatterns.slice(0, 3),
      notes: [
        recurringPatterns.length > 0
          ? `${recurringPatterns.length} recurring high-quality pattern(s) are reinforcing this run.`
          : "Stored history is still thin, so this run should be judged mostly on current conditions.",
      ],
    },
    alertsSnapshot: {
      total: alertsCount,
      title: alertsCount > 0 ? "Alert pressure is active" : "No alerts this run",
      notes: alertsCount > 0
        ? [
            `${alertsCount} alert(s) are active in parallel with the ranked board.`,
            qualifiedCount > 0
              ? "Review the shortlist first, then use alerts to expand the review set if needed."
              : "Alerts may be the best secondary review surface when the shortlist is thin.",
          ]
        : qualifiedCount > 0
          ? [
              "Qualified trades were found, but none passed the tighter alert filters.",
              "Alerts surface only the strongest candidates — not every qualified trade.",
              "To see more signal volume, adjust score and signal-history filters in Expert mode.",
            ]
          : [
              "No qualified trades or alerts were produced in this run.",
              "Review Overview and Daily Summary, or widen the scan before adjusting alert filters.",
            ],
    },
    nextActions: [
      { label: "Start with the ranked board", to: "/qualified" },
      { label: "Check whether alerts widen the set", to: "/alerts" },
      { label: "Confirm portfolio fit before sizing", to: "/portfolio" },
    ],
  };
}


export function selectQualifiedBoardModel(scanResult: ScanResult) {
  const diagnostics = objectOrEmpty(scanResult.diagnostics) as ScanResult["diagnostics"];
  const qualifiedTrades = arrayOrEmpty(scanResult.qualified_trades);
  const thresholds = currentScanThresholds(scanResult);
  const portfolio = portfolioPosture(scanResult.portfolio_summary);
  const concentrationRows = arrayOrEmpty(scanResult.portfolio_summary?.exposure?.qualified?.top_ticker_concentration);
  const caveats = [
    arrayOrEmpty(diagnostics.provider_errors).length > 0
      ? "Provider issues were reported in this run, so the ranked board may be incomplete."
      : null,
    arrayOrEmpty(diagnostics.missing_tickers).length > 0
      ? `Missing tickers: ${arrayOrEmpty(diagnostics.missing_tickers).join(", ")}`
      : null,
    portfolio.topTicker?.share_pct && portfolio.topTicker.share_pct >= 30
      ? `${portfolio.topTicker.ticker} represents ${portfolio.topTicker.share_pct}% of the current qualified set.`
      : null,
  ].filter(Boolean) as string[];

  return {
    summary: [
      { label: "Qualified", value: qualifiedTrades.length, tone: "success" as const },
      {
        label: "Stable",
        value: qualifiedTrades.filter((trade) => trade.stability_level === "stable").length,
        tone: "neutral" as const,
      },
      {
        label: "Score Floor",
        value: thresholds.minScore ?? "-",
        tone: "accent" as const,
      },
      {
        label: "Portfolio Posture",
        value: portfolio.posture,
        tone: "warning" as const,
      },
    ],
    caveats,
    narrative: [
      qualifiedTrades.length > 0
        ? `Start at the top card first: ${qualifiedTrades.length} idea(s) cleared the active filters.`
        : "This run did not surface any qualified opportunities.",
      thresholds.minScore !== null && thresholds.minScore !== undefined
        ? `The shortlist is using ${describeQualityIntent(thresholds.minScore)}.`
        : "No explicit score floor was returned in the current scan metadata.",
      portfolio.posture ? `Portfolio posture currently reads as ${portfolio.posture.toLowerCase()}.` : null,
    ].filter(Boolean) as string[],
    emptyState: arrayOrEmpty(diagnostics.provider_errors).length > 0
      ? {
          title: "Partial results available",
          message: "Provider failures affected this run. Review alerts and diagnostics before concluding there were no qualified setups.",
        }
      : arrayOrEmpty(diagnostics.missing_tickers).length > 0 || diagnostics.partial_result
        ? {
            title: "Partial results available",
            message: "Some tickers were unavailable during the scan, so this empty board may reflect incomplete market coverage.",
          }
        : {
            title: "No qualified trades",
            message: "The latest scan did not produce any qualified opportunities. If you want a wider review set, broaden the ticker group or relax the score threshold.",
          },
    items: qualifiedTrades.map((trade, index) => {
      const concentration = concentrationRows.find((row) => row.ticker === trade.ticker) ?? null;

      return {
      id: trade.trade_id ?? `${scanResult.scan_metadata.scan_id}-${index}`,
      href: buildTradeDetailPath(scanResult.scan_metadata.scan_id, trade.trade_id),
      rank: index + 1,
      title: formatTradeLabel(trade),
      strategyLabel: trade.strategy_label ?? labelFromValue(trade.strategy_type, "Trade"),
      subtitle: `Exp ${trade.expiration_date ?? "-"} • DTE ${formatNumber(trade.DTE)} • ${labelFromValue(trade.volatility_context, "Premium context unavailable")}`,
      direction: labelFromValue(trade.directional_bias, "Neutral"),
      directionTone: toneFromDirection(trade.directional_bias),
      label: labelFromValue(trade.label ?? trade.stability_level, "Candidate"),
      labelTone: toneFromStability(trade.stability_level ?? trade.label),
      freshnessLabel: describeFreshnessLabel(trade.stability_level, trade.stability_count),
      freshnessTone: toneFromStability(trade.stability_level),
      score: formatNumber(fallbackScore(trade)),
      scoreDetail: thresholdDelta(fallbackScore(trade), thresholds.minScore),
      metrics: [
        {
          label: "Score",
          value: formatNumber(fallbackScore(trade)),
          detail: thresholdDelta(fallbackScore(trade), thresholds.minScore),
          tone: "accent" as const,
        },
        {
          label: "POP",
          value: formatNumber(trade.POP),
          detail: thresholdDelta(trade.POP, thresholds.minPop),
          tone: "success" as const,
        },
        {
          label: "ROR",
          value: formatNumber(trade.ROR),
          detail: thresholdDelta(trade.ROR, thresholds.minRor),
          tone: "warning" as const,
        },
        {
          label: "DTE",
          value: formatNumber(trade.DTE),
          detail: trade.expiration_date ? `Expires ${trade.expiration_date}` : null,
          tone: "neutral" as const,
        },
      ],
      quickReview: {
        summary: firstNonEmpty([trade.decision_summary, trade.status_reason, trade.explanation]) ?? "No short review text was provided.",
        structure: [
          `Strikes ${formatNumber(trade.short_strike)} / ${formatNumber(trade.long_strike)}`,
          `Max risk ${formatCurrency(trade.max_risk)} against ${formatCurrency(trade.net_credit)} credit`,
          `Stability ${labelFromValue(trade.stability_level, "Unknown")}${trade.stability_count !== undefined ? ` (${trade.stability_count})` : ""}`,
        ],
      },
      narrative: [
        labelFromValue(trade.volatility_context, "Premium context unavailable"),
        `${labelFromValue(trade.directional_bias, "Neutral")} posture`,
        describeFreshnessLabel(trade.stability_level, trade.stability_count),
      ],
      chartLabel: trade.directional_bias === "bearish" ? "Risk profile skewed defensive" : "Risk profile skewed supportive",
      riskNote: `Collect ${formatCurrency(trade.net_credit)} to take on up to ${formatCurrency(trade.max_risk)} of defined risk.`,
      portfolioNote: concentration
        ? `${trade.ticker} already represents ${concentration.share_pct ?? concentration.count}% of the current qualified set.`
        : `${portfolio.posture} posture remains the main portfolio framing for this idea.`,
      riskProfile: {
        reward: trade.net_credit ?? null,
        risk: trade.max_risk ?? null,
      },
      actionLabel: "Review execution brief",
      };
    }),
  };
}


export function selectTradeDetailExperienceModel(scanResult: ScanResult, detail: TradeDetailResponse) {
  const trade = detail.trade;
  const historyContext = objectOrEmpty(scanResult.history_context);
  const historicalIntelligence = (historyContext.historical_intelligence_summary ?? {}) as HistoricalIntelligenceSummary;
  const historyMetadata: HistoryMetadata = historicalIntelligence.metadata ?? {};
  const recurringPatterns = arrayOrEmpty(
    historicalIntelligence.signal_quality_summary?.recurring_high_quality_patterns,
  );
  const portfolio = portfolioPosture(scanResult.portfolio_summary);
  const topTickerRows = arrayOrEmpty(scanResult.portfolio_summary?.exposure?.qualified?.top_ticker_concentration);
  const matchingTicker = topTickerRows.find((row) => row.ticker === trade.ticker) ?? null;
  const sizingWarnings = arrayOrEmpty(scanResult.portfolio_summary?.position_sizing?.warnings);
  const explanationRows = Object.entries(trade.score_breakdown ?? {})
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .slice(0, 4)
    .map(([key, value]) => `${labelFromValue(key)}: ${formatNumber(value as number | string)}`);

  return {
    header: {
      title: formatTradeLabel(trade),
      subtitle: `Scan ${detail.scan_id} • ${detail.scan_metadata.profile ?? scanResult.scan_metadata.profile} • ${detail.scan_metadata.ticker_group ?? scanResult.scan_metadata.ticker_group}`,
      direction: labelFromValue(trade.directional_bias, "Neutral"),
      directionTone: toneFromDirection(trade.directional_bias),
      statusLabel: labelFromValue(trade.label ?? trade.stability_level, "Candidate"),
      statusTone: toneFromStability(trade.stability_level ?? trade.label),
    },
    quickVerdict:
      firstNonEmpty([trade.decision_summary, trade.status_reason, trade.explanation]) ??
      "No concise verdict text was returned for this trade.",
    briefingPoints: [
      `${labelFromValue(trade.directional_bias, "Neutral")} ${trade.strategy_label ?? labelFromValue(trade.strategy_type, "spread").toLowerCase()} under the ${detail.scan_metadata.profile ?? scanResult.scan_metadata.profile} profile.`,
      `Current premium context reads ${labelFromValue(trade.volatility_context, "unspecified").toLowerCase()} with ${describeFreshnessLabel(trade.stability_level, trade.stability_count).toLowerCase()}.`,
    ],
    construction: [
      { label: "Short Strike", value: formatNumber(trade.short_strike) },
      { label: "Long Strike", value: formatNumber(trade.long_strike) },
      { label: "Expiration", value: trade.expiration_date ?? "-" },
      { label: "DTE", value: formatNumber(trade.DTE) },
      { label: "Underlying", value: formatCurrency(trade.underlying_price) },
      { label: "Volatility", value: labelFromValue(trade.volatility_context, "Unspecified") },
    ],
    strikeMarkers: [
      { label: "Underlying", value: formatCurrency(trade.underlying_price), detail: "Current reference price" },
      { label: "Short Strike", value: formatNumber(trade.short_strike), detail: "Primary short leg" },
      { label: "Long Strike", value: formatNumber(trade.long_strike), detail: "Protective long leg" },
    ],
    riskReward: [
      { label: "POP", value: formatNumber(trade.POP), tone: "success" as const },
      { label: "ROR", value: formatNumber(trade.ROR), tone: "warning" as const },
      { label: "Net Credit", value: formatCurrency(trade.net_credit), tone: "accent" as const },
      { label: "Spread Width", value: formatNumber(trade.spread_width), tone: "neutral" as const },
      { label: "Max Risk", value: formatCurrency(trade.max_risk), tone: "danger" as const },
      { label: "Score", value: formatNumber(fallbackScore(trade)), tone: "accent" as const },
    ],
    executionPrep: [
      `Target expiration: ${trade.expiration_date ?? "Unknown"}`,
      `Spread width: ${formatNumber(trade.spread_width)} with estimated max risk ${formatCurrency(trade.max_risk)}.`,
      `Current POP / ROR reads ${formatNumber(trade.POP)} / ${formatNumber(trade.ROR)}.`,
    ],
    riskStory: [
      `Defined risk is capped near ${formatCurrency(trade.max_risk)} while the current credit reads ${formatCurrency(trade.net_credit)}.`,
      `The setup expires ${trade.expiration_date ?? "on an unspecified date"} with ${formatNumber(trade.DTE)} DTE in view.`,
    ],
    whyThisTrade: [
      trade.status_reason,
      trade.decision_summary,
      trade.explanation,
      ...explanationRows,
    ].filter(Boolean) as string[],
    stability: {
      metrics: [
        { label: "Stability", value: labelFromValue(trade.stability_level, "Unknown"), tone: "neutral" as const },
        { label: "Times Seen", value: trade.stability_count ?? "-", tone: "accent" as const },
        { label: "Runs Analyzed", value: historyMetadata.runs_analyzed ?? 0, tone: "neutral" as const },
        { label: "Signals Logged", value: historyMetadata.signals_analyzed ?? 0, tone: "neutral" as const },
      ],
      notes: [
        recurringPatterns.length > 0
          ? `${recurringPatterns.length} recurring high-quality pattern(s) are available in the current history context.`
          : "History context is still thin in the current view.",
        detail.diagnostics.missing_tickers?.length
          ? `Missing tickers in this scan: ${detail.diagnostics.missing_tickers.join(", ")}`
          : null,
      ].filter(Boolean) as string[],
    },
    portfolioImpact: {
      posture: portfolio.posture,
      notes: [
        ...portfolio.interpretation.slice(0, 1),
        matchingTicker
          ? `${matchingTicker.ticker} represents ${matchingTicker.share_pct ?? 0}% of the current qualified set.`
          : null,
        ...arrayOrEmpty(scanResult.portfolio_summary?.exposure?.notes).slice(0, 1),
        ...sizingWarnings.slice(0, 1),
      ].filter(Boolean) as string[],
    },
    historyStory: [
      recurringPatterns.length > 0
        ? `Recurring history exists for ${recurringPatterns.length} high-quality pattern(s), which adds context but not certainty.`
        : "History is currently thin, so this trade should be judged mostly on the current run.",
      matchingTicker
        ? `${matchingTicker.ticker} is already present in the run-level concentration view.`
        : null,
    ].filter(Boolean) as string[],
    diagnostics: {
      tone: detail.diagnostics.provider_errors?.length ? ("warning" as const) : ("info" as const),
      title: detail.diagnostics.provider_errors?.length ? "Scan caveats present" : "Scan context",
      message: detail.diagnostics.provider_errors?.length
        ? "Provider issues were reported for this scan, so use the trade detail with appropriate caution."
        : "This brief reflects the current scan context and the latest trade values returned for this setup.",
    },
    actions: [
      { label: "Back to Qualified Trades", to: "/qualified" },
      { label: "Review Overview", to: "/" },
      { label: "Check Alerts", to: "/alerts" },
    ],
  };
}


export function selectSidebarWorkflowModel(
  latestScan: ScanResult | null | undefined,
  request: ScanRequest,
  mode: WorkflowMode,
  isRunning: boolean,
) {
  const strategyLabels = request.selected_strategy_keys.map((key) => strategyLookup[key] ?? key);
  const topTrade = latestScan?.summary.top_overall ?? latestScan?.qualified_trades[0] ?? null;

  const readiness = isRunning
    ? {
        tone: "info" as const,
        title: "Scan in progress",
        message: mode === "guided"
          ? "Review the plan summary while the next opportunity set is being prepared."
          : "The current control set is being executed against the backend scan contract.",
      }
    : latestScan
      ? {
          tone: "success" as const,
          title: "Latest scan ready",
          message: "You can review the current decision surfaces or adjust the plan and run again.",
        }
      : {
          tone: "info" as const,
          title: "Ready to run",
          message: mode === "guided"
            ? "Use the guided framing below, then run the scan when the plan looks right."
            : "Adjust the primary and advanced controls, then run the scan.",
        };

  return {
    modeFrame: mode === "guided"
      ? {
          eyebrow: "Mode",
          title: "Guided",
          description: "Intent-first scan controls.",
        }
      : {
          eyebrow: "Mode",
          title: "Expert",
          description: "Raw controls, same scan contract.",
        },
    readiness,
    planSummary: {
      title: "Interpreted Plan",
      lines: buildSidebarPlanSummary(request),
    },
    interpretedSummary: {
      title: "Live Plan",
      lines: buildSidebarPlanSummary(request),
      helper: mode === "guided"
        ? "Short labels, same backend mapping."
        : "Direct fields, unchanged ranking logic.",
    },
    guidedQuestions: [
      {
        step: "01",
        title: "What kind of premium setup feels right today?",
        description: "Choose the overall posture first so PRIS knows how selective and defensive to be.",
      },
      {
        step: "02",
        title: "Which part of the market should PRIS search?",
        description: "Pick the watchlist and the direction you care about before worrying about the details.",
      },
      {
        step: "03",
        title: "When should the trade expire?",
        description: "Use a simple timing preference instead of thinking in raw DTE ranges.",
      },
      {
        step: "04",
        title: "How selective should the shortlist feel?",
        description: "Decide whether you want a broader list, tighter quality filtering, or more repeated signals.",
      },
    ],
    expertNotes: [
      "Expert mode exposes raw scan fields inside the same grouped workflow.",
      "Candidate ranking still stays server-driven.",
    ],
    guardrails: [
      "No score calculations are performed in React.",
      "Alert eligibility remains backend-owned.",
      "Portfolio posture is displayed, not inferred client-side.",
    ],
    latestSnapshot: latestScan
      ? {
          profile: latestScan.scan_metadata.profile,
          tickerGroup: latestScan.scan_metadata.ticker_group,
          qualified: latestScan.summary.qualified_count,
          alerts: latestScan.alerts.length,
          runtime: latestScan.scan_metadata.execution_time_seconds,
          topTrade: topTrade ? formatTradeLabel(topTrade) : null,
        }
      : null,
  };
}