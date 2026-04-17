from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from backend.api.cors import cors_configuration_summary
from backend.repositories.factory import get_auth_repository, get_scan_repository
from data_provider import has_alpaca_credentials
from settings import get_safe_settings_summary, get_settings


router = APIRouter(tags=["ops"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness_check() -> JSONResponse:
    settings = get_settings()
    checks: dict[str, dict[str, object]] = {}
    overall_ready = True

    try:
        get_scan_repository().list_scans(limit=1, newest_first=True)
        checks["persistence"] = {"status": "ok"}
    except Exception as exc:
        overall_ready = False
        checks["persistence"] = {"status": "error", "detail": type(exc).__name__}

    try:
        get_auth_repository().get_user_by_id("readiness_probe")
        checks["auth"] = {"status": "ok"}
    except Exception as exc:
        overall_ready = False
        checks["auth"] = {"status": "error", "detail": type(exc).__name__}

    history_dir = Path(settings.get("history_dir", ".history"))
    cache_dir = Path(settings.get("cache_dir", ".cache"))
    config_ready = history_dir.parent.exists() and cache_dir.parent.exists()
    checks["config"] = {
        "status": "ok" if config_ready else "error",
        "environment": settings.get("app_env", "development"),
        "summary": get_safe_settings_summary(),
    }
    if not config_ready:
        overall_ready = False

    checks["provider"] = {
        "status": "ok",
        "mode": "live" if has_alpaca_credentials() else "mock",
        "configured": has_alpaca_credentials(),
    }

    status_code = 200 if overall_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall_ready else "not_ready",
            "checks": checks,
        },
    )


@router.get("/ops/cors")
def cors_check() -> dict[str, object]:
    return {
        "status": "ok",
        "cors": cors_configuration_summary(),
    }