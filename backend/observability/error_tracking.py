from __future__ import annotations

import logging

from backend.observability.logging import get_logger, log_event
from settings import get_settings


logger = get_logger(__name__)


def initialize_error_tracking() -> bool:
    settings = get_settings()
    sentry_dsn = settings.get("sentry_dsn")
    if not sentry_dsn:
        return False

    try:
        import sentry_sdk  # type: ignore
    except ImportError:
        log_event(
            logger,
            "error_tracking_unavailable",
            level=logging.WARNING,
            provider="sentry",
            reason="sdk_not_installed",
        )
        return False

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=settings.get("app_env", "development"),
        traces_sample_rate=0.0,
    )
    log_event(logger, "error_tracking_initialized", provider="sentry")
    return True
