import { describe, expect, it } from "vitest";

import type { ScanResult } from "../../../types/api";
import { selectScanPerformanceSummary } from "./scanSelectors";


function buildScanResult(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_123",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.5, ror_weight: 0.5 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 1.42,
      provider: "alpaca",
      request: {
        profile: "balanced",
        ticker_group: "tech",
        selected_strategy_keys: ["bull_put_spread"],
        dte_min: 20,
        dte_max: 35,
        min_score: 65,
        min_pop: null,
        min_ror: null,
        min_consistency: 3,
        alerts_only: false,
        use_mock_data: null,
      },
    },
    summary: {
      qualified_count: 1,
      near_miss_count: 0,
      top_overall: null,
    },
    qualified_trades: [],
    alerts: [],
    near_miss_trades: [],
    ticker_diagnostics: [],
    portfolio_summary: {},
    history_context: {},
    daily_summary: {},
    diagnostics: {
      missing_tickers: [],
      provider_errors: [],
      alerts_export_path: null,
      top_overall_identity: null,
      performance: {
        scan_duration_ms: 1320,
        successful_ticker_count: 3,
        failed_ticker_count: 1,
        total_provider_calls: 7,
        average_provider_latency_ms: 84.5,
        retry_latency_impact_ms: 120,
        estimated_cache_saved_duration_ms: 240,
      },
      cache: {},
    },
  };
}


describe("selectScanPerformanceSummary", () => {
  it("builds a lightweight UI summary from diagnostics performance metrics", () => {
    const summary = selectScanPerformanceSummary(buildScanResult());

    expect(summary).not.toBeNull();
    expect(summary?.message).toContain("1.32s");
    expect(summary?.notes).toContain("Tickers processed successfully: 3. Failed: 1.");
    expect(summary?.notes).toContain("Provider calls issued: 7.");
    expect(summary?.notes).toContain("Average provider latency: 84.50ms.");
    expect(summary?.notes).toContain("Retry backoff added 120.00ms.");
    expect(summary?.notes).toContain("Cache reuse saved an estimated 240.00ms.");
  });
});