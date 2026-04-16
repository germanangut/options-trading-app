"""Scan execution and retrieval routes."""

from typing import Any

from fastapi import APIRouter, HTTPException

from backend.api.schemas.scans import (
    AlertItemResponse,
    DailySummaryResponse,
    HistoryScreenResponse,
    PortfolioScreenResponse,
    ScanRequestBody,
    ScanResultResponse,
    TradeDetailResponse,
    TradeSummaryRow,
)
from backend.contracts.scan_result import ScanRequest
from backend.services.scan_service import (
    get_latest_scan,
    get_scan_by_id,
    get_trade_by_id,
    run_scan,
)
from backend.services.screen_builders import (
    build_daily_summary_payload,
    build_history_screen_payload,
    build_portfolio_screen_payload,
    build_trade_detail_payload,
    build_trade_summary_row,
)


router = APIRouter(tags=["scans"])
legacy_router = APIRouter(prefix="/scans", tags=["scans"])
v1_router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


def _to_scan_request(payload: ScanRequestBody) -> ScanRequest:
    return ScanRequest(
        profile=payload.profile,
        ticker_group=payload.ticker_group,
        selected_strategy_keys=list(payload.selected_strategy_keys),
        dte_min=payload.dte_min,
        dte_max=payload.dte_max,
        min_score=payload.min_score,
        min_pop=payload.min_pop,
        min_ror=payload.min_ror,
        min_consistency=payload.min_consistency,
        alerts_only=payload.alerts_only,
        use_mock_data=payload.use_mock_data,
    )


def _load_required_scan(scan_id: str) -> dict[str, Any]:
    scan_result = get_scan_by_id(scan_id)
    if scan_result is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' was not found.")

    return scan_result


def _load_required_trade(scan_result: dict[str, Any], trade_id: str) -> dict[str, Any]:
    trade = get_trade_by_id(scan_result, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail=f"Trade '{trade_id}' was not found in scan '{scan_result.get('scan_metadata', {}).get('scan_id')}'.")

    return trade


@legacy_router.post("", response_model=ScanResultResponse)
@v1_router.post("", response_model=ScanResultResponse)
def post_scan(payload: ScanRequestBody) -> dict[str, Any]:
    try:
        return run_scan(_to_scan_request(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Scan execution failed.") from exc


@legacy_router.get("/latest", response_model=ScanResultResponse)
@v1_router.get("/latest", response_model=ScanResultResponse)
def get_latest_scan_route() -> dict[str, Any]:
    scan_result = get_latest_scan()
    if scan_result is None:
        raise HTTPException(status_code=404, detail="No scan result is available yet.")

    return scan_result


@v1_router.get("/{scan_id}", response_model=ScanResultResponse)
def get_scan_by_id_route(scan_id: str) -> dict[str, Any]:
    return _load_required_scan(scan_id)


@v1_router.get("/{scan_id}/qualified-trades", response_model=list[TradeSummaryRow])
def get_qualified_trades(scan_id: str) -> list[dict[str, Any]]:
    scan_result = _load_required_scan(scan_id)
    return [build_trade_summary_row(trade) for trade in scan_result.get("qualified_trades", []) or []]


@v1_router.get("/{scan_id}/alerts", response_model=list[AlertItemResponse])
def get_alerts(scan_id: str) -> list[dict[str, Any]]:
    scan_result = _load_required_scan(scan_id)
    return [build_trade_summary_row(alert) for alert in scan_result.get("alerts", []) or []]


@v1_router.get("/{scan_id}/daily-summary", response_model=DailySummaryResponse)
def get_daily_summary(scan_id: str) -> dict[str, Any]:
    scan_result = _load_required_scan(scan_id)
    return build_daily_summary_payload(scan_result)


@v1_router.get("/{scan_id}/portfolio", response_model=PortfolioScreenResponse)
def get_portfolio(scan_id: str) -> dict[str, Any]:
    scan_result = _load_required_scan(scan_id)
    return build_portfolio_screen_payload(scan_result)


@v1_router.get("/{scan_id}/history", response_model=HistoryScreenResponse)
def get_history(scan_id: str) -> dict[str, Any]:
    scan_result = _load_required_scan(scan_id)
    return build_history_screen_payload(scan_result)


@v1_router.get("/{scan_id}/trades/{trade_id}", response_model=TradeDetailResponse)
def get_trade_detail(scan_id: str, trade_id: str) -> dict[str, Any]:
    scan_result = _load_required_scan(scan_id)
    trade = _load_required_trade(scan_result, trade_id)
    return build_trade_detail_payload(trade, scan_result)


router.include_router(legacy_router)
router.include_router(v1_router)
