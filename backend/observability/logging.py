from __future__ import annotations

from datetime import UTC, datetime
import json
import logging
import sys
from typing import Any

from backend.observability.context import get_context
from settings import get_settings


_LOGGING_CONFIGURED = False
_SENSITIVE_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "authorization",
    "credential",
    "api_key",
    "api_secret",
)


def _is_sensitive_key(key: str | None) -> bool:
    normalized = str(key or "").strip().lower()
    if normalized in {"request_id", "user_id", "scan_id"}:
        return False
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def _sanitize_value(value: Any, *, key: str | None = None) -> Any:
    if _is_sensitive_key(key):
        return "***"

    if isinstance(value, dict):
        return {
            str(child_key): _sanitize_value(child_value, key=str(child_key))
            for child_key, child_value in value.items()
            if child_value is not None
        }

    if isinstance(value, (list, tuple, set)):
        return [_sanitize_value(item) for item in value]

    return value


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
        }

        event = getattr(record, "event", None)
        if event:
            payload["event"] = event
        else:
            payload["message"] = record.getMessage()

        context = get_context()
        if context:
            payload.update(_sanitize_value(context))

        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(_sanitize_value(fields))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
            payload.setdefault("error_type", record.exc_info[0].__name__)

        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(force: bool = False) -> None:
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED and not force:
        return

    settings = get_settings()
    level_name = str(settings.get("log_level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, *, level: int = logging.INFO, **fields: Any) -> None:
    sanitized_fields = {
        key: value
        for key, value in _sanitize_value(fields).items()
        if value is not None
    }
    logger.log(level, event, extra={"event": event, "fields": sanitized_fields})
