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

export type CredentialsPayload = {
  email: string;
  password: string;
};

export type CurrentUser = {
  user_id: string;
  email: string;
  auth_provider: string;
  created_at: string;
  last_login_at: string | null;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: CurrentUser;
};

export type ScanMetadataBasics = {
  scan_id: string;
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
  trade_id?: string;
  ticker: string;
  strategy_type: string;
  strategy_key?: string;
  strategy_label?: string;
  expiration_date?: string;
  DTE?: number;
  short_strike?: number;
  long_strike?: number;
  underlying_price?: number;
  net_credit?: number;
  spread_width?: number;
  max_risk?: number;
  POP?: number;
  ROR?: number;
  score?: number;
  adjusted_score?: number;
  label?: string;
  decision_summary?: string | null;
  directional_bias?: string;
  status_reason?: string;
  explanation?: string;
  volatility_context?: string;
  stability_level?: string;
  stability_count?: number;
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
  partial_result?: boolean;
  performance?: Record<string, unknown>;
  cache?: Record<string, unknown>;
};

export type HistoryMetadata = {
  runs_analyzed?: number;
  signals_analyzed?: number;
  latest_run_timestamp?: string | null;
  history_available?: boolean;
  signal_history_available?: boolean;
};

export type HistoryCountRow = {
  ticker?: string;
  strategy?: string;
  label?: string;
  volatility_context?: string;
  stability_level?: string;
  count: number;
};

export type HistoryAverageRow = {
  ticker?: string;
  strategy?: string;
  pair?: string;
  volatility_context?: string;
  stability_level?: string;
  average_adjusted_score?: number | null;
  count?: number;
};

export type HistoricalIntelligenceSummary = {
  metadata?: HistoryMetadata;
  signal_quality_summary?: {
    most_frequent_qualified_tickers?: HistoryCountRow[];
    most_frequent_qualified_strategies?: HistoryCountRow[];
    recurring_high_quality_patterns?: Array<{
      pattern: string;
      count: number;
      average_adjusted_score?: number | null;
    }>;
  };
  feature_summary?: {
    average_adjusted_score_by_ticker_strategy_pair?: HistoryAverageRow[];
  };
};

export type HistoryContext = {
  historical_intelligence_summary?: HistoricalIntelligenceSummary;
};

export type DailySummary = {
  profile?: string;
  ticker_group?: string;
  execution_time_seconds?: number | null;
  dte_range?: {
    dte_min?: number;
    dte_max?: number;
  };
  qualified_count?: number;
  near_miss_count?: number;
  alerts_count?: number;
  top_overall?: QualifiedTradeRow | null;
  stable_alert_count?: number;
  emerging_alert_count?: number;
  new_alert_count?: number;
  most_stable_alert?: QualifiedTradeRow | null;
};

export type PortfolioSummary = {
  exposure?: {
    metadata?: {
      qualified_trade_count?: number;
      alert_trade_count?: number;
    };
    qualified?: {
      counts_by_ticker?: Array<{ ticker: string; count: number; share_pct?: number }>;
      counts_by_strategy?: Array<{ strategy: string; count: number; share_pct?: number }>;
      directional_exposure?: Array<{ directional_bias: string; count: number; share_pct?: number }>;
      top_ticker_concentration?: Array<{ ticker: string; count: number; share_pct?: number }>;
      notes?: string[];
    };
    alerts?: {
      notes?: string[];
    };
    notes?: string[];
  };
  position_sizing?: {
    inputs?: {
      account_size?: number;
      max_risk_pct?: number;
      max_risk_dollars?: number;
    };
    summary?: {
      qualified_trade_count?: number;
      trade_count_with_risk_estimate?: number;
      fits_budget_count?: number;
      oversized_count?: number;
      insufficient_data_count?: number;
      average_estimated_max_risk_dollars?: number | null;
    };
    trade_sizing?: Array<{
      ticker?: string;
      strategy?: string;
      adjusted_score?: number;
      estimated_max_risk_dollars?: number | null;
      fits_risk_budget?: boolean | null;
      approx_contracts_within_budget?: number | null;
      sizing_note?: string;
    }>;
    warnings?: string[];
  };
  overlap?: {
    repeated_ticker_direction_combinations?: Array<{
      ticker_direction: string;
      count: number;
    }>;
    notes?: string[];
  };
  decision?: {
    posture_label?: string;
    interpretation?: string[];
    key_portfolio_signals?: string[];
    cautions?: string[];
  };
};

export type ScanResult = {
  scan_metadata: ScanMetadataBasics;
  summary: ScanSummaryBasics;
  qualified_trades: QualifiedTradeRow[];
  alerts: AlertItem[];
  near_miss_trades: QualifiedTradeRow[];
  ticker_diagnostics: Array<Record<string, unknown>>;
  portfolio_summary: PortfolioSummary;
  history_context: HistoryContext;
  daily_summary: DailySummary;
  diagnostics: ScanDiagnostics;
};

export type TradeDetailData = TradeIdentityFields & {
  underlying_price?: number;
  net_credit?: number;
  spread_width?: number;
  max_risk?: number;
  consistency_bonus?: number;
  score_breakdown?: Record<string, unknown> | null;
  penalties?: Record<string, unknown> | null;
};

export type TradeDetailResponse = {
  scan_id: string;
  trade: TradeDetailData;
  scan_metadata: {
    profile?: string;
    ticker_group?: string;
    generated_at?: string;
  };
  diagnostics: {
    provider_errors?: Array<Record<string, unknown>>;
    missing_tickers?: string[];
  };
};

export type PayoffPoint = {
  underlying_price: number;
  expiration_payoff: number;
};

