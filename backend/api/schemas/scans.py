from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScanRequestBody(BaseModel):
    profile: str = "balanced"
    ticker_group: str = "tech"
    selected_strategy_keys: list[str] = Field(default_factory=list)
    dte_min: int = 20
    dte_max: int = 35
    min_score: int = 65
    min_pop: float | None = None
    min_ror: float | None = None
    min_consistency: int = 3
    alerts_only: bool = False
    use_mock_data: bool | None = None


class TradeSummaryRow(BaseModel):
    trade_id: str | None = None
    ticker: str | None = None
    strategy_type: str | None = None
    strategy_key: str | None = None
    strategy_label: str | None = None
    directional_bias: str | None = None
    expiration_date: str | None = None
    DTE: int | None = None
    short_strike: float | int | None = None
    long_strike: float | int | None = None
    POP: float | None = None
    ROR: float | None = None
    score: float | None = None
    adjusted_score: float | None = None
    label: str | None = None
    decision_summary: str | None = None
    status_reason: str | None = None
    volatility_context: str | None = None
    stability_level: str | None = None
    stability_count: int | None = None


class AlertItemResponse(TradeSummaryRow):
    pass


class ScanMetadataResponse(BaseModel):
    scan_id: str
    generated_at: str
    profile: str
    ticker_group: str
    selected_strategy_keys: list[str]
    dte_range: dict[str, Any]
    scoring_weights: dict[str, Any]
    alert_thresholds: dict[str, Any]
    execution_time_seconds: float | None = None
    provider: str | None = None
    request: dict[str, Any]


class ScanSummaryPayload(BaseModel):
    qualified_count: int
    near_miss_count: int
    top_overall: TradeSummaryRow | None = None
    top_bull_put: TradeSummaryRow | None = None
    top_bear_call: TradeSummaryRow | None = None


class ScanDiagnosticsResponse(BaseModel):
    missing_tickers: list[str]
    provider_errors: list[dict[str, Any]]
    alerts_export_path: str | None = None
    top_overall_identity: dict[str, Any] | None = None
    partial_result: bool = False
    performance: dict[str, Any] = Field(default_factory=dict)
    cache: dict[str, Any] = Field(default_factory=dict)


class ScanResultResponse(BaseModel):
    scan_metadata: ScanMetadataResponse
    summary: ScanSummaryPayload
    qualified_trades: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    near_miss_trades: list[dict[str, Any]]
    ticker_diagnostics: list[dict[str, Any]]
    portfolio_summary: dict[str, Any]
    history_context: dict[str, Any]
    daily_summary: dict[str, Any]
    diagnostics: ScanDiagnosticsResponse


class ScanSummaryResponse(BaseModel):
    scan_id: str
    scan_metadata: ScanMetadataResponse
    summary: ScanSummaryPayload
    diagnostics: ScanDiagnosticsResponse


class TradeDetailData(BaseModel):
    trade_id: str | None = None
    scan_id: str | None = None
    ticker: str | None = None
    strategy_type: str | None = None
    strategy_key: str | None = None
    strategy_label: str | None = None
    directional_bias: str | None = None
    direction: str | None = None
    expiration_date: str | None = None
    DTE: int | None = None
    short_strike: float | int | None = None
    long_strike: float | int | None = None
    POP: float | None = None
    ROR: float | None = None
    score: float | None = None
    adjusted_score: float | None = None
    label: str | None = None
    decision_summary: str | None = None
    status_reason: str | None = None
    volatility_context: str | None = None
    stability_level: str | None = None
    stability_count: int | None = None
    underlying_price: float | None = None
    net_credit: float | None = None
    spread_width: float | None = None
    width: float | None = None
    max_profit: float | None = None
    max_risk: float | None = None
    max_loss: float | None = None
    breakeven: float | None = None
    explanation: str | None = None
    why_this_trade: str | None = None
    consistency_bonus: float | None = None
    consistency_score: float | int | None = None
    stability_summary: str | None = None
    portfolio_fit_summary: str | None = None
    warnings: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, Any] | None = None
    penalties: dict[str, Any] | None = None


class TradeHistoryContext(BaseModel):
    has_history: bool
    runs_analyzed: int = 0
    recent_appearance_count: int = 0
    ticker_strategy_pair: str | None = None
    appeared_recently: bool = False
    latest_seen_at: str | None = None
    recent_continuity: str | None = None
    stability_note: str | None = None
    notes: list[str] = Field(default_factory=list)


class PortfolioFitSummary(BaseModel):
    posture_label: str | None = None
    estimated_max_risk_dollars: float | int | None = None
    fits_risk_budget: bool | None = None
    approx_contracts_within_budget: int | None = None
    note: str | None = None


class TradeDiagnosticsSummary(BaseModel):
    provider_errors: list[dict[str, Any]] = Field(default_factory=list)
    missing_tickers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TradeDetailResponse(BaseModel):
    scan_id: str
    trade: TradeDetailData
    scan_metadata: dict[str, Any]
    portfolio_fit: PortfolioFitSummary | None = None
    history_context: TradeHistoryContext
    diagnostics: TradeDiagnosticsSummary


class ScanComparisonSnapshot(BaseModel):
    has_previous_scan: bool
    previous_scan_id: str | None = None
    previous_generated_at: str | None = None
    qualified_count_change: int | None = None
    alerts_count_change: int | None = None
    top_opportunity_changed: bool | None = None
    current_top_trade_id: str | None = None
    previous_top_trade_id: str | None = None
    notes: list[str] = Field(default_factory=list)


class OverviewHeadlineSnapshot(BaseModel):
    scan_id: str
    generated_at: str | None = None
    profile: str | None = None
    ticker_group: str | None = None
    execution_time_seconds: float | None = None
    qualified_count: int = 0
    alerts_count: int = 0
    near_miss_count: int = 0


class ScanTrustSnapshot(BaseModel):
    status: str
    provider: str | None = None
    provider_error_count: int = 0
    missing_ticker_count: int = 0
    caveats: list[str] = Field(default_factory=list)


class OverviewOpportunitySummary(BaseModel):
    trade_id: str | None = None
    ticker: str | None = None
    strategy_type: str | None = None
    strategy_label: str | None = None
    directional_bias: str | None = None
    expiration_date: str | None = None
    DTE: int | None = None
    POP: float | None = None
    ROR: float | None = None
    score: float | None = None
    adjusted_score: float | None = None
    decision_summary: str | None = None
    status_reason: str | None = None
    label: str | None = None


class OverviewPortfolioSummary(BaseModel):
    posture_label: str | None = None
    interpretation: list[str] = Field(default_factory=list)
    top_ticker_concentration: str | None = None
    cautions: list[str] = Field(default_factory=list)


class OverviewSnapshotResponse(BaseModel):
    scan_id: str
    headline: OverviewHeadlineSnapshot
    top_opportunity: OverviewOpportunitySummary | None = None
    trust_snapshot: ScanTrustSnapshot
    comparison: ScanComparisonSnapshot
    portfolio_summary: OverviewPortfolioSummary


class HistorySummaryCard(BaseModel):
    label: str
    value: Any


class HistoryScreenResponse(BaseModel):
    scan_id: str
    summary_cards: list[HistorySummaryCard]
    recent_patterns: list[dict[str, Any]]
    top_tickers: list[dict[str, Any]]
    top_strategies: list[dict[str, Any]]
    top_pairs: list[dict[str, Any]]


class PortfolioSummaryCard(BaseModel):
    label: str
    value: Any


class PortfolioScreenResponse(BaseModel):
    scan_id: str
    summary_cards: list[PortfolioSummaryCard]
    positions: list[dict[str, Any]]
    warnings: list[str]
    exposure_notes: list[str]
    top_ticker_concentration: list[dict[str, Any]]
    directional_exposure: list[dict[str, Any]]
    interpretation: list[str]
    key_signals: list[str]
    cautions: list[str]
    overlap_warnings: list[str]


class DailyHeadlineResponse(BaseModel):
    profile: str | None = None
    ticker_group: str | None = None
    execution_time_seconds: float | None = None
    qualified_count: int | None = None
    near_miss_count: int | None = None
    alerts_count: int | None = None


class DailySignalResponse(BaseModel):
    label: str
    value: int | float | None = None


class DailySummaryResponse(BaseModel):
    scan_id: str
    headline: DailyHeadlineResponse
    top_opportunity: TradeSummaryRow | None = None
    alert_signals: list[DailySignalResponse]
    most_stable_alert: TradeSummaryRow | None = None
    notes: list[str]
