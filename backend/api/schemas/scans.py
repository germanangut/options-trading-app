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
    underlying_price: float | None = None
    net_credit: float | None = None
    spread_width: float | None = None
    max_risk: float | None = None
    explanation: str | None = None
    consistency_bonus: float | None = None
    score_breakdown: dict[str, Any] | None = None
    penalties: dict[str, Any] | None = None


class TradeDetailResponse(BaseModel):
    scan_id: str
    trade: TradeDetailData
    scan_metadata: dict[str, Any]
    diagnostics: dict[str, Any]


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
