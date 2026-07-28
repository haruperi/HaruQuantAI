"""Standard-response boundary helpers for Analytics public operations."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, cast

from app.services.analytics.contracts.errors import (
    AnalyticsError,
    AnalyticsValidationError,
)
from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_logger,
    success_response,
    validate_id,
)

type JsonValue = Any
type ResponseMetadata = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]


@dataclass(frozen=True, slots=True)
class ErrorDefinition:
    """Immutable domain-owned error catalogue entry."""

    code: str
    domain: str
    description: str
    category: str
    severity: Literal["info", "warning", "error", "critical"]
    retryable: bool
    operator_action: str


logger = get_logger(__name__)

_ANALYTICS_ERROR_DEFINITIONS = (
    ErrorDefinition(
        code="ANALYTICS_VALIDATION_FAILED",
        domain="analytics",
        description="Analytics input or evidence validation failed",
        category="validation",
        severity="error",
        retryable=False,
        operator_action="Correct the supplied Analytics evidence",
    ),
    ErrorDefinition(
        code="ANALYTICS_EXECUTION_FAILED",
        domain="analytics",
        description="Analytics operation execution failed",
        category="execution",
        severity="critical",
        retryable=False,
        operator_action="Inspect bounded Analytics execution evidence",
    ),
)

ANALYTICS_ERROR_CATALOG = MappingProxyType(
    {definition.code: definition for definition in _ANALYTICS_ERROR_DEFINITIONS}
)

type ResponseTransform[TRaw, T] = Callable[[TRaw], tuple[T, Mapping[str, object]]]


def _resolve_identifier(value: str | None, prefix: str) -> str:
    """Resolve a valid response identifier without exposing invalid input.

    Returns:
        A valid prefixed identifier.
    """
    if value is not None:
        try:
            validate_id(value, expected_prefix=prefix)
            return value
        except Exception:
            logger.warning("Invalid Analytics response identifier was replaced")
    return generate_id(prefix)


def _metadata(
    *,
    operation: str,
    request_id: str,
    correlation_id: str | None,
    risk_level: RiskLevel,
    start_time: int,
    extensions: Mapping[str, object] | None,
) -> ResponseMetadata:
    """Build standard Analytics metadata for one completed operation.

    Returns:
        Immutable validated response metadata.
    """
    return build_response_metadata(
        name=operation,
        domain="analytics",
        risk_level=risk_level,
        request_id=request_id,
        correlation_id=correlation_id,
        start_time=start_time,
        read_only=True,
        writes_file=False,
        modifies_database=False,
        places_trade=False,
        requires_network=False,
        extensions=cast("Mapping[str, JsonValue]", extensions or {}),
    )


def run_analytics_operation[TRaw, T](
    *,
    operation: str,
    raw: Callable[[], TRaw],
    request_id: str | None = None,
    correlation_id: str | None = None,
    risk_level: RiskLevel = "low",
    extensions: Mapping[str, object] | None = None,
    transform: ResponseTransform[TRaw, T] | None = None,
) -> StandardResponse[T]:
    """Execute a raw Analytics operation and return a standard response.

    Args:
        operation: Stable qualified Analytics operation name.
        raw: Callable containing the existing raw operation behavior.
        request_id: Optional caller request identifier.
        correlation_id: Optional caller correlation identifier.
        risk_level: Static invocation-risk classification.
        extensions: Safe non-result metadata to preserve.
        transform: Optional conversion separating raw result data from extensions.

    Returns:
        A validated response containing the raw successful result in ``data``.

    Raises:
        KeyboardInterrupt: Propagated process-control interruption.
        SystemExit: Propagated process-control interruption.
    """
    start_time = time.perf_counter_ns()
    response_request_id = _resolve_identifier(request_id, "req")
    response_correlation_id = (
        _resolve_identifier(correlation_id, "cor")
        if correlation_id is not None
        else None
    )
    try:
        result = raw()
    except KeyboardInterrupt, SystemExit:
        raise
    except AnalyticsValidationError:
        logger.warning("Analytics operation validation failed")
        metadata = _metadata(
            operation=operation,
            request_id=response_request_id,
            correlation_id=response_correlation_id,
            risk_level=risk_level,
            start_time=start_time,
            extensions=extensions,
        )
        return error_response(
            code="ANALYTICS_VALIDATION_FAILED",
            details={"reason": "VALIDATION_FAILED"},
            message="Analytics validation failed",
            metadata=metadata,
            catalog=ANALYTICS_ERROR_CATALOG,
        )
    except AnalyticsError:
        logger.exception("Analytics operation execution failed")
        metadata = _metadata(
            operation=operation,
            request_id=response_request_id,
            correlation_id=response_correlation_id,
            risk_level=risk_level,
            start_time=start_time,
            extensions=extensions,
        )
        return error_response(
            code="ANALYTICS_EXECUTION_FAILED",
            details={"reason": "EXECUTION_FAILED"},
            message="Analytics execution failed",
            metadata=metadata,
            catalog=ANALYTICS_ERROR_CATALOG,
        )
    except Exception:
        logger.exception("Unexpected Analytics operation failure")
        metadata = _metadata(
            operation=operation,
            request_id=response_request_id,
            correlation_id=response_correlation_id,
            risk_level=risk_level,
            start_time=start_time,
            extensions=extensions,
        )
        return error_response(
            code="ANALYTICS_EXECUTION_FAILED",
            details={"reason": "UNEXPECTED_EXCEPTION"},
            message="Analytics execution failed",
            metadata=metadata,
            catalog=ANALYTICS_ERROR_CATALOG,
        )

    response_data: T = cast("T", result)
    response_extensions = dict(extensions or {})
    if transform is not None:
        response_data, transform_extensions = transform(result)
        response_extensions.update(transform_extensions)
    metadata = _metadata(
        operation=operation,
        request_id=response_request_id,
        correlation_id=response_correlation_id,
        risk_level=risk_level,
        start_time=start_time,
        extensions=response_extensions,
    )
    return success_response(
        response_data,
        message="Analytics operation completed",
        metadata=metadata,
    )


__all__ = [
    "ANALYTICS_ERROR_CATALOG",
    "run_analytics_operation",
]
