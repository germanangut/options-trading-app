import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ScanResult } from "../../types/api";
import { AppShell } from "./AppShell";

vi.mock("../../features/auth/AuthContext", () => ({
  useAuth: vi.fn(),
}));

vi.mock("../../features/scans/hooks/useLatestScan", () => ({
  useLatestScan: vi.fn(),
}));

vi.mock("../../features/scans/hooks/useScanActivity", () => ({
  useScanActivity: vi.fn(),
}));

vi.mock("../../features/scans/hooks/useElapsedTimer", () => ({
  useElapsedTimer: vi.fn(),
}));

vi.mock("./Sidebar", () => ({
  Sidebar: () => <div data-testid="mock-sidebar" />,
}));

const { useAuth } = await import("../../features/auth/AuthContext");
const { useLatestScan } = await import("../../features/scans/hooks/useLatestScan");
const { useScanActivity } = await import("../../features/scans/hooks/useScanActivity");
const { useElapsedTimer } = await import("../../features/scans/hooks/useElapsedTimer");

afterEach(() => {
  cleanup();
});

function buildScan(): ScanResult {
  return {
    scan_metadata: {
      scan_id: "scan_shell",
      generated_at: "2026-04-19T12:15:00Z",
      profile: "balanced",
      ticker_group: "tech",
      selected_strategy_keys: ["bull_put_spread"],
      dte_range: { dte_min: 20, dte_max: 35 },
      scoring_weights: { pop_weight: 0.6, ror_weight: 0.4 },
      alert_thresholds: { min_score: 65, min_consistency: 3 },
      execution_time_seconds: 4.8,
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
      top_bull_put: null,
      top_bear_call: null,
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
      partial_result: false,
      performance: {
        provider_duration_ms: 4800,
        average_provider_latency_ms: 900,
        total_provider_calls: 12,
        retry_count: 2,
        retry_latency_impact_ms: 120,
        estimated_cache_saved_duration_ms: 85,
        cache_hit_rate: 0.22,
        scan_duration_ms: 5100,
        successful_ticker_count: 8,
        failed_ticker_count: 0,
      },
      cache: {},
    },
  };
}

function renderShell() {
  vi.mocked(useAuth).mockReturnValue({
    status: "authenticated",
    currentUser: {
      user_id: "user_1",
      email: "trader@example.com",
      auth_provider: "password",
      created_at: "2026-04-19T00:00:00Z",
      last_login_at: "2026-04-19T12:00:00Z",
    },
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    isAuthenticated: true,
  } as ReturnType<typeof useAuth>);

  vi.mocked(useLatestScan).mockReturnValue({
    isLoading: false,
    isError: false,
    data: buildScan(),
  } as ReturnType<typeof useLatestScan>);

  vi.mocked(useScanActivity).mockReturnValue({
    isRunning: false,
    latestSubmittedAt: null,
    latestRequest: null,
  });

  vi.mocked(useElapsedTimer).mockReturnValue(0);

  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<div>Decision workspace body</div>} />
        </Route>
      </Routes>
    </MemoryRouter>,
  );
}

describe("AppShell diagnostics UX", () => {
  it("shows a compact diagnostics status instead of inline diagnostics banners", () => {
    renderShell();

    expect(screen.getByTestId("diagnostics-status")).toBeInTheDocument();
    expect(screen.getByText("Provider slower than usual")).toBeInTheDocument();
    expect(screen.queryByText("Degraded retrieval signals")).not.toBeInTheDocument();
    expect(screen.queryByText("Performance summary")).not.toBeInTheDocument();
  });

  it("opens the diagnostics panel and keeps diagnostics content accessible", () => {
    renderShell();

    fireEvent.click(screen.getByRole("button", { name: "View diagnostics" }));

    expect(screen.getByTestId("session-diagnostics-panel")).toBeInTheDocument();
    expect(screen.getByText("Diagnostics")).toBeInTheDocument();
    expect(screen.getByText("Provider timing")).toBeInTheDocument();
    expect(screen.getByText("Retry and cache notes")).toBeInTheDocument();
    expect(screen.getByText("Session metadata")).toBeInTheDocument();
    expect(screen.getByText("Retry backoff added 120.00ms.")).toBeInTheDocument();
  });
});