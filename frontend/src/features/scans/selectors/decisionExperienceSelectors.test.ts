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
      alert_thresholds: { min_score: 55, min_consistency: 1 },
      execution_time_seconds: null,
      provider: null,
      request: {
        profile: "balanced",
        ticker_group: "tech",
        selected_strategy_keys: ["bull_put_spread"],
        dte_min: 20,
        dte_max: 35,
        min_score: 55,
        min_pop: null,
        min_ror: null,
        min_consistency: 1,
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

  it("shows zero-alert messaging when there are no alerts and no qualified trades", () => {
    const scan = buildSparseScan();
    const cockpit = selectOverviewCockpitModel(scan);

    expect(cockpit.alertsSnapshot.title).toBe("No alerts this run");
    expect(cockpit.alertsSnapshot.notes).toEqual(
      expect.arrayContaining([
        expect.stringContaining("No qualified trades or alerts were produced"),
      ]),
    );
  });

  it("explains that qualified trades exist but none passed alert filters", () => {
    const scan = buildSparseScan();
    scan.qualified_trades = [
      {
        trade_id: "trade_msft",
        ticker: "MSFT",
        strategy_type: "bull_put_spread",
        strategy_key: "bull_put_spread",
        strategy_label: "Bull Put Spread",
        directional_bias: "bullish",
        expiration_date: "2026-05-15",
        DTE: 28,
        short_strike: 390,
        long_strike: 385,
        POP: 66,
        ROR: 18,
        score: 57,
        adjusted_score: 58,
        label: "High Quality",
        decision_summary: null,
        status_reason: "Cleared Balanced thresholds.",
        volatility_context: "balanced_premium",
        stability_level: "new",
        stability_count: 0,
      },
    ] as ScanResult["qualified_trades"];
    scan.alerts = [] as unknown as ScanResult["alerts"];

    const cockpit = selectOverviewCockpitModel(scan);

    expect(cockpit.alertsSnapshot.title).toBe("No alerts this run");
    expect(cockpit.alertsSnapshot.notes).toEqual(
      expect.arrayContaining([
        expect.stringContaining("Qualified trades were found, but none passed the tighter alert filters"),
        expect.stringContaining("Alerts surface only the strongest candidates"),
        expect.stringContaining("Expert mode"),
      ]),
    );
  });
});