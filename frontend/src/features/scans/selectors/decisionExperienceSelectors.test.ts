import { describe, expect, it } from "vitest";

import type { ScanResult } from "../../../types/api";
import {
  selectOverviewCockpitModel,
  selectQualifiedBoardModel,
} from "./decisionExperienceSelectors";


function buildSparseScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_sparse",
      generated_at: "2026-04-17T00:00:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.5, ror_weight: 0.5 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: null,
      provider: null,
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
    summary: null as unknown as ScanResult["summary"],
    qualified_trades: null as unknown as ScanResult["qualified_trades"],
    alerts: null as unknown as ScanResult["alerts"],
    near_miss_trades: [],
    ticker_diagnostics: [],
    portfolio_summary: null as unknown as ScanResult["portfolio_summary"],
    history_context: null as unknown as ScanResult["history_context"],
    daily_summary: null as unknown as ScanResult["daily_summary"],
    diagnostics: null as unknown as ScanResult["diagnostics"],
  };
}


describe("decisionExperienceSelectors", () => {
  it("keeps cockpit and qualified-board models safe for sparse payloads", () => {
    const scan = buildSparseScan();

    const cockpit = selectOverviewCockpitModel(scan);
    const board = selectQualifiedBoardModel(scan);

    expect(cockpit.snapshot.title).toBe("No top opportunity");
    expect(cockpit.trust.metrics[1].value).toBe(0);
    expect(cockpit.history.runsAnalyzed).toBe(0);
    expect(board.items).toEqual([]);
    expect(board.summary[0].value).toBe(0);
    expect(board.emptyState.title).toBe("No qualified trades");
    expect(board.caveats).toEqual([]);
  });
});