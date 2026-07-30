"""Focused builders for Trading-owned standard operation responses."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter_ns
from typing import Any, Literal, TypeVar, cast

from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_common_error_catalog,
    get_standard_response_type,
    validate_id,
)

type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

type JsonValue = Any
type ResponseMetadata = Any

T = TypeVar("T")


def _safe_trace_id(value: str | None, prefix: str) -> str:
    """Return a valid trace identifier or a fresh bounded fallback."""
    if value is not None:
        try:
            return validate_id(value, expected_prefix=prefix)
        except Exception:  # noqa: BLE001 - invalid trace input uses a safe fallback.
            value = None
    return generate_id(prefix)


def _metadata(
    operation: str,
    *,
    risk_level: RiskLevel,
    request_id: str | None,
    correlation_id: str | None,
    started_at: int,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    places_trade: bool,
    requires_network: bool,
    extensions: Mapping[str, object] | None,
) -> ResponseMetadata:
    """Build bounded Trading response metadata.

    Returns:
        Validated Utils response metadata.
    """
    return build_response_metadata(
        name=operation,
        domain="trading",
        risk_level=risk_level,
        request_id=_safe_trace_id(request_id, "req"),
        correlation_id=(
            _safe_trace_id(correlation_id, "cor")
            if correlation_id is not None
            else None
        ),
        start_time=started_at,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=places_trade,
        requires_network=requires_network,
        extensions=cast("Mapping[str, JsonValue]", extensions),
    )


def success_trading_response(
    data: T | None,
    *,
    operation: str = "trading.operation",
    message: str = "Trading operation completed",
    risk_level: RiskLevel = "low",
    request_id: str | None = None,
    correlation_id: str | None = None,
    started_at: int | None = None,
    read_only: bool = True,
    writes_file: bool = False,
    modifies_database: bool = False,
    places_trade: bool = False,
    requires_network: bool = False,
    legacy_status: str | None = None,
    extensions: Mapping[str, object] | None = None,
) -> StandardResponse[T]:
    """Build a successful Trading response containing raw result data.

    Returns:
        Standard success response containing ``data``.
    """
    response_extensions = dict(extensions or {})
    if legacy_status is not None:
        response_extensions["legacy_status"] = legacy_status
    response_type: Any = get_standard_response_type()
    return response_type(
        status="success",
        message=message,
        data=data,
        error=None,
        metadata=_metadata(
            operation,
            risk_level=risk_level,
            request_id=request_id,
            correlation_id=correlation_id,
            started_at=started_at or perf_counter_ns(),
            read_only=read_only,
            writes_file=writes_file,
            modifies_database=modifies_database,
            places_trade=places_trade,
            requires_network=requires_network,
            extensions=response_extensions,
        ),
    )


def error_trading_response(
    *,
    code: str,
    details: Mapping[str, object],
    operation: str = "trading.operation",
    message: str = "Trading operation failed",
    risk_level: RiskLevel = "high",
    request_id: str | None = None,
    correlation_id: str | None = None,
    started_at: int | None = None,
    read_only: bool = True,
    writes_file: bool = False,
    modifies_database: bool = False,
    places_trade: bool = False,
    requires_network: bool = False,
    legacy_status: str | None = None,
    extensions: Mapping[str, object] | None = None,
) -> StandardResponse[T]:
    """Build a failed Trading response with redacted structured evidence.

    Returns:
        Standard error response with ``data=None``.

    Raises:
        RuntimeError: If the Utils response invariant omits its error payload.
    """
    response_extensions = dict(extensions or {})
    if legacy_status is not None:
        response_extensions["legacy_status"] = legacy_status
    metadata = _metadata(
        operation,
        risk_level=risk_level,
        request_id=request_id,
        correlation_id=correlation_id,
        started_at=started_at or perf_counter_ns(),
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=places_trade,
        requires_network=requires_network,
        extensions=response_extensions,
    )
    template: Any = error_response(
        code="INTERNAL_ERROR",
        details={},
        message=message,
        metadata=metadata,
        catalog=get_common_error_catalog(),
    )
    if template.error is None:  # pragma: no cover - Utils invariant.
        raise RuntimeError("Utils error response omitted StandardError")
    standard_error_type = type(template.error)
    response_type: Any = get_standard_response_type()
    return response_type(
        status="error",
        message=message,
        data=None,
        error=standard_error_type(
            code=code,
            details=cast("Mapping[str, JsonValue]", details),
        ),
        metadata=metadata,
    )


__all__ = ["error_trading_response", "success_trading_response"]
