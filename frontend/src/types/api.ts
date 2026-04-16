export type ScanRequest = {
  profile: string;
  ticker_group: string;
  selected_strategy_keys: string[];
  dte_min: number;
  dte_max: number;
  min_score: number;
  min_pop: number | null;
  min_ror: number | null;
  min_consistency: number;
  alerts_only: boolean;
  use_mock_data: boolean | null;
};

export type ScanMetadataBasics = {
  generated_at: string;
  profile: string;
  ticker_group: string;
  selected_strategy_keys: string[];
  dte_range: {
    dte_min: number;
    dte_max: number;
  };
  scoring_weights: {
    pop_weight: number;
    ror_weight: number;
  };
  alert_thresholds: {
    min_score: number;
    min_consistency: number;
  };
  execution_time_seconds: number | null;
  provider: string | null;
  request: ScanRequest;
};

export type TradeIdentityFields = {
  ticker: string;
  strategy_type: string;
  strategy_key?: string;
  strategy_label?: string;
  expiration_date?: string;
  DTE?: number;
  short_strike?: number;
  long_strike?: number;
  POP?: number;
  ROR?: number;
  score?: number;
  adjusted_score?: number;
  label?: string;
  decision_summary?: string;
  directional_bias?: string;
};

export type QualifiedTradeRow = TradeIdentityFields;
export type AlertItem = QualifiedTradeRow;

export type ScanSummaryBasics = {
  qualified_count: number;
  near_miss_count: number;
  top_overall: QualifiedTradeRow | null;
  top_bull_put?: QualifiedTradeRow | null;
  top_bear_call?: QualifiedTradeRow | null;
};

export type ScanDiagnostics = {
  missing_tickers: string[];
  provider_errors: Array<Record<string, unknown>>;
  alerts_export_path: string | null;
  top_overall_identity: {
    ticker: string;
    strategy_type: string;
    expiration_date: string | null;
    short_strike: number | null;
    long_strike: number | null;
  } | null;
};

export type ScanResult = {
  scan_metadata: ScanMetadataBasics;
  summary: ScanSummaryBasics;
  qualified_trades: QualifiedTradeRow[];
  alerts: AlertItem[];
  near_miss_trades: QualifiedTradeRow[];
  ticker_diagnostics: Array<Record<string, unknown>>;
  portfolio_summary: Record<string, unknown>;
  history_context: Record<string, unknown>;
  daily_summary: Record<string, unknown>;
  diagnostics: ScanDiagnostics;
};
