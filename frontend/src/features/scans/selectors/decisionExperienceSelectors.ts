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
  const diagnostics = scanResult.diagnostics ?? { missing_tickers: [], provider_errors: [] };
  const qualifiedTrades = scanResult.qualified_trades ?? [];
  const alerts = scanResult.alerts ?? [];
  const topTrade = scanResult.summary.top_overall ?? qualifiedTrades[0] ?? null;
  const providerErrors = (diagnostics.provider_errors ?? []).length;
  const missingTickers = diagnostics.missing_tickers ?? [];
  const qualifiedCount = scanResult.summary.qualified_count ?? qualifiedTrades.length;
  const alertsCount = alerts.length;
  const historySummary = scanResult.history_context.historical_intelligence_summary ?? {};
  const historyMetadata = historySummary.metadata ?? {};
  const recurringPatterns = historySummary.signal_quality_summary?.recurring_high_quality_patterns ?? [];
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
        { label: "Qualified", value: scanResult.summary.qualified_count, tone: "success" as const },
        { label: "Alerts", value: scanResult.alerts.length, tone: "warning" as const },
        {
          label: "Stable Names",
          value: scanResult.qualified_trades.filter((trade) => trade.stability_level === "stable").length,
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
    },
    history: {
      runsAnalyzed: historyMetadata.runs_analyzed ?? 0,
      signalsAnalyzed: historyMetadata.signals_analyzed ?? 0,
      latestRun: historyMetadata.latest_run_timestamp ?? "No history yet",
      recurringPatterns: recurringPatterns.slice(0, 3),
    },
    nextActions: [
      { label: "Review qualified board", to: "/qualified" },
      { label: "Check alerts", to: "/alerts" },
      { label: "Read portfolio posture", to: "/portfolio" },
    ],
  };
}


export function selectQualifiedBoardModel(scanResult: ScanResult) {
  const diagnostics = scanResult.diagnostics ?? { missing_tickers: [], provider_errors: [] };
  const thresholds = currentScanThresholds(scanResult);
  const portfolio = portfolioPosture(scanResult.portfolio_summary);
  const caveats = [
    (diagnostics.provider_errors ?? []).length > 0
      ? "Provider issues were reported in this run, so the ranked board may be incomplete."
      : null,
    (diagnostics.missing_tickers ?? []).length > 0
      ? `Missing tickers: ${(diagnostics.missing_tickers ?? []).join(", ")}`
      : null,
    portfolio.topTicker?.share_pct && portfolio.topTicker.share_pct >= 30
      ? `${portfolio.topTicker.ticker} represents ${portfolio.topTicker.share_pct}% of the current qualified set.`
      : null,
  ].filter(Boolean) as string[];

  return {
    summary: [
      { label: "Qualified", value: scanResult.qualified_trades.length, tone: "success" as const },
      {
        label: "Stable",
        value: scanResult.qualified_trades.filter((trade) => trade.stability_level === "stable").length,
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
    emptyState: (diagnostics.provider_errors ?? []).length > 0
      ? {
          title: "Partial results available",
          message: "Provider failures affected this run. Review alerts and diagnostics before concluding there were no qualified setups.",
        }
      : (diagnostics.missing_tickers ?? []).length > 0 || diagnostics.partial_result
        ? {
            title: "Partial results available",
            message: "Some tickers were unavailable during the scan, so this empty board may reflect incomplete market coverage.",
          }
        : {
            title: "No qualified trades",
            message: "The latest scan did not produce any qualified opportunities. If you want a wider review set, broaden the ticker group or relax the score threshold.",
          },
    items: scanResult.qualified_trades.map((trade, index) => ({
      id: trade.trade_id ?? `${scanResult.scan_metadata.scan_id}-${index}`,
      href: buildTradeDetailPath(scanResult.scan_metadata.scan_id, trade.trade_id),
      rank: index + 1,
      title: formatTradeLabel(trade),
      subtitle: `Exp ${trade.expiration_date ?? "-"} • DTE ${formatNumber(trade.DTE)} • ${labelFromValue(trade.volatility_context, "Premium context unavailable")}`,
      direction: labelFromValue(trade.directional_bias, "Neutral"),
      directionTone: toneFromDirection(trade.directional_bias),
      label: labelFromValue(trade.label ?? trade.stability_level, "Candidate"),
      labelTone: toneFromStability(trade.stability_level ?? trade.label),
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
      ],
      quickReview: {
        summary: firstNonEmpty([trade.decision_summary, trade.status_reason, trade.explanation]) ?? "No short review text was provided.",
        structure: [
          `Strikes ${formatNumber(trade.short_strike)} / ${formatNumber(trade.long_strike)}`,
          `Stability ${labelFromValue(trade.stability_level, "Unknown")}${trade.stability_count !== undefined ? ` (${trade.stability_count})` : ""}`,
        ],
      },
    })),
  };
}


export function selectTradeDetailExperienceModel(scanResult: ScanResult, detail: TradeDetailResponse) {
  const trade = detail.trade;
  const historyMetadata = scanResult.history_context.historical_intelligence_summary?.metadata ?? {};
  const recurringPatterns = scanResult.history_context.historical_intelligence_summary?.signal_quality_summary?.recurring_high_quality_patterns ?? [];
  const portfolio = portfolioPosture(scanResult.portfolio_summary);
  const topTickerRows = scanResult.portfolio_summary.exposure?.qualified?.top_ticker_concentration ?? [];
  const matchingTicker = topTickerRows.find((row) => row.ticker === trade.ticker) ?? null;
  const sizingWarnings = scanResult.portfolio_summary.position_sizing?.warnings ?? [];
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
    construction: [
      { label: "Short Strike", value: formatNumber(trade.short_strike) },
      { label: "Long Strike", value: formatNumber(trade.long_strike) },
      { label: "Expiration", value: trade.expiration_date ?? "-" },
      { label: "DTE", value: formatNumber(trade.DTE) },
      { label: "Underlying", value: formatCurrency(trade.underlying_price) },
      { label: "Volatility", value: labelFromValue(trade.volatility_context, "Unspecified") },
    ],
    riskReward: [
      { label: "POP", value: formatNumber(trade.POP), tone: "success" as const },
      { label: "ROR", value: formatNumber(trade.ROR), tone: "warning" as const },
      { label: "Net Credit", value: formatCurrency(trade.net_credit), tone: "accent" as const },
      { label: "Spread Width", value: formatNumber(trade.spread_width), tone: "neutral" as const },
      { label: "Max Risk", value: formatCurrency(trade.max_risk), tone: "danger" as const },
      { label: "Score", value: formatNumber(fallbackScore(trade)), tone: "accent" as const },
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
          : "Historical pattern context is limited in the current payload.",
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
        ...scanResult.portfolio_summary.exposure?.notes?.slice(0, 1) ?? [],
        ...sizingWarnings.slice(0, 1),
      ].filter(Boolean) as string[],
    },
    diagnostics: {
      tone: detail.diagnostics.provider_errors?.length ? ("warning" as const) : ("info" as const),
      title: detail.diagnostics.provider_errors?.length ? "Scan caveats present" : "Scan context",
      message: detail.diagnostics.provider_errors?.length
        ? "Provider issues were reported for this scan, so use the trade detail with appropriate caution."
        : "This screen is backed by the current trade-detail contract and stays presentation-only.",
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
          eyebrow: "Guided Mode",
          title: "Workflow-first setup",
          description: "Use the higher-signal controls first and keep the scan request easy to reason about.",
        }
      : {
          eyebrow: "Expert Mode",
          title: "Direct control surface",
          description: "Tune the scan request explicitly while keeping the same backend truth and ordering.",
        },
    readiness,
    planSummary: {
      title: "Current Plan",
      lines: [
        `${profileLookup[request.profile] ?? labelFromValue(request.profile)} profile on ${tickerLookup[request.ticker_group] ?? labelFromValue(request.ticker_group)} names.`,
        `${request.dte_min}-${request.dte_max} DTE window with score floor ${request.min_score}.`,
        `${request.min_consistency} minimum consistency requirement${mode === "guided" ? " for guided review" : " across the expert setup"}.`,
        strategyLabels.length > 0
          ? `${strategyLabels.length} strategy${strategyLabels.length === 1 ? "" : "ies"} enabled: ${strategyLabels.join(", ")}.`
          : "No strategies selected yet.",
      ],
    },
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