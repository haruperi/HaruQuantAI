"""Standard response boundaries for Simulation public operations."""

from __future__ import annotations

import functools
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Literal, Protocol, cast, overload

from app.composition.logging import get_logger
from app.contracts.common.models import (
    build_response_metadata,
    error_response,
    exception_response,
    success_response,
)
from app.kernel.identity import generate_id, validate_id
from app.services.simulator.errors.catalog import SIM_ERROR_CATALOG
from app.services.simulator.errors.exception import SimulationError

type JsonValue = Any
type ResponseMetadata = Any


class _ErrorLike(Protocol):
    """Structural error evidence used by the internal response unwrapping seam."""

    @property
    def code(self) -> str:
        """Return the stable error code."""
        ...

    @property
    def details(self) -> Mapping[str, object]:
        """Return bounded error details."""
        ...


class _MetadataLike(Protocol):
    """Structural trace metadata used by the response unwrapping seam."""

    @property
    def request_id(self) -> str:
        """Return the request identifier."""
        ...

    @property
    def correlation_id(self) -> str | None:
        """Return the optional correlation identifier."""
        ...


class StandardResponse[T](Protocol):
    """Structural subset of the Utils response contract consumed here."""

    @property
    def status(self) -> str:
        """Return response status."""
        ...

    @property
    def message(self) -> str:
        """Return the bounded response message."""
        ...

    @property
    def data(self) -> T | None:
        """Return successful response data."""
        ...

    @property
    def error(self) -> _ErrorLike | None:
        """Return optional error evidence."""
        ...

    @property
    def metadata(self) -> _MetadataLike:
        """Return response metadata."""
        ...


RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)
_UUID_VERSION = 4


def _trace_context(
    args: tuple[object, ...], kwargs: Mapping[str, object]
) -> tuple[str, str | None]:
    """Find valid request and correlation identifiers in operation arguments.

    Args:
        args: Positional operation arguments.
        kwargs: Keyword operation arguments.

    Returns:
        A valid request identifier and optional correlation identifier. Fresh
        identifiers are generated when callers do not provide valid values.
    """
    request_id: object | None = None
    correlation_id: object | None = None
    for value in (*args, *kwargs.values()):
        if isinstance(value, str) and value.startswith("req-"):
            request_id = value
        elif isinstance(value, str) and value.startswith("cor-"):
            correlation_id = value
        elif isinstance(value, Mapping):
            request_id = value.get("request_id", request_id)
            correlation_id = value.get("correlation_id", correlation_id)
        else:
            request_id = getattr(value, "request_id", request_id)
            correlation_id = getattr(value, "correlation_id", correlation_id)
        if request_id is not None:
            break
    if not _is_trace_id(request_id, "req"):
        request_id = generate_id("req")
    else:
        request_id = validate_id(cast("str", request_id), expected_prefix="req")
    if correlation_id is not None and not _is_trace_id(correlation_id, "cor"):
        correlation_id = None
    return request_id, cast("str | None", correlation_id)


def _is_trace_id(value: object, prefix: str) -> bool:
    """Return whether a value is one canonical prefixed UUID4 identifier."""
    if not isinstance(value, str) or not value.startswith(f"{prefix}-"):
        return False
    try:
        parsed = uuid.UUID(value.removeprefix(f"{prefix}-"))
    except ValueError:
        return False
    return parsed.version == _UUID_VERSION and str(parsed) == value.removeprefix(
        f"{prefix}-"
    )


def _metadata(
    *,
    operation: str,
    risk_level: RiskLevel,
    request_id: str,
    correlation_id: str | None,
    start_time: int,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    requires_network: bool,
) -> ResponseMetadata:
    """Build common Simulation response metadata.

    Returns:
        Metadata describing the bounded operation and its safety properties.
    """
    return build_response_metadata(
        name=operation,
        domain="simulation",
        risk_level=risk_level,
        request_id=request_id,
        correlation_id=correlation_id,
        start_time=start_time,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=False,
        requires_network=requires_network,
    )


def _error_details(error: SimulationError) -> Mapping[str, JsonValue]:
    """Preserve safe Simulation error evidence for the response branch.

    Returns:
        Safe, serializable error details for the response envelope.
    """
    details: dict[str, JsonValue] = {
        str(key): cast("JsonValue", value) for key, value in error.details.items()
    }
    if error.request_id is not None:
        details["request_id"] = error.request_id
    if error.correlation_id is not None:
        details["correlation_id"] = error.correlation_id
    return details


def _response[T](
    function: Callable[..., T],
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    start_time: int,
    *,
    operation: str,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    requires_network: bool,
) -> StandardResponse[T]:
    """Execute one synchronous raw operation and construct its response.

    Returns:
        A success or error response containing the operation result or evidence.
    """
    request_id, correlation_id = _trace_context(args, kwargs)

    def metadata() -> ResponseMetadata:
        """Build response metadata after the bounded operation completes.

        Returns:
            Metadata describing the bounded operation.
        """
        return _metadata(
            operation=operation,
            risk_level=risk_level,
            request_id=request_id,
            correlation_id=correlation_id,
            start_time=start_time,
            read_only=read_only,
            writes_file=writes_file,
            modifies_database=modifies_database,
            requires_network=requires_network,
        )

    try:
        value = function(*args, **kwargs)
    except SimulationError as error:
        return error_response(
            code=error.code,
            details=_error_details(error),
            message=error.message,
            metadata=metadata(),
            catalog=cast("Any", SIM_ERROR_CATALOG),
        )
    except Exception as error:
        logger.exception("Unexpected Simulation operation failure: %s", operation)
        return error_response(
            code="SIM_INTERNAL_ERROR",
            details={
                "detail": "UNEXPECTED_EXCEPTION",
                "failure_type": type(error).__name__,
            },
            message="simulation operation failed with an unexpected internal error",
            metadata=metadata(),
            catalog=cast("Any", SIM_ERROR_CATALOG),
        )
    return success_response(
        value,
        message=f"{function.__name__} completed successfully",
        metadata=metadata(),
    )


