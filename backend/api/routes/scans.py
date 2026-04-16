"""Scan execution routes.

The routes stay intentionally thin:
- validate HTTP payloads
- map them to the existing ScanRequest contract
- call the backend scan service
- return the canonical ScanResult unchanged
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.contracts.scan_result import ScanRequest
from backend.services.scan_service import run_scan


router = APIRouter(prefix="/scans", tags=["scans"])

_LATEST_SCAN_RESULT: dict[str, Any] | None = None


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


@router.post("")
def post_scan(payload: ScanRequestBody) -> dict[str, Any]:
    global _LATEST_SCAN_RESULT

    try:
        result = run_scan(_to_scan_request(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Scan execution failed.",
        ) from exc

    _LATEST_SCAN_RESULT = result
    return result


@router.get("/latest")
def get_latest_scan() -> dict[str, Any]:
    if _LATEST_SCAN_RESULT is None:
        raise HTTPException(status_code=404, detail="No scan result is available yet.")

    return _LATEST_SCAN_RESULT
