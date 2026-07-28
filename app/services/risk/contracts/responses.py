"""Private StandardResponse boundary helpers for Risk operations."""

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Callable, Mapping
from contextlib import suppress
from typing import ParamSpec, TypeVar, cast

from pydantic import ValidationError as PydanticValidationError

from app.services.risk.contracts.catalog import RISK_ERROR_CATALOG
from app.services.risk.contracts.enums import RiskErrorCode
from app.services.risk.contracts.errors import RiskDomainError
from app.utils import (
    ResponseMetadata,
    RiskLevel,
    StandardResponse,
    build_response_metadata,
    error_response,
    exception_response,
    generate_id,
    logger,
    success_response,
    validate_id,
)

_P = ParamSpec("_P")
_T = TypeVar("_T")


def _trace_context(
    args: tuple[object, ...], kwargs: Mapping[str, object]
) -> tuple[str, str | None]:
    """Find valid caller trace identifiers or create bounded replacements.

    Args:
        args: Positional operation arguments.
        kwargs: Keyword operation arguments.

    Returns:
        A canonical request identifier and optional correlation identifier.
    """
    for value in (*args, *kwargs.values()):
        request_id = getattr(value, "request_id", None)
        if not isinstance(request_id, str):
            continue
        try:
            canonical_request = validate_id(request_id, expected_prefix="req")
        except Exception:  # noqa: BLE001 - invalid caller trace fails closed locally.
            canonical_request = generate_id("req")
        correlation_id = getattr(value, "correlation_id", None)
        if not isinstance(correlation_id, str):
            return canonical_request, None
        try:
            return canonical_request, validate_id(correlation_id, expected_prefix="cor")
        except Exception:  # noqa: BLE001 - invalid optional trace is not propagated.
            return canonical_request, generate_id("cor")
    return generate_id("req"), None


def _operation_metadata(
    function: Callable[..., object],
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    started: int,
    *,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool,
    modifies_database: bool,
    places_trade: bool,
    requires_network: bool,
) -> ResponseMetadata:
    """Build the required Risk response metadata.

    Args:
        function: Wrapped Risk operation.
        args: Positional operation arguments.
        kwargs: Keyword operation arguments.
        started: Monotonic operation start time.
        risk_level: Static operation risk classification.
        read_only: Whether the operation has no mutation.
        writes_file: Whether the operation can write files.
        modifies_database: Whether the operation can modify a database.
        places_trade: Whether the operation can place a trade.
        requires_network: Whether the operation can require network access.

    Returns:
        Validated standard response metadata.
    """
    request_id, correlation_id = _trace_context(args, kwargs)
    return build_response_metadata(
        name=f"{function.__module__.removeprefix('app.services.')}.{function.__name__}",
        domain="risk",
        risk_level=risk_level,
        request_id=request_id,
        correlation_id=correlation_id,
        start_time=started,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=modifies_database,
        places_trade=places_trade,
        requires_network=requires_network,
    )


def guard_risk_boundary(
    *,
    risk_level: RiskLevel,
    read_only: bool,
    writes_file: bool = False,
    modifies_database: bool = False,
    places_trade: bool = False,
    requires_network: bool = False,
) -> Callable[[Callable[_P, _T]], Callable[_P, StandardResponse[_T]]]:
    """Convert one Risk operation into a five-field standard response.

    Args:
        risk_level: Static operation risk classification.
        read_only: Whether the operation has no mutation.
        writes_file: Whether the operation can write files.
        modifies_database: Whether the operation can modify a database.
        places_trade: Whether the operation can place a trade.
        requires_network: Whether the operation can require network access.

    Returns:
        A decorator that preserves the raw result in ``StandardResponse.data``.
    """

    def decorator(
        function: Callable[_P, _T],
    ) -> Callable[_P, StandardResponse[_T]]:
        @functools.wraps(function)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> StandardResponse[_T]:
            """Execute one Risk operation behind the response boundary.

            Returns:
                Standard response containing the raw result or safe error.
            """
            started = time.perf_counter_ns()

            def metadata() -> ResponseMetadata:
                """Build response metadata after execution completes.

                Returns:
                    Validated response metadata.
                """
                return _operation_metadata(
                    function,
                    args,
                    kwargs,
                    started,
                    risk_level=risk_level,
                    read_only=read_only,
                    writes_file=writes_file,
                    modifies_database=modifies_database,
                    places_trade=places_trade,
                    requires_network=requires_network,
                )

            try:
                raw_result = function(*args, **kwargs)
            except RiskDomainError as error:
                logger.info("Risk operation returned %s", error.risk_code.value)
                return error_response(
                    code=error.risk_code.value,
                    details={"diagnostic": error.details},
                    message=RISK_ERROR_CATALOG[error.risk_code.value].description,
                    metadata=metadata(),
                    catalog=RISK_ERROR_CATALOG,
                )
            except (PydanticValidationError, TypeError, ValueError) as error:
                logger.info("Risk operation failed validation")
                return error_response(
                    code=RiskErrorCode.VALIDATION_FAILED.value,
                    details={"failure_type": type(error).__name__},
                    message=RISK_ERROR_CATALOG[
                        RiskErrorCode.VALIDATION_FAILED.value
                    ].description,
                    metadata=metadata(),
                    catalog=RISK_ERROR_CATALOG,
                )
            except Exception as error:  # noqa: BLE001 - outer fail-closed boundary.
                logger.error(
                    "Unexpected %s escaped Risk operation %s",
                    type(error).__name__,
                    function.__name__,
                )
                return exception_response(
                    RiskDomainError(
                        RiskErrorCode.UNKNOWN_ERROR,
                        "UNEXPECTED_EXCEPTION",
                    ),
                    message=RISK_ERROR_CATALOG[
                        RiskErrorCode.UNKNOWN_ERROR.value
                    ].description,
                    metadata=metadata(),
                    catalog=RISK_ERROR_CATALOG,
                    extensions={
                        "operation": function.__name__,
                        "failure_type": type(error).__name__,
                    },
                )

            return success_response(
                raw_result,
                message=f"{function.__name__} completed successfully",
                metadata=metadata(),
            )

        signature = inspect.signature(function)
        annotation = signature.return_annotation
        if annotation is inspect.Signature.empty:
            annotation = "object"
        response_annotation = (
            f"StandardResponse[{annotation}]"
            if isinstance(annotation, str)
            else f"StandardResponse[{annotation!r}]"
        )
        wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
            return_annotation=response_annotation
        )
        wrapper.__annotations__ = {
            **wrapper.__annotations__,
            "return": response_annotation,
        }
        return wrapper

    return decorator


def unwrap_risk_response(
    response: StandardResponse[_T],
    *,
    operation: str,
) -> _T:
    """Unwrap a Risk response or raise its safe domain failure.

    Args:
        response: Response returned by a migrated Risk operation.
        operation: Stable operation name for invalid-response diagnostics.

    Returns:
        The exact raw successful result, including ``None`` when valid.

    Raises:
        RiskDomainError: If the response is an error or structurally invalid.
    """
    if not isinstance(response, StandardResponse):
        raise RiskDomainError(RiskErrorCode.UNKNOWN_ERROR, "INVALID_RESPONSE")
    if response.status == "success":
        return cast("_T", response.data)
    code = RiskErrorCode.UNKNOWN_ERROR
    if response.error is not None:
        with suppress(ValueError):
            code = RiskErrorCode(response.error.code)
    raise RiskDomainError(code, operation.upper().replace(".", "_"))


__all__ = ["guard_risk_boundary", "unwrap_risk_response"]
