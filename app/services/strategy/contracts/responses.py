"""Private Strategy response construction and nested-response adapters."""

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Callable, Mapping
from typing import Any, Literal, ParamSpec, TypeVar, cast, overload

from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_logger,
    success_response,
    validate_id,
)

type StandardResponse[T] = Any

type JsonValue = Any
type ResponseMetadata = Any
type StandardResponse[T] = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

_P = ParamSpec("_P")
_T = TypeVar("_T")


class StrategyOperationError(Exception):
    """Known, safe Strategy failure used inside public boundaries."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Mapping[str, JsonValue] | None = None,
        *,
        request_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize one bounded Strategy failure.

        Args:
            code: Approved Strategy error code.
            message: Safe bounded failure message.
            details: Safe structured failure evidence.
            request_id: Optional request trace identifier.
            correlation_id: Optional correlation identifier.
        """
        self.code = str(code)
        self.message = message
        self.details = dict(details or {})
        self.request_id = request_id
        self.correlation_id = correlation_id
        super().__init__(self.code)


def _trace_context(
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
) -> tuple[str, str | None]:
    """Find the first caller-owned trace context or create one.

    Returns:
        Canonical request and optional correlation identifiers.
    """
    for value in (*args, *kwargs.values()):
        request_id = getattr(value, "request_id", None)
        if isinstance(request_id, str):
            correlation_id = getattr(value, "correlation_id", None)
            try:
                canonical_request = validate_id(request_id, expected_prefix="req")
            except Exception:
                canonical_request = generate_id("req")
            canonical_correlation = None
            if isinstance(correlation_id, str):
                try:
                    canonical_correlation = validate_id(
                        correlation_id, expected_prefix="cor"
                    )
                except Exception:
                    canonical_correlation = generate_id("cor")
            return canonical_request, canonical_correlation
    return generate_id("req"), None


def _operation_metadata(
    function: Callable[..., object],
    args: tuple[object, ...],
    kwargs: Mapping[str, object],
    start_time: int,
) -> ResponseMetadata:
    """Build operation metadata from the Strategy ownership boundary.

    Returns:
        Utils-owned response metadata for this operation.
    """
    module = function.__module__
    operation = f"{module.removeprefix('app.services.')}.{function.__name__}"
    is_mutation = module.endswith(("registry.registration", "registry.parameters"))
    is_checkpoint_write = module.endswith(
        "checkpoints.store"
    ) and function.__name__ == ("create_strategy_checkpoint")
    if is_mutation:
        risk = "high"
    elif module.endswith(("vectorized.runner", "event.runner", "signals.boundary")) or (
        ".evaluators." in module
    ):
        risk = "medium"
    else:
        risk = "low"
    request_id, correlation_id = _trace_context(args, kwargs)
    return build_response_metadata(
        name=operation,
        domain="strategy",
        risk_level=risk,
        request_id=request_id,
        correlation_id=correlation_id,
        start_time=start_time,
        read_only=not (is_mutation or is_checkpoint_write),
        writes_file=False,
        modifies_database=is_mutation or is_checkpoint_write,
        places_trade=False,
        requires_network=False,
    )


def guard_strategy_boundary(
    function: Callable[_P, _T],
) -> Callable[_P, StandardResponse[_T]]:
    """Convert one Strategy callable into a standard five-field response.

    Args:
        function: Raw Strategy implementation.

    Returns:
        A callable returning ``StandardResponse`` with the raw result in data.
    """

    @functools.wraps(function)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> StandardResponse[_T]:
        """Execute a raw Strategy operation under its response boundary.

        Returns:
            A five-field Utils ``StandardResponse``.
        """
        started = time.perf_counter_ns()

        def metadata() -> ResponseMetadata:
            """Build response metadata after the operation completes.

            Returns:
                Utils-owned response metadata.
            """
            return _operation_metadata(function, args, kwargs, started)

        try:
            raw_result = function(*args, **kwargs)
        except StrategyOperationError as error:
            from app.services.strategy.diagnostics.errors import STRATEGY_ERROR_CATALOG

            logger.info("Strategy operation returned %s", error.code)
            return error_response(
                code=error.code,
                details=error.details,
                message=error.message,
                metadata=metadata(),
                catalog=STRATEGY_ERROR_CATALOG,
            )
        except Exception as error:  # noqa: BLE001 - outer boundary is fail closed.
            from app.services.strategy.diagnostics.errors import STRATEGY_ERROR_CATALOG

            failure_type = type(error).__name__
            logger.error(
                "Unexpected %s escaped Strategy operation %s",
                failure_type,
                function.__name__,
            )
            return error_response(
                code="STRATEGY_INTERNAL_ERROR",
                details={
                    "operation": function.__name__,
                    "failure_type": failure_type,
                },
                message="strategy operation failed with an unexpected internal error",
                metadata=metadata(),
                catalog=STRATEGY_ERROR_CATALOG,
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
    wrapper.__annotations__ = {**wrapper.__annotations__, "return": response_annotation}
    return wrapper


def unwrap_strategy_response(
    response: StandardResponse[_T],
    *,
    operation: str,
) -> _T:
    """Unwrap a nested Strategy response or re-raise its safe failure.

    Returns:
        The raw response data.

    Raises:
        StrategyOperationError: If the nested response is an error.
    """
    if response.status == "success":
        return cast("_T", response.data)
    if response.error is not None:
        raise StrategyOperationError(
            response.error.code,
            response.message,
            response.error.details,
            request_id=response.metadata.request_id,
            correlation_id=response.metadata.correlation_id,
        )
    raise StrategyOperationError(
        "STRATEGY_INTERNAL_ERROR",
        "strategy operation returned an invalid response",
        {"operation": operation},
    )


@overload
def unwrap_evaluator_result(
    result: StandardResponse[_T],
    *,
    operation: str,
) -> _T: ...


@overload
def unwrap_evaluator_result(
    result: _T,
    *,
    operation: str,
) -> _T: ...


def unwrap_evaluator_result(
    result: StandardResponse[_T] | _T,
    *,
    operation: str,
) -> _T:
    """Unwrap a migrated evaluator response while tolerating raw test doubles.

    Returns:
        The raw evaluator result.
    """
    if all(hasattr(result, field) for field in ("status", "metadata")):
        return cast("_T", unwrap_strategy_response(result, operation=operation))
    return result


@overload
def unwrap_data_response(response: StandardResponse[_T], *, operation: str) -> _T: ...


@overload
def unwrap_data_response(response: _T, *, operation: str) -> _T: ...


def unwrap_data_response(
    response: StandardResponse[_T] | _T,
    *,
    operation: str,
) -> _T:
    """Translate an upstream Data response failure into Strategy ownership.

    Returns:
        The raw Data result.

    Raises:
        StrategyOperationError: If Data returned an error response.
    """
    if not all(hasattr(response, field) for field in ("status", "metadata")):
        return response
    if response.status == "success":
        return cast("_T", response.data)
    upstream_code = (
        response.error.code if response.error is not None else "INVALID_RESPONSE"
    )
    raise StrategyOperationError(
        "STRATEGY_INTERNAL_ERROR",
        "strategy data dependency failed",
        {"operation": operation, "upstream_code": upstream_code},
    )


__all__ = [
    "StrategyOperationError",
    "guard_strategy_boundary",
    "unwrap_data_response",
    "unwrap_evaluator_result",
    "unwrap_strategy_response",
]
