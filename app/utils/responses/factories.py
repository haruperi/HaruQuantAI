"""Factories for validated standard operation responses."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.utils.errors.catalog import COMMON_ERROR_CATALOG
from app.utils.errors.mapping import map_exception
from app.utils.errors.validation import require_error_definition
from app.utils.responses.models import (
    JsonValue,
    ResponseMetadata,
    RiskLevel,
    StandardError,
    StandardResponse,
)
from app.utils.responses.timing import get_execution_ms

if TYPE_CHECKING:
    from app.utils.errors.contracts import ErrorDefinition


def build_response_metadata(
    *,
    name: str,
    domain: str,
    risk_level: str,
    request_id: str,
    start_time: int,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    places_trade: bool,
    requires_network: bool,
    correlation_id: str | None = None,
    extensions: Mapping[str, JsonValue] | None = None,
) -> ResponseMetadata:
    """Build required response metadata using monotonic execution timing.

    Args:
        name: Stable qualified operation name.
        domain: Owning HaruQuantAI domain.
        risk_level: Static invocation-risk classification.
        request_id: Canonical request trace identifier.
        start_time: Starting ``time.perf_counter_ns`` value.
        read_only: Whether the operation has no externally observable mutation.
        writes_file: Whether the operation can write a file.
        modifies_database: Whether the operation can modify a database.
        places_trade: Whether the operation can place a trade.
        requires_network: Whether the operation can require network access.
        correlation_id: Optional canonical correlation trace identifier.
        extensions: Preserved operation-specific envelope metadata.

    Returns:
        Immutable validated response metadata.

    Raises:
        TypeError: If metadata or timing values have invalid types.
        ValueError: If metadata or timing invariants are violated.
        ValidationError: If trace identifiers or extensions are invalid.
    """
    return ResponseMetadata(
        name=name,
        domain=domain,
        risk_level=RiskLevel(risk_level),
        request_id=request_id,
        correlation_id=correlation_id,
        execution_ms=get_execution_ms(start_time),
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=places_trade,
        requires_network=requires_network,
        extensions=extensions or {},
    )


def success_response[T](
    data: T | None,
    *,
    message: str,
    metadata: ResponseMetadata,
) -> StandardResponse[T]:
    """Return a successful response containing the raw function result.

    Args:
        data: Raw successful result with no additional payload wrapper.
        message: Safe human-readable summary.
        metadata: Required operation metadata.

    Returns:
        Immutable successful standard response.
    """
    return StandardResponse[T](
        status="success",
        message=message,
        data=data,
        error=None,
        metadata=metadata,
    )


def error_response[T](
    *,
    code: str,
    details: Mapping[str, JsonValue],
    message: str,
    metadata: ResponseMetadata,
    catalog: Mapping[str, ErrorDefinition],
) -> StandardResponse[T]:
    """Return an error response after approving its error code.

    Args:
        code: Candidate symbolic error code.
        details: Safe structured diagnostic evidence.
        message: Safe human-readable summary.
        metadata: Required operation metadata.
        catalog: Owning domain's approved immutable error catalogue.

    Returns:
        Immutable failed standard response with ``data=None``.

    Raises:
        ValidationError: If the code is absent from the approved catalogue.
    """
    definition = require_error_definition(code, catalog)
    return StandardResponse[T](
        status="error",
        message=message,
        data=None,
        error=StandardError(code=definition.code, details=details),
        metadata=metadata,
    )


def exception_response[T](
    exception: BaseException,
    *,
    message: str,
    metadata: ResponseMetadata,
    catalog: Mapping[str, ErrorDefinition],
    extensions: Mapping[str, JsonValue] | None = None,
) -> StandardResponse[T]:
    """Map a caught exception to a secret-safe approved error response.

    Known shared or domain exceptions retain their symbolic code only when that
    code is approved by the supplied catalogue. Unknown or unapproved exceptions
    map to the common ``INTERNAL_ERROR`` definition. Raw exception text is never
    retained.

    Args:
        exception: Caught exception to normalize without retaining it.
        message: Safe human-readable summary.
        metadata: Required operation metadata.
        catalog: Owning domain's approved immutable error catalogue.
        extensions: Additional safe diagnostic details.

    Returns:
        Immutable failed standard response.

    Raises:
        CancelledError: If asynchronous cancellation is supplied.
        GeneratorExit: If generator termination is supplied.
        KeyboardInterrupt: If process interruption is supplied.
        SystemExit: If process exit is supplied.
    """
    if isinstance(
        exception,
        asyncio.CancelledError | GeneratorExit | KeyboardInterrupt | SystemExit,
    ):
        raise exception
    mapped = map_exception(exception)
    active_catalog = catalog
    if mapped["code"] not in catalog:
        active_catalog = COMMON_ERROR_CATALOG
        mapped = {
            "code": "INTERNAL_ERROR",
            "detail": "UNEXPECTED_EXCEPTION",
        }
    details: dict[str, JsonValue] = {}
    if extensions is not None:
        details.update(extensions)
    details["detail"] = mapped["detail"]
    return error_response(
        code=mapped["code"],
        details=details,
        message=message,
        metadata=metadata,
        catalog=active_catalog,
    )


__all__ = [
    "build_response_metadata",
    "error_response",
    "exception_response",
    "success_response",
]
