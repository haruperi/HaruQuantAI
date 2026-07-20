"""Deterministic error-code mapping for the market data service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Data, and provides a single redacted mapping
helper for official Data tool boundaries in ``public_api.py``.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class DataServiceError(Exception):
    """Base exception for all market data operations."""

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class DataValidationError(DataServiceError):
    """Validation exception for market data parameters."""

    code = "VALIDATION_FAILED"


class DataIntegrityError(DataServiceError):
    """Data integrity or storage lookup exception."""

    code = "DATA_NOT_FOUND"


class DataExternalServiceError(DataServiceError):
    """External service, source network, or timeout failure."""

    code = "SERVICE_UNAVAILABLE"


class DataConfigurationError(DataServiceError):
    """Configuration exception for market data settings."""

    code = "CREDENTIALS_MISSING"


DATA_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_TIMEFRAME",
        "UNSUPPORTED_OPERATION",
        "AUTHENTICATION_FAILED",
        "CREDENTIALS_MISSING",
        "BROKER_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "CIRCUIT_BREAKER_OPEN",
        "LICENSE_RESTRICTION",
        "DATA_NOT_FOUND",
        "DATA_SCHEMA_DRIFT",
        "BUFFER_OVERFLOW",
        "DATA_DROPPED",
        "FEED_HEARTBEAT_TIMEOUT",
        "FEED_RECONCILIATION_FAILED",
        "STATE_RECOVERY_FAILED",
        "DATA_SERIALIZATION_FAILED",
    }
)
"""Deterministic codes expected at the Data official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "VALIDATION_FAILED": "Response validation failed.",
    "INVALID_INPUT": "The request input is invalid.",
    "UNSUPPORTED_TIMEFRAME": "The requested timeframe is invalid or unsupported.",
    "UNSUPPORTED_OPERATION": "The requested operation is unsupported.",
    "AUTHENTICATION_FAILED": "Authentication failed for the data source.",
    "CREDENTIALS_MISSING": "Credentials are missing for the source.",
    "BROKER_UNAVAILABLE": "The broker service is unavailable.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "CIRCUIT_BREAKER_OPEN": "Circuit breaker is open for the source.",
    "LICENSE_RESTRICTION": "Access denied due to license restrictions.",
    "DATA_NOT_FOUND": "The requested data was not found.",
    "DATA_SCHEMA_DRIFT": "Data payload shape does not match the expected schema.",
    "BUFFER_OVERFLOW": "Feed buffer has overflowed.",
    "DATA_DROPPED": "Data record was dropped due to buffer overflow or constraints.",
    "FEED_HEARTBEAT_TIMEOUT": "Feed heartbeat timeout detected.",
    "FEED_RECONCILIATION_FAILED": "Feed gap reconciliation failed.",
    "STATE_RECOVERY_FAILED": "Failed to recover scheduler/feed state.",
    "DATA_SERIALIZATION_FAILED": "Data payload could not be serialized safely.",
}


def to_data_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Data error payload.

    Use this at the ``public_api.py`` tool boundary instead of returning raw
    exceptions or unredacted messages to callers.

    Args:
        exception: Exception raised by native Data functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code if isinstance(raw_code, str) and raw_code.strip() else "DATA_NOT_FOUND"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Data service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}