export type PayoffAnalysis = {
  strategy_key: string;
  ticker: string | null;
  quantity: number;
  underlying_price_reference: number;
  short_strike: number;
  long_strike: number;
  net_credit: number;
  spread_width: number;
  max_profit: number;
  max_loss: number;
  breakeven_low: number | null;
  breakeven_high: number | null;
  profit_zone: string;
  loss_zone: string;
  expiration_summary: string;
  price_grid: number[];
  payoff_points: PayoffPoint[];
};

export type PayoffEnvelope = {
  source_type: string;
  source_id: string;
  payoff: PayoffAnalysis;
};

export type StrategyVariant = {
  variant_type: "baseline" | "conservative" | "max_credit";
  strategy_key: string;
  reference_trade_id: string | null;
  short_strike: number;
  long_strike: number;
  expiration_date: string | null;
  net_credit: number;
  spread_width: number;
  max_profit: number;
  max_loss: number;
  breakeven: number;
  label: string;
  rationale: string;
  is_credit_estimated: boolean;
  comparison: {
    is_baseline: boolean;
    delta_net_credit: number;
    delta_max_profit: number;
    delta_max_loss: number;
    delta_breakeven: number;
    delta_spread_width: number;
    risk_reward_ratio: number | null;
    delta_risk_reward_ratio: number | null;
    summary: string;
    safety_tradeoff: string;
  } | null;
  payoff: PayoffAnalysis | null;
};

export type VariantSet = {
  scan_id: string;
  trade_id: string;
  strategy_key: string;
  underlying_price_reference: number;
  ticker: string | null;
  variants: StrategyVariant[];
};

export type TradeLifecycleState =
  | "new"
  | "saved"
  | "watching"
  | "execution_ready"
  | "paper_submitted"
  | "paper_filled"
  | "paper_closed"
  | "dismissed";

export type TradeLifecycleRecord = {
  trade_id: string;
  lifecycle_state: TradeLifecycleState;
  state_updated_at: string | null;
  note: string | null;
  tags: string[];
  source_scan_id: string | null;
  created_at: string | null;
  updated_at: string | null;
  is_default: boolean;
};

export type TradeLifecycleListResponse = {
  items: TradeLifecycleRecord[];
};

export type TradeLifecycleUpsertPayload = {
  lifecycle_state?: TradeLifecycleState;
  note?: string | null;
  tags?: string[];
  source_scan_id?: string | null;
};

export type ExecutionTicketStatus =
  | "draft"
  | "ready"
  | "submitted"
  | "accepted"
  | "rejected"
  | "canceled"
  | "filled";

export type OrderIntent = "open_credit" | "open_debit" | "other";

export type ExecutionTicket = {
  ticket_id: string;
  trade_id: string;
  source_scan_id: string | null;
  ticker: string;
  strategy_key: string;
  strategy_label: string;
  directional_bias: string | null;
  expiration_date: string | null;
  short_strike: number | null;
  long_strike: number | null;
  underlying_price_at_creation: number | null;
  net_credit_estimate: number | null;
  max_risk_estimate: number | null;
  adjusted_score_at_creation: number | null;
  quantity: number;
  order_intent: OrderIntent;
  execution_status: ExecutionTicketStatus;
  note: string | null;
  created_at: string | null;
  updated_at: string | null;
  broker_order_id: string | null;
  broker_status_raw: string | null;
  broker_submitted_at: string | null;
  broker_updated_at: string | null;
  last_submission_payload: Record<string, unknown> | null;
  last_submission_response: Record<string, unknown> | null;
  submission_error_message: string | null;
};

export type ExecutionTicketListResponse = {
  items: ExecutionTicket[];
};

export type CreateTicketPayload = {
  trade_id: string;
  source_scan_id?: string | null;
  ticker: string;
  strategy_key: string;
  strategy_label: string;
  directional_bias?: string | null;
  expiration_date?: string | null;
  short_strike?: number | null;
  long_strike?: number | null;
  underlying_price_at_creation?: number | null;
  net_credit_estimate?: number | null;
  max_risk_estimate?: number | null;
  adjusted_score_at_creation?: number | null;
  quantity?: number;
  order_intent?: OrderIntent;
  note?: string | null;
};

export type PatchTicketPayload = {
  quantity?: number | null;
  note?: string | null;
  clear_note?: boolean;
  execution_status?: "draft" | "ready" | null;
};

export type PaperPositionRow = {
  symbol: string | null;
  ticker: string | null;
  qty: number | null;
  side: string | null;
  avg_entry_price: number | null;
  market_value: number | null;
  cost_basis: number | null;
  unrealized_pl: number | null;
  unrealized_plpc: number | null;
  realized_pl: number | null;
  broker_updated_at: string | null;
  linked_ticket_id: string | null;
  strategy_label: string | null;
  directional_bias: string | null;
  ticket_execution_status: ExecutionTicketStatus | null;
  estimated_credit_or_debit: number | null;
};

export type PaperOrderHistoryRow = {
  broker_order_id: string | null;
  symbol: string | null;
  status: string | null;
  order_type: string | null;
  side: string | null;
  qty: number | null;
  filled_qty: number | null;
  filled_avg_price: number | null;
  submitted_at: string | null;
  updated_at: string | null;
};

export type PaperDashboardResponse = {
  pending_orders: ExecutionTicket[];
  open_positions: PaperPositionRow[];
  closed_trades: ExecutionTicket[];
  recent_orders: PaperOrderHistoryRow[];
  summary: {
    pending_count: number;
    open_positions_count: number;
    closed_count: number;
    recent_orders_count: number;
  };
  data_source: {
    mode: string;
    app_history_source: string;
    broker_live_data_available: boolean;
    broker_live_data_warning: string | null;
    status_refresh_attempted: boolean;
    status_refresh_errors: string[];
    generated_at: string;
  };
};
