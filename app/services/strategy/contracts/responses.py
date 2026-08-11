"""Private Strategy response construction and nested-response adapters."""

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Callable, Mapping
from typing import Any, Literal, ParamSpec, Protocol, TypeGuard, TypeVar, cast

from app.utils import (
    build_response_metadata,
    error_response,
    generate_id,
    get_logger,
    get_standard_response_type,
    success_response,
    validate_id,
)

type JsonValue = Any
type ResponseMetadata = Any
RiskLevel = Literal["none", "low", "medium", "high", "critical"]

logger = get_logger(__name__)

_P = ParamSpec("_P")
_T = TypeVar("_T")
_STANDARD_RESPONSE_TYPE = get_standard_response_type()


class _ResponseError(Protocol):
    """Structural view of one Utils-owned standard error."""

    @property
    def code(self) -> str:
        """Return the stable error code.

        Returns:
            Stable error code string.
        """

    @property
    def details(self) -> Mapping[str, JsonValue]:
        """Return bounded structured error details.

        Returns:
            Bounded structured error details mapping.
        """


class _ResponseMetadata(Protocol):
    """Structural view of trace fields in Utils-owned response metadata."""

    @property
    def request_id(self) -> str:
        """Return the canonical request identifier.

        Returns:
            Canonical request identifier string.
        """

    @property
    def correlation_id(self) -> str | None:
        """Return the optional correlation identifier.

        Returns:
            Optional correlation identifier string.
        """


class StandardResponse[T](Protocol):
    """Private structural view of the Utils-owned response contract."""

    @property
    def status(self) -> Literal["success", "error"]:
        """Return the response status.

        Returns:
            Response status literal.
        """

    @property
    def message(self) -> str:
        """Return the bounded response message.

        Returns:
            Bounded response message string.
        """

    @property
    def data(self) -> T | None:
        """Return successful response data.

        Returns:
            Successful response data value.
        """

    @property
    def error(self) -> _ResponseError | None:
        """Return structured failure evidence.

        Returns:
            Structured failure evidence error instance.
        """

    @property
    def metadata(self) -> _ResponseMetadata:
        """Return operation metadata.

        Returns:
            Operation metadata instance.
        """


def _is_standard_response(value: object) -> TypeGuard[StandardResponse[object]]:
    """Return whether ``value`` is the Utils-owned runtime response type.

    Args:
        value: Candidate response value.

    Returns:
        Whether the value is a canonical Utils standard response.
    """
    return isinstance(value, _STANDARD_RESPONSE_TYPE)


def _build_error_response[T](
    *,
    code: str,
    details: Mapping[str, JsonValue],
    message: str,
    metadata: ResponseMetadata,
    catalog: Mapping[str, object],
) -> StandardResponse[T]:
    """Build one Utils response through Strategy's structural adapter.

    Args:
        code: Approved Strategy error code.
        details: Bounded structured error evidence.
        message: Safe response message.
        metadata: Utils-owned operation metadata.
        catalog: Structurally compatible Strategy error catalogue.

    Returns:
        Canonical Utils response exposed through the private structural view.
    """
    build_error = cast("Callable[..., object]", error_response)
    return cast(
        "StandardResponse[T]",
        build_error(
            code=code,
            details=details,
            message=message,
            metadata=metadata,
            catalog=catalog,
        ),
    )


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
            except Exception as error:
                if not str(getattr(error, "code", "")).startswith("IDENTIFIER_"):
                    raise
                canonical_request = generate_id("req")
            canonical_correlation = None
            if isinstance(correlation_id, str):
                try:
                    canonical_correlation = validate_id(
                        correlation_id, expected_prefix="cor"
                    )
                except Exception as error:
                    if not str(getattr(error, "code", "")).startswith("IDENTIFIER_"):
                        raise
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
    is_mutation = module.endswith(
        ("registry.registration", "registry.parameters", "registry.optimization")
    )
    is_checkpoint_write = (
        module.endswith("checkpoints.store")
        and function.__name__ == "create_strategy_checkpoint"
    )
    is_audit_write = (
        module.endswith("proposal_intake.evaluation")
        and function.__name__ == "evaluate_strategy_proposal"
    )
    if is_mutation:
        risk = "high"
    elif module.endswith(
        (
            "vectorized.runner",
            "event.runner",
            "signals.boundary",
            "proposal_intake.evaluation",
        )
    ) or (".evaluators." in module):
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
        read_only=not (is_mutation or is_checkpoint_write or is_audit_write),
        writes_file=False,
        modifies_database=is_mutation or is_checkpoint_write or is_audit_write,
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
            return _build_error_response(
                code=error.code,
                details=error.details,
                message=error.message,
                metadata=metadata(),
                catalog=STRATEGY_ERROR_CATALOG,
            )
        except Exception as error:
            from app.services.strategy.diagnostics.errors import STRATEGY_ERROR_CATALOG

            failure_type = type(error).__name__
            logger.exception(
                "Unexpected %s escaped Strategy operation %s",
                failure_type,
                function.__name__,
            )
            return _build_error_response(
                code="STRATEGY_INTERNAL_ERROR",
                details={
                    "operation": function.__name__,
                    "failure_type": failure_type,
                },
                message="strategy operation failed with an unexpected internal error",
                metadata=metadata(),
                catalog=STRATEGY_ERROR_CATALOG,
            )
        return cast(
            "StandardResponse[_T]",
            success_response(
                raw_result,
                message=f"{function.__name__} completed successfully",
                metadata=metadata(),
            ),
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


def unwrap_evaluator_result(
    result: StandardResponse[_T] | _T,
    *,
    operation: str,
) -> _T:
    """Unwrap a migrated evaluator response while tolerating raw test doubles.

    Returns:
        The raw evaluator result.
    """
    if _is_standard_response(result):
        typed = cast("StandardResponse[_T]", result)
        return unwrap_strategy_response(typed, operation=operation)
    return cast("_T", result)


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
    if not _is_standard_response(response):
        return cast("_T", response)
    typed = cast("StandardResponse[_T]", response)
    if typed.status == "success":
        return cast("_T", typed.data)
    upstream_code = typed.error.code if typed.error is not None else "INVALID_RESPONSE"
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
