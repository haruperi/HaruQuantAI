"""Deterministic Core MVP error catalogue and structured domain exception."""

from __future__ import annotations

import functools
import math
import re
from collections.abc import Callable, Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import Final, ParamSpec, TypeVar

from app.utils import logger, redact_text_value

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
    logger.debug("Validating IndicatorError message")
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
    logger.debug("Validating one IndicatorError scalar detail value")
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
    logger.debug("Validating one IndicatorError detail value")
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
    logger.debug("Validating IndicatorError details mapping")
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
) -> Callable[_P, _R]:
    """Convert any unexpected exception into a redacted ``IND_INTERNAL_ERROR``.

    Applied to every official indicator convenience function so that no raw
    pandas, NumPy, Utils, or Python exception can cross the Indicators public
    port. A deliberate ``IndicatorError`` propagates unchanged so documented
    deterministic failures keep their exact code.

    The original exception is suppressed with ``raise ... from None`` and only
    its class name is reported, because an upstream exception message may embed
    caller payload data that must not cross the boundary.

    This is an internal Core helper, not public API: it appears in no
    ``__all__`` and is not a documented import for callers outside this package.

    Args:
        function: One official public indicator callable to protect.

    Returns:
        The wrapped callable with identical signature and behavior on success.
    """

    @functools.wraps(function)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Execute the wrapped callable under the deterministic error boundary.

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded unchanged.

        Returns:
            Whatever the wrapped callable returns.

        Raises:
            IndicatorError: The original deterministic failure, or a redacted
                ``IND_INTERNAL_ERROR`` replacing an unexpected exception.
        """
        try:
            return function(*args, **kwargs)
        except IndicatorError:
            raise
        # BLE001 is intentional here and only here: this decorator is the
        # domain's outermost exception boundary, and its entire purpose is to
        # stop *any* unexpected exception from crossing the public port. A
        # narrower clause would let an unanticipated type escape as a raw
        # traceback. BaseException is deliberately not caught, so KeyboardInterrupt
        # and SystemExit still propagate.
        except Exception as error:  # noqa: BLE001
            failure_type = type(error).__name__
            logger.error(
                "Unexpected %s escaped %s; raising IND_INTERNAL_ERROR",
                failure_type,
                function.__name__,
            )
            raise IndicatorError(
                IndicatorErrorCode.IND_INTERNAL_ERROR,
                "indicator calculation failed with an unexpected internal error",
                {"operation": function.__name__, "failure_type": failure_type},
            ) from None

    return wrapper


__all__ = ["IndicatorError", "IndicatorErrorCode"]
