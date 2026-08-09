"""Canonical non-stream HTTP response envelope middleware."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any, cast, override

from fastapi import Request, Response, status
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.services.api.contracts.models import (
    ApiError,
    ApiErrorCode,
    ApiMetadata,
    ApiResponse,
    ApiStatus,
)

_SUCCESS_MIN = 200
_ERROR_MIN = 400
_NO_CONTENT = 204
_ENVELOPE_KEYS = {"status", "message", "data", "error", "metadata"}
_FRAMEWORK_PATHS = frozenset(
    {"/docs", "/docs/oauth2-redirect", "/openapi.json", "/redoc"}
)
_STATUS_ERROR_CODES = {
    status.HTTP_401_UNAUTHORIZED: ApiErrorCode.AUTHENTICATION_REQUIRED,
    status.HTTP_403_FORBIDDEN: ApiErrorCode.AUTHORIZATION_DENIED,
    status.HTTP_404_NOT_FOUND: ApiErrorCode.NOT_FOUND,
    status.HTTP_429_TOO_MANY_REQUESTS: ApiErrorCode.RATE_LIMITED,
}
_VALIDATION_STATUSES = {
    status.HTTP_400_BAD_REQUEST,
    status.HTTP_409_CONFLICT,
    status.HTTP_422_UNPROCESSABLE_CONTENT,
}
_DEPENDENCY_STATUSES = {
    status.HTTP_502_BAD_GATEWAY,
    status.HTTP_503_SERVICE_UNAVAILABLE,
    status.HTTP_504_GATEWAY_TIMEOUT,
}


def _error_code(detail: object, status_code: int) -> ApiErrorCode:
    """Classify one bounded public error detail.

    Returns:
        Stable public error code.
    """
    candidate = detail if isinstance(detail, str) else ""
    try:
        return ApiErrorCode(candidate)
    except ValueError:
        if status_code in _STATUS_ERROR_CODES:
            return _STATUS_ERROR_CODES[status_code]
        if status_code in _VALIDATION_STATUSES:
            return ApiErrorCode.VALIDATION_FAILED
        if status_code in _DEPENDENCY_STATUSES:
            return ApiErrorCode.DEPENDENCY_UNAVAILABLE
        return ApiErrorCode.INTERNAL_ERROR


async def _read_body(iterator: AsyncIterator[bytes]) -> bytes:
    """Collect one bounded response body already produced by FastAPI.

    Returns:
        Serialized response bytes.
    """
    return b"".join([chunk async for chunk in iterator])


def _response_with_body(response: Response, body: bytes) -> Response:
    """Rebuild a response while preserving repeated non-content headers.

    Returns:
        Response with the supplied serialized body.
    """
    rebuilt = Response(
        content=body,
        status_code=response.status_code,
        media_type="application/json",
        background=response.background,
    )
    for name, value in response.raw_headers:
        if name.lower() not in {b"content-length", b"content-type"}:
            rebuilt.raw_headers.append((name, value))
    return rebuilt


class _CanonicalEnvelopeMiddleware(BaseHTTPMiddleware):
    """Wrap every non-stream JSON response in ``ApiResponse v1``."""

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Wrap one completed HTTP response.

        Returns:
            Canonical response or the unchanged non-JSON/204 response.
        """
        response = await call_next(request)
        if request.url.path in _FRAMEWORK_PATHS:
            return response
        content_type = response.headers.get("content-type", "")
        if (
            response.status_code == _NO_CONTENT
            or "application/json" not in content_type
        ):
            return response
        body = await _read_body(cast("Any", response).body_iterator)
        try:
            payload = json.loads(body)
        except TypeError, ValueError, UnicodeDecodeError:
            return _response_with_body(response, body)
        if isinstance(payload, dict) and set(payload) == _ENVELOPE_KEYS:
            return _response_with_body(response, body)
        registry = request.app.state.api_route_contract_registry
        contract = registry.get(request.method, request.url.path)
        request_context = getattr(request.state, "api_request_context", None)
        request_id = str(getattr(request_context, "request_id", "unknown"))
        correlation_id = getattr(request_context, "correlation_id", None)
        metadata = ApiMetadata(
            request_id=request_id,
            trace_id=str(correlation_id) if correlation_id else None,
            route=contract.path if contract is not None else request.url.path,
            operation=contract.route_id if contract is not None else "api.unknown",
            side_effect=contract.side_effect if contract is not None else "read",
        )
        if _SUCCESS_MIN <= response.status_code < _ERROR_MIN:
            envelope = ApiResponse[object](
                status=ApiStatus.SUCCESS,
                message="Request completed",
                data=payload,
                metadata=metadata,
            )
        else:
            detail = payload.get("detail") if isinstance(payload, dict) else payload
            code = _error_code(detail, response.status_code)
            envelope = ApiResponse[object](
                status=ApiStatus.ERROR,
                message=code.value,
                error=ApiError(
                    code=code,
                    message=code.value,
                    request_id=request_id,
                    trace_id=str(correlation_id) if correlation_id else None,
                    retryable=response.status_code in {429, 502, 503, 504},
                ),
                metadata=metadata,
            )
        encoded = json.dumps(
            jsonable_encoder(envelope),
            separators=(",", ":"),
        ).encode("utf-8")
        return _response_with_body(response, encoded)


def get_canonical_envelope_middleware() -> type[BaseHTTPMiddleware]:
    """Return the internal canonical envelope middleware type.

    Returns:
        Middleware class for FastAPI composition.
    """
    return _CanonicalEnvelopeMiddleware


__all__ = ("get_canonical_envelope_middleware",)
