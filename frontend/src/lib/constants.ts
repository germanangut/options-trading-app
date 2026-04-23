import type { ScanRequest } from "../types/api";

const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim();

export const API_BASE_URL = configuredApiBaseUrl || (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");

export const QUERY_KEYS = {
  latestScan: ["latest-scan"] as const,
  scanById: ["scan-by-id"] as const,
  tradeDetail: ["trade-detail"] as const,
  lifecycleList: ["lifecycle-list"] as const,
  tradeLifecycle: ["trade-lifecycle"] as const,
  ticketList: ["ticket-list"] as const,
  ticketsByTrade: ["tickets-by-trade"] as const,
  paperDashboard: ["paper-dashboard"] as const,
};

export const DEFAULT_SCAN_REQUEST: ScanRequest = {
  profile: "balanced",
  ticker_group: "tech",
  selected_strategy_keys: ["bull_put_spread", "bear_call_spread"],
  dte_min: 20,
  dte_max: 35,
  min_score: 65,
  min_pop: null,
  min_ror: null,
  min_consistency: 3,
  alerts_only: false,
  use_mock_data: null,
};

export const NAV_ITEMS = [
  { to: "/", label: "Overview", shortcut: "01" },
  { to: "/qualified", label: "Qualified Trades", shortcut: "02" },
  { to: "/alerts", label: "Alerts", shortcut: "03" },
  { to: "/portfolio", label: "Portfolio", shortcut: "04" },
  { to: "/history", label: "History", shortcut: "05" },
  { to: "/daily-summary", label: "Daily Summary", shortcut: "06" },
  { to: "/paper-dashboard", label: "Paper Dashboard", shortcut: "07" },
];

export const PROFILE_OPTIONS = [
  { value: "conservative", label: "Conservative" },
  { value: "balanced", label: "Balanced" },
  { value: "aggressive", label: "Aggressive" },
];

export const TICKER_GROUP_OPTIONS = [
  { value: "tech", label: "Tech" },
  { value: "index", label: "Index" },
  { value: "mixed", label: "Mixed" },
];

export const STRATEGY_OPTIONS = [
  { value: "bull_put_spread", label: "Bull Put Spread" },
  { value: "bear_call_spread", label: "Bear Call Spread" },
];
