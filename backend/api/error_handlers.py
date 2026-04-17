from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import requests

from backend.observability.context import get_request_id
from backend.observability.logging import get_logger, log_event


logger = get_logger(__name__)


def _error_code_for_status(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        422: "validation_error",
        502: "provider_failure",
    }
    return mapping.get(status_code, "internal_server_error")


def _build_error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or get_request_id()
    response = JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
        headers=headers,
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        log_event(
            logger,
            "request_failed",
            level=logging.WARNING,
            endpoint=request.url.path,
            method=request.method,
            status_code=422,
            error_type="RequestValidationError",
        )
        return _build_error_response(
            request,
            status_code=422,
            code="validation_error",
            message="Request validation failed.",
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        status_code = exc.status_code
        code = _error_code_for_status(status_code)
        message = str(exc.detail) if status_code < 500 else "Internal server error."
        log_event(
            logger,
            "request_failed",
            level=logging.WARNING if status_code < 500 else logging.ERROR,
            endpoint=request.url.path,
            method=request.method,
            status_code=status_code,
            error_type=code,
        )
        return _build_error_response(
            request,
            status_code=status_code,
            code=code,
            message=message,
            headers=exc.headers,
        )

    @app.exception_handler(requests.RequestException)
    async def handle_provider_exception(request: Request, exc: requests.RequestException) -> JSONResponse:
        log_event(
            logger,
            "request_failed",
            level=logging.ERROR,
            endpoint=request.url.path,
            method=request.method,
            status_code=502,
            error_type=type(exc).__name__,
            provider="alpaca",
        )
        return _build_error_response(
            request,
            status_code=502,
            code="provider_failure",
            message="Provider request failed.",
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "event": "request_failed",
                "fields": {
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": 500,
                    "error_type": type(exc).__name__,
                },
            },
        )
        return _build_error_response(
            request,
            status_code=500,
            code="internal_server_error",
            message="Internal server error.",
        )