def guard_operation[**P, T](
    function: Callable[P, T],
    *,
    operation: str,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
    requires_network: bool = False,
) -> Callable[P, StandardResponse[T]]:
    """Wrap one synchronous Simulation operation in StandardResponse.

    Returns:
        A callable that returns the canonical response envelope.
    """

    @functools.wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> StandardResponse[T]:
        return _response(
            cast("Callable[..., T]", function),
            args,
            kwargs,
            time.perf_counter_ns(),
            operation=operation,
            risk_level=risk_level,
            read_only=read_only,
            writes_file=writes_file,
            modifies_database=modifies_database,
            requires_network=requires_network,
        )

    return wrapper


def guard_async_operation[**P, T](
    function: Callable[P, Awaitable[T]],
    *,
    operation: str,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
    requires_network: bool = False,
) -> Callable[P, Awaitable[StandardResponse[T]]]:
    """Wrap one asynchronous Simulation operation in StandardResponse.

    Returns:
        An asynchronous callable that returns the canonical response envelope.
    """

    @functools.wraps(function)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> StandardResponse[T]:
        start_time = time.perf_counter_ns()
        request_id, correlation_id = _trace_context(args, kwargs)

        def metadata() -> ResponseMetadata:
            """Build response metadata after the bounded operation completes.

            Returns:
                Metadata describing the bounded operation.
            """
            return _metadata(
                operation=operation,
                risk_level=risk_level,
                request_id=request_id,
                correlation_id=correlation_id,
                start_time=start_time,
                read_only=read_only,
                writes_file=writes_file,
                modifies_database=modifies_database,
                requires_network=requires_network,
            )

        try:
            value = await function(*args, **kwargs)
        except SimulationError as error:
            return error_response(
                code=error.code,
                details=_error_details(error),
                message=error.message,
                metadata=metadata(),
                catalog=cast("Any", SIM_ERROR_CATALOG),
            )
        except Exception as error:  # noqa: BLE001 - outer fail-closed boundary.
            return exception_response(
                SimulationError("SIM_INTERNAL_ERROR", "Simulation failed safely"),
                message="simulation operation failed with an unexpected internal error",
                metadata=metadata(),
                catalog=cast("Any", SIM_ERROR_CATALOG),
                extensions={"failure_type": type(error).__name__},
            )
        return success_response(
            value,
            message=f"{function.__name__} completed successfully",
            metadata=metadata(),
        )

    return wrapper


def operation_guard[**P, T](
    **settings: object,
) -> Callable[[Callable[P, T]], Callable[P, StandardResponse[T]]]:
    """Return a decorator for synchronous Simulation methods.

    Returns:
        A decorator that applies the canonical response boundary.
    """

    def decorate(
        function: Callable[P, T],
    ) -> Callable[P, StandardResponse[T]]:
        return cast(
            "Callable[P, StandardResponse[T]]",
            guard_operation(function, **settings),  # type: ignore[arg-type]
        )

    return decorate


def async_operation_guard[**P, T](
    **settings: object,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[StandardResponse[T]]]]:
    """Return a decorator for asynchronous Simulation methods.

    Returns:
        A decorator that applies the canonical asynchronous response boundary.
    """

    def decorate(
        function: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[StandardResponse[T]]]:
        return cast(
            "Callable[P, Awaitable[StandardResponse[T]]]",
            guard_async_operation(function, **settings),  # type: ignore[arg-type]
        )

    return decorate


@overload
def unwrap_simulation_response[T](
    response: StandardResponse[T], *, operation: str
) -> T: ...


@overload
def unwrap_simulation_response(response: object, *, operation: str) -> object: ...


def unwrap_simulation_response(response: object, *, operation: str) -> object:
    """Unwrap one successful Simulation response without nesting it.

    Args:
        response: Response returned by a migrated Simulation operation.
        operation: Consuming operation name used in safe diagnostics.

    Returns:
        The exact raw value stored in ``response.data``.

    Raises:
        SimulationError: If the response reports a domain failure or has no
            valid error evidence.
    """
    if not all(hasattr(response, field) for field in ("status", "metadata")):
        return response
    envelope = cast("StandardResponse[object]", response)
    if envelope.status == "success":
        return envelope.data
    if envelope.error is not None:
        raise SimulationError(
            envelope.error.code,
            envelope.message,
            details=envelope.error.details,
            request_id=envelope.metadata.request_id,
            correlation_id=envelope.metadata.correlation_id,
        )
    raise SimulationError(
        "SIM_INTERNAL_ERROR",
        f"{operation} returned an invalid response",
    )


__all__ = [
    "async_operation_guard",
    "guard_async_operation",
    "guard_operation",
    "operation_guard",
    "unwrap_simulation_response",
]
