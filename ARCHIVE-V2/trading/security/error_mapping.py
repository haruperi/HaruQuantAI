"""Trading exception hierarchy and public error mapping.

This module converts raw SDK, network, validation, persistence, and permission
failures into stable public trading error contracts. Public details are always
redacted and never include raw tracebacks.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.services.trading.contracts import JsonObject, JsonValue, TradingError
from app.services.trading.errors import TradingError as UtilityTradingError
from app.utils.logger import logger
from app.utils.security import redact_text, redact_value
from pydantic import ValidationError as PydanticValidationError


class TradingMappedError(UtilityTradingError):
    """Mapped exception for trading runtime errors.

    Args:
        message: Human-readable error message.
        code: Stable public error code.
        details: Optional JSON-safe diagnostic details.
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN_ERROR",
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a trading runtime exception.

        Args:
            message: Human-readable error message.
            code: Stable public error code.
            details: Optional JSON-safe diagnostic details.
        """
        logger.info("Initializing trading exception with code {}.", code)
        super().__init__(message, code=code)
        self.details = dict(details or {})


class TradingValidationError(TradingMappedError):
    """Trading request or payload validation failure."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a trading validation error.

        Args:
            message: Human-readable error message.
            details: Optional JSON-safe diagnostic details.
        """
        logger.info("Initializing trading validation exception.")
        super().__init__(message, code="VALIDATION_FAILED", details=details)


class TradingTimeoutError(TradingMappedError):
    """Trading timeout failure."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a trading timeout error.

        Args:
            message: Human-readable error message.
            details: Optional JSON-safe diagnostic details.
        """
        logger.info("Initializing trading timeout exception.")
        super().__init__(message, code="TIMEOUT", details=details)


class TradingPermissionError(TradingMappedError):
    """Trading permission or authentication failure."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a trading permission error.

        Args:
            message: Human-readable error message.
            details: Optional JSON-safe diagnostic details.
        """
        logger.info("Initializing trading permission exception.")
        super().__init__(message, code="PERMISSION_DENIED", details=details)


class TradingServiceUnavailableError(TradingMappedError):
    """Trading broker or network unavailability failure."""

    def __init__(
        self,
        message: str,
        *,
        details: Mapping[str, JsonValue] | None = None,
    ) -> None:
        """Initialize a trading service availability error.

        Args:
            message: Human-readable error message.
            details: Optional JSON-safe diagnostic details.
        """
        logger.info("Initializing trading service unavailable exception.")
        super().__init__(message, code="BROKER_UNAVAILABLE", details=details)


def map_exception_to_trading_error(
    error: BaseException,
    *,
    request_id: str,
    correlation_id: str,
    provider: str | None = None,
) -> TradingError:
    """Map an exception to a redacted public trading error contract.

    Args:
        error: Raw internal exception to translate.
        request_id: Request identifier to include in redacted details.
        correlation_id: Correlation identifier to include in redacted details.
        provider: Optional broker/provider name.

    Returns:
        TradingError: Public error payload with a standard code and redacted
        details.

    Raises:
        ValueError: If request or correlation identifiers are blank.
    """
    logger.info("Mapping exception to trading error for request {}.", request_id)
    if not request_id.strip():
        raise ValueError("request_id must be non-empty.")
    if not correlation_id.strip():
        raise ValueError("correlation_id must be non-empty.")

    code = _classify_exception(error)
    detail_parts: JsonObject = {
        "request_id": request_id,
        "correlation_id": correlation_id,
        "error_type": type(error).__name__,
    }
    if provider is not None:
        detail_parts["provider"] = provider
    if isinstance(error, TradingMappedError) and error.details:
        redacted_details = redact_value(error.details)
        if isinstance(redacted_details, dict):
            detail_parts["details"] = _json_object_from_mapping(redacted_details)

    details = redact_text(str(detail_parts))
    logger.debug(
        "Mapped exception type {} to trading code {}.",
        type(error).__name__,
        code,
    )
    return TradingError(code=code, details=details)


def _classify_exception(error: BaseException) -> str:
    """Classify an exception as a stable public error code.

    Args:
        error: Exception to classify.

    Returns:
        str: Standard public error code.
    """
    logger.debug("Classifying trading exception type {}.", type(error).__name__)
    if isinstance(error, TradingMappedError):
        return str(error.code)
    typed_codes: tuple[tuple[type[BaseException], str], ...] = (
        (TimeoutError, "TIMEOUT"),
        (PermissionError, "PERMISSION_DENIED"),
        (ConnectionError, "BROKER_UNAVAILABLE"),
        (OSError, "NETWORK_ERROR"),
        (ValueError, "VALIDATION_FAILED"),
        (PydanticValidationError, "VALIDATION_FAILED"),
    )
    for exception_type, code in typed_codes:
        if isinstance(error, exception_type):
            return code
    if isinstance(error, UtilityTradingError):
        return str(error.code)

    text_code = _classify_exception_text(str(error).lower())
    if text_code is not None:
        return text_code
    return "UNKNOWN_ERROR"


def _classify_exception_text(text: str) -> str | None:
    """Classify error text when no typed exception mapping applies.

    Args:
        text: Lowercase exception text.

    Returns:
        str | None: Public error code when a pattern matches.
    """
    logger.debug("Classifying trading exception text.")
    text_codes = (
        (("database", "sql"), "DATABASE_ERROR"),
        (("permission", "auth"), "PERMISSION_DENIED"),
        (("timeout", "timed out"), "TIMEOUT"),
        (("network", "connection", "broker"), "BROKER_UNAVAILABLE"),
    )
    for needles, code in text_codes:
        if any(needle in text for needle in needles):
            return code
    return None


def _json_object_from_mapping(payload: Mapping[str, object]) -> JsonObject:
    """Return a JSON-object view of a redacted mapping.

    Args:
        payload: Redacted mapping.

    Returns:
        JsonObject: JSON-safe mapping.
    """
    logger.debug("Normalizing redacted error details to JSON object.")
    result: JsonObject = {}
    for key, value in payload.items():
        if isinstance(value, str | int | float | bool) or value is None:
            result[str(key)] = value
        elif isinstance(value, list):
            result[str(key)] = [
                item
                if isinstance(item, str | int | float | bool) or item is None
                else str(item)
                for item in value
            ]
        else:
            result[str(key)] = str(value)
    return result
