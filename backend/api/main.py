"""Minimal FastAPI app for scan execution and latest-scan retrieval."""

import os
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.error_handlers import register_exception_handlers
from backend.api.routes.auth import router as auth_router
from backend.api.routes.ops import router as ops_router
from backend.api.routes.scans import router as scans_router
from backend.observability.context import bind_context, clear_context
from backend.observability.error_tracking import initialize_error_tracking
from backend.observability.logging import configure_logging, get_logger, log_event
from settings import get_safe_settings_summary


configure_logging()
logger = get_logger(__name__)
initialize_error_tracking()


def _allowed_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOW_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    return [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]


app = FastAPI(
    title="Options Trading App Backend",
    version="0.1.0",
    description=(
        "Minimal backend skeleton for running options scans and retrieving "
        "the most recent canonical ScanResult."
    ),
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req_{uuid4().hex}"
    request.state.request_id = request_id
    bind_context(request_id=request_id)

    started_at = time.perf_counter()
    log_event(
        logger,
        "request_started",
        endpoint=request.url.path,
        method=request.method,
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_event(
            logger,
            "request_failed",
            level=40,
            endpoint=request.url.path,
            method=request.method,
            status_code=500,
            duration_ms=duration_ms,
            error_type=type(exc).__name__,
        )
        clear_context()
        raise

    duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    event_name = "request_completed" if response.status_code < 400 else "request_failed"
    log_level = 20 if response.status_code < 400 else 30
    log_event(
        logger,
        event_name,
        level=log_level,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    clear_context()
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_cors_origins(),
    allow_origin_regex=os.getenv("CORS_ALLOW_ORIGIN_REGEX") or None,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(scans_router)
app.include_router(auth_router)
app.include_router(ops_router)

log_event(logger, "app_configured", **get_safe_settings_summary())


def create_app() -> FastAPI:
    """Application factory for tests and local development."""
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
