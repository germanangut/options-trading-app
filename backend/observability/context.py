from __future__ import annotations

from contextvars import ContextVar
from typing import Any


_request_context: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})


def get_context() -> dict[str, Any]:
    return dict(_request_context.get({}))


def bind_context(**values: Any) -> None:
    context = get_context()
    for key, value in values.items():
        if value is None:
            context.pop(key, None)
        else:
            context[key] = value
    _request_context.set(context)


def clear_context() -> None:
    _request_context.set({})


def get_request_id() -> str | None:
    return get_context().get("request_id")


def get_user_id() -> str | None:
    return get_context().get("user_id")
