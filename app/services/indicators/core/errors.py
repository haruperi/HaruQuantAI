"""Deterministic Core MVP error catalogue and structured domain exception."""

from __future__ import annotations

import functools
import inspect
import math
import re
import time
from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Final, ParamSpec, TypeVar, cast

from app.services.indicators.core.error_catalog import INDICATOR_ERROR_CATALOG
from app.utils import (
    HaruQuantError,
    JsonValue,
    ResponseMetadata,
    RiskLevel,
    StandardResponse,
    build_response_metadata,
    error_response,
    exception_response,
    generate_id,
    logger,
    redact_text_value,
    success_response,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")

_MESSAGE_MAX_LENGTH: Final[int] = 256
_DETAILS_MAX_KEYS: Final[int] = 16
_DETAILS_KEY_MAX_LENGTH: Final[int] = 64
_DETAILS_STRING_MAX_LENGTH: Final[int] = 256
_DETAILS_TUPLE_MAX_ITEMS: Final[int] = 20
_SNAKE_CASE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*$")


class IndicatorErrorCode(StrEnum):
    """Exactly the approved Core MVP Indicators error codes."""

    IND_INVALID_CONFIG = "IND_INVALID_CONFIG"
    IND_INVALID_PARAMETER = "IND_INVALID_PARAMETER"
    IND_UNSUPPORTED_INDICATOR = "IND_UNSUPPORTED_INDICATOR"
    IND_UNSUPPORTED_TIMEFRAME = "IND_UNSUPPORTED_TIMEFRAME"
    IND_UNSUPPORTED_DTYPE = "IND_UNSUPPORTED_DTYPE"
    IND_INVALID_INPUT_SCHEMA = "IND_INVALID_INPUT_SCHEMA"
    IND_MISSING_REQUIRED_COLUMN = "IND_MISSING_REQUIRED_COLUMN"
    IND_INVALID_OUTPUT_COLUMN = "IND_INVALID_OUTPUT_COLUMN"
    IND_OUTPUT_COLUMN_CONFLICT = "IND_OUTPUT_COLUMN_CONFLICT"
    IND_INVALID_OUTPUT_MODE = "IND_INVALID_OUTPUT_MODE"
    IND_INPUT_MUTATION_DETECTED = "IND_INPUT_MUTATION_DETECTED"
    IND_DUPLICATE_TIMESTAMP = "IND_DUPLICATE_TIMESTAMP"
    IND_NON_MONOTONIC_TIME = "IND_NON_MONOTONIC_TIME"
    IND_AMBIGUOUS_TIMESTAMP = "IND_AMBIGUOUS_TIMESTAMP"
    IND_INVALID_TIMEZONE = "IND_INVALID_TIMEZONE"
    IND_INVALID_OHLC = "IND_INVALID_OHLC"
    IND_INSUFFICIENT_DATA = "IND_INSUFFICIENT_DATA"
    IND_LOOKAHEAD_RISK = "IND_LOOKAHEAD_RISK"
    IND_FORMULA_VERSION_MISMATCH = "IND_FORMULA_VERSION_MISMATCH"
    IND_RESOURCE_LIMIT_EXCEEDED = "IND_RESOURCE_LIMIT_EXCEEDED"
    IND_PARTIAL_RESULT = "IND_PARTIAL_RESULT"
    IND_INTERNAL_ERROR = "IND_INTERNAL_ERROR"


def _validate_message(message: str) -> str:
    """Validate and redact a deterministic Indicators error message.

    Args:
        message: Candidate safe message.

    Returns:
        Redacted, length-bounded message text.

    Raises:
        ValueError: If the message is empty, blank, or exceeds the maximum
            approved length.
    """
    if not message or not message.strip():
        raise ValueError("message must be a non-empty string")
    if len(message) > _MESSAGE_MAX_LENGTH:
        raise ValueError("message exceeds the maximum length")
    return str(redact_text_value(message).value)


def _validate_scalar(value: object) -> object:
    """Validate and redact one bounded JSON-scalar detail value.

    Args:
        value: Candidate scalar value.

    Returns:
        The redacted, validated scalar.

    Raises:
        ValueError: If a string or float value violates its approved bound.
        TypeError: If the value is not an approved JSON-scalar type.
    """
    if value is None or isinstance(value, bool | int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("details float value must be finite")
        return value
    if isinstance(value, str):
        if len(value) > _DETAILS_STRING_MAX_LENGTH:
            raise ValueError("details string value exceeds the maximum length")
        return str(redact_text_value(value).value)
    raise TypeError("details values must be JSON scalars")


def _validate_detail_value(value: object) -> object:
    """Validate one bounded detail value or scalar tuple.

    Args:
        value: Candidate JSON-scalar or tuple-of-scalars value.

    Returns:
        The redacted, validated value.

    Raises:
        ValueError: If a tuple exceeds the maximum approved item count.
        TypeError: If the value is not an approved JSON-scalar type.
    """
    if isinstance(value, tuple):
        if len(value) > _DETAILS_TUPLE_MAX_ITEMS:
            raise ValueError("details tuple exceeds the maximum item count")
        return tuple(_validate_scalar(item) for item in value)
    return _validate_scalar(value)


def _validate_details(
    details: Mapping[str, object] | None,
) -> Mapping[str, object]:
    """Validate, redact, and freeze bounded structured error details.

    Args:
        details: Candidate flat mapping of JSON-scalar or scalar-tuple values.

    Returns:
        Immutable redacted details mapping.

    Raises:
        ValueError: If keys, counts, or values violate the approved shape.
        TypeError: If a value is not an approved JSON-scalar type.
    """
    if details is None:
        return MappingProxyType({})
    if len(details) > _DETAILS_MAX_KEYS:
        raise ValueError("details exceeds the maximum key count")
    validated: dict[str, object] = {}
    for key, value in details.items():
        if not isinstance(key, str) or len(key) > _DETAILS_KEY_MAX_LENGTH:
            raise ValueError("details key exceeds the maximum length")
        if not _SNAKE_CASE_PATTERN.fullmatch(key):
            raise ValueError("details key must be lowercase snake_case")
        validated[key] = _validate_detail_value(value)
    return MappingProxyType(validated)


class IndicatorError(Exception):
    """Deterministic, redacted failure raised at the Indicators public boundary.

    Attributes:
        code: Approved ``IndicatorErrorCode`` identifying the failure.
        message: Redacted, deterministic, length-bounded safe message.
        details: Immutable redacted flat diagnostic mapping.
    """

    def __init__(
        self,
        code: IndicatorErrorCode,
        message: str,
        details: Mapping[str, object] | None = None,
    ) -> None:
        """Initialize a redacted deterministic Indicators error.

        Args:
            code: Approved error code identifying the failure category.
            message: Non-empty deterministic safe message, at most 256
                characters.
            details: Optional flat mapping of at most 16 lowercase
                snake_case keys, each at most 64 characters, with
                JSON-scalar values or tuples of at most 20 JSON scalars.

        Raises:
            ValueError: If the message or details violate the approved shape.
            TypeError: If a details value is not an approved JSON-scalar type.
        """
        logger.info("Constructing IndicatorError code=%s", code.value)
        self.code = code
        self.message = _validate_message(message)
        self.details = _validate_details(details)
        super().__init__(self.code.value)


def guard_public_boundary(
    function: Callable[_P, _R],
) -> Callable[_P, StandardResponse[_R]]:
    """Return a standard response for one Indicators public operation.

    Applied to every qualifying Indicators operation. The wrapped callable
    remains the raw implementation so internal formula and validation behavior
    is unchanged, while callers receive the Utils-owned five-field response.

    The original exception is suppressed with ``raise ... from None`` and only
    its class name is reported, because an upstream exception message may embed
    caller payload data that must not cross the boundary.

    This is an internal Core helper, not public API: it appears in no
    ``__all__`` and is not a documented import for callers outside this package.

    Args:
        function: One official public indicator callable to protect.

    Returns:
        The wrapped callable returning ``StandardResponse[_R]``.
    """

    @functools.wraps(function)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> StandardResponse[_R]:
        """Execute the wrapped callable under the deterministic error boundary.

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded unchanged.

        Returns:
            A standard response containing the raw result or safe error.
        """
        start_time = time.perf_counter_ns()
        operation = (
            f"{function.__module__.removeprefix('app.services.')}.{function.__name__}"
        )
        risk_level = (
            RiskLevel.NONE
            if function.__module__.endswith(".registry")
            else RiskLevel.LOW
        )

        def metadata() -> ResponseMetadata:
            """Build the common pure/read-only operation metadata.

            Returns:
                Standard response metadata for this operation.
            """
            return build_response_metadata(
                name=operation,
                domain="indicators",
                risk_level=risk_level,
                request_id=generate_id("req"),
                start_time=start_time,
                read_only=True,
                writes_file=False,
                modifies_database=False,
                places_trade=False,
                requires_network=False,
            )

        try:
            raw_result = function(*args, **kwargs)
        except IndicatorError as error:
            logger.info("Indicators operation returned a known error: %s", operation)
            return error_response(
                code=error.code.value,
                details=cast("Mapping[str, JsonValue]", dict(error.details)),
                message=error.message,
                metadata=metadata(),
                catalog=INDICATOR_ERROR_CATALOG,
            )
        # BLE001 is intentional here and only here: this decorator is the
        # domain's outermost exception boundary, and its entire purpose is to
        # stop *any* unexpected exception from crossing the public port. A
        # narrower clause would let an unanticipated type escape as a raw
        # traceback. BaseException is deliberately not caught, so KeyboardInterrupt
        # and SystemExit still propagate.
        except Exception as error:  # noqa: BLE001
            failure_type = type(error).__name__
            logger.error(
                "Unexpected %s escaped %s; returning IND_INTERNAL_ERROR",
                failure_type,
                function.__name__,
            )
            return exception_response(
                HaruQuantError("IND_INTERNAL_ERROR", "UNEXPECTED_EXCEPTION"),
                message="indicator operation failed with an unexpected internal error",
                metadata=metadata(),
                catalog=INDICATOR_ERROR_CATALOG,
                extensions={
                    "operation": function.__name__,
                    "failure_type": failure_type,
                },
            )

        return success_response(
            raw_result,
            message=f"{function.__name__} completed successfully",
            metadata=metadata(),
        )

    signature = inspect.signature(function)
    return_annotation = signature.return_annotation
    if return_annotation is inspect.Signature.empty:
        return_annotation = "object"
    if isinstance(return_annotation, str):
        response_annotation = f"StandardResponse[{return_annotation}]"
    else:
        response_annotation = f"StandardResponse[{return_annotation!r}]"
    wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
        return_annotation=response_annotation
    )
    wrapper.__annotations__ = {
        **wrapper.__annotations__,
        "return": response_annotation,
    }
    return wrapper


def _unwrap_indicator_response(response: StandardResponse[_R]) -> _R:
    """Consume a nested internal Indicators response without nesting it.

    Args:
        response: Response returned by another migrated Indicators operation.

    Returns:
        The exact successful raw result.

    Raises:
        IndicatorError: If the nested operation returned a known error.
    """
    if response.status == "success" and response.data is not None:
        return response.data
    if response.error is not None:
        try:
            code = IndicatorErrorCode(response.error.code)
        except ValueError:
            code = IndicatorErrorCode.IND_INTERNAL_ERROR
        raise IndicatorError(code, response.message, response.error.details)
    raise IndicatorError(
        IndicatorErrorCode.IND_INTERNAL_ERROR,
        "indicator operation returned an invalid response",
    )


__all__ = ["IndicatorError", "IndicatorErrorCode"]
