from __future__ import annotations

import os


DEFAULT_CORS_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
]
DEFAULT_VERCEL_CORS_ORIGIN_REGEX = (
    r"^https://options-trading-app(?:-[a-z0-9-]+)?\.vercel\.app$"
)


def allowed_cors_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOW_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    return DEFAULT_CORS_ORIGINS


def allowed_cors_origin_regex() -> str | None:
    configured = (os.getenv("CORS_ALLOW_ORIGIN_REGEX") or "").strip()
    if configured:
        return configured

    if os.getenv("CORS_ALLOW_ORIGINS"):
        return None

    return DEFAULT_VERCEL_CORS_ORIGIN_REGEX


def cors_configuration_summary() -> dict[str, object]:
    has_origin_override = bool((os.getenv("CORS_ALLOW_ORIGINS") or "").strip())
    has_regex_override = bool((os.getenv("CORS_ALLOW_ORIGIN_REGEX") or "").strip())

    return {
        "allow_origins": allowed_cors_origins(),
        "allow_origin_regex": allowed_cors_origin_regex(),
        "source": {
            "origins": "env" if has_origin_override else "default",
            "origin_regex": "env" if has_regex_override else "default",
        },
    }