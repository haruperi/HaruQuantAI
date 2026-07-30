"""Secret-safe request telemetry middleware."""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Callable, Mapping
from typing import Any, Final, Protocol, cast, override

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.services.api.middleware.context import CANONICAL_CONTEXT_STATE_KEY
from app.utils import (
    get_default_redaction_policy,
    get_logger,
    log_info,
    redact_mapping_value,
)

_REQUEST_STATE_REQUEST_ID = "request_id"
_REQUEST_STATE_CORRELATION_ID = "correlation_id"
_REQUEST_STATE_ROUTE = "path"
_REQUEST_STATE_ROUTE_ID = "route_id"
_REQUEST_STATE_STATUS = "status"
_REQUEST_STATE_DURATION_MS = "duration_ms"
_REQUEST_STATE_ERROR_CODE = "error_code"
_RESPONSE_ERROR_DETAIL_KEY: Final = "detail"
_KNOWN_REQUEST_STATE_KEY: Final = CANONICAL_CONTEXT_STATE_KEY
_DEFAULT_ERROR_CODE: Final = "INTERNAL_ERROR"
_HTTP_ERROR_STATUS_MIN: Final = 400
_HTTP_STATUS_MIN: Final = 100
_HTTP_STATUS_MAX: Final = 999
_HTTP_STATUS_FALLBACK: Final = 500

_LOGGER = get_logger(__name__)

TelemetryEvent = dict[str, object]
EventEmitter = Callable[[TelemetryEvent], None]


class _BodyIteratorResponse(Protocol):
    """Response shape used when replaying a consumed streaming body."""

    body_iterator: AsyncIterator[bytes]


def _default_emitter(event: TelemetryEvent) -> None:
    """Emit one bounded telemetry event through the shared logger."""
    log_info(_LOGGER, "api.request_telemetry", context=event)


def _read_context(request: Request) -> Mapping[str, object]:
    """Read request context if one exists; otherwise return safe defaults.

    Returns:
        The validated, bounded result.
    """
    context = getattr(request.state, _KNOWN_REQUEST_STATE_KEY, None)
    if context is None:
        return {}
    return {
        _REQUEST_STATE_REQUEST_ID: getattr(
            context,
            _REQUEST_STATE_REQUEST_ID,
            "",
        ),
        _REQUEST_STATE_CORRELATION_ID: getattr(
            context,
            _REQUEST_STATE_CORRELATION_ID,
            "",
        ),
        _REQUEST_STATE_ROUTE: getattr(context, _REQUEST_STATE_ROUTE, request.url.path),
        _REQUEST_STATE_ROUTE_ID: getattr(context, _REQUEST_STATE_ROUTE_ID, None),
    }


def _coerce_error_code(error: Exception) -> str:
    """Convert middleware execution errors to a bounded emit code.

    Returns:
        The validated, bounded result.
    """
    if isinstance(error, HTTPException):
        return str(error.detail)
    return _DEFAULT_ERROR_CODE


async def _coerce_error_code_from_response(
    response: Response,
) -> str | None:
    """Try to read a structured error code from one response body.

    Returns:
        The validated, bounded result.
    """
    if response.status_code < _HTTP_ERROR_STATUS_MIN:
        return None
    body = await _read_response_body(response)
    if not body:
        return str(response.status_code)
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError, UnicodeDecodeError:
        return str(response.status_code)
    detail = None
    if isinstance(payload, dict):
        detail = payload.get(_RESPONSE_ERROR_DETAIL_KEY)
    elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
        detail = payload[0].get(_REQUEST_STATE_ERROR_CODE)
    if isinstance(detail, str) and detail:
        return detail
    return str(response.status_code)


async def _read_response_body(response: Response) -> bytes:
    """Read and restore one response body without changing downstream output.

    Returns:
        The validated, bounded result.
    """
    body = getattr(response, "body", None)
    if isinstance(body, bytes):
        return body

    body_iterator = getattr(response, "body_iterator", None)
    if body_iterator is None:
        return b""

    chunks: list[bytes] = []
    async for chunk in body_iterator:
        if isinstance(chunk, str):
            chunks.append(chunk.encode("utf-8"))
        else:
            chunks.append(bytes(chunk))
    replay_body = b"".join(chunks)
    cast("_BodyIteratorResponse", response).body_iterator = _replay_response_body(
        replay_body
    )
    return replay_body


async def _replay_response_body(body: bytes) -> AsyncIterator[bytes]:
    """Replay one already-buffered response body.

    Yields:
        One bounded response-body chunk.
    """
    if body:
        yield body
    else:
        return


def _coerce_duration(start_time: float) -> float:
    """Render bounded duration in milliseconds.

    Returns:
        The validated, bounded result.
    """
    return (time.perf_counter() - start_time) * 1_000


def _coerce_status(value: int) -> int:
    """Return a bounded HTTP-style status code."""
    return (
        value
        if _HTTP_STATUS_MIN <= value <= _HTTP_STATUS_MAX
        else _HTTP_STATUS_FALLBACK
    )


class SecretRedactionMiddleware(BaseHTTPMiddleware):
    """Publish bounded, redacted request telemetry from ASGI responses."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        redaction_policy: object | None = None,
        event_emitter: EventEmitter | None = None,
    ) -> None:
        """Create one telemetry-redaction middleware instance."""
        super().__init__(app)
        self._policy = cast(
            "Any",
            redaction_policy or get_default_redaction_policy(),
        )
        self._event_emitter = event_emitter or _default_emitter

    @override
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process one request and emit redacted telemetry metadata.

        Returns:
            The validated, bounded result.
        """
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as error:
            status_code = 500
            if isinstance(error, HTTPException):
                status_code = error.status_code
            payload = self._build_payload(
                request=request,
                status_code=status_code,
                error_code=_coerce_error_code(error),
                start_time=start,
            )
            self._emit(payload)
            raise

        payload = self._build_payload(
            request=request,
            status_code=response.status_code,
            error_code=await _coerce_error_code_from_response(response),
            start_time=start,
        )
        self._emit(payload)
        return response

    def _emit(self, event: TelemetryEvent) -> None:
        """Emit one redacted telemetry payload via the selected sink."""
        sanitized = redact_mapping_value(event, policy=self._policy).value
        if isinstance(sanitized, dict):
            self._event_emitter(dict(sanitized))

    def _build_payload(
        self,
        *,
        request: Request,
        status_code: int,
        error_code: str | None,
        start_time: float,
    ) -> TelemetryEvent:
        """Build one bounded allowlisted telemetry payload.

        Returns:
            The validated, bounded result.
        """
        context = _read_context(request)
        request_id = str(context.get(_REQUEST_STATE_REQUEST_ID, ""))
        correlation_id = str(context.get(_REQUEST_STATE_CORRELATION_ID, ""))
        route = str(context.get(_REQUEST_STATE_ROUTE, request.url.path))
        route_id = context.get(_REQUEST_STATE_ROUTE_ID)
        normalized_status = _coerce_status(status_code)
        return {
            "method": request.method,
            "route": route,
            "route_id": route_id,
            "status": normalized_status,
            "duration_ms": _coerce_duration(start_time),
            "error_code": error_code,
            "request_id": request_id,
            "correlation_id": correlation_id,
        }


def build_secret_redaction_middleware(
    app: ASGIApp,
    *,
    redaction_policy: object | None = None,
    event_emitter: EventEmitter | None = None,
) -> object:
    """Build a configured secret-redaction middleware instance.

    Returns:
        The validated, bounded result.
    """
    return SecretRedactionMiddleware(
        app,
        redaction_policy=cast("Any", redaction_policy),
        event_emitter=event_emitter,
    )
