"""Deterministic error-code mapping for the brokers service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Brokers, and provides a single redacted mapping
helper for official Brokers tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class BrokerError(Exception):
    """Base exception for broker domain errors."""

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class BrokerValidationError(BrokerError):
    """Validation exception for broker domain."""

    code = "VALIDATION_FAILED"


class BrokerConfigurationError(BrokerError):
    """Configuration exception for brokers."""

    code = "CREDENTIALS_MISSING"


class BrokerExternalServiceError(BrokerError):
    """External broker service or network failure."""

    code = "BROKER_UNAVAILABLE"


BROKERS_ERROR_CODES: frozenset[str] = frozenset(
    {
        "BROKER_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "AUTHENTICATION_FAILED",
        "CREDENTIALS_MISSING",
        "NETWORK_ERROR",
        "TIMEOUT",
        "PERMISSION_DENIED",
        "LIVE_BROKER_READINESS_FAILED",
        "LIVE_BROKER_REJECTED",
        "LIVE_SESSION_INACTIVE",
        "INVALID_INPUT",
        "VALIDATION_FAILED",
        "UNKNOWN_ERROR",
    }
)
"""Deterministic codes expected at the Brokers official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "BROKER_UNAVAILABLE": "The broker service is unavailable.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "AUTHENTICATION_FAILED": "Authentication failed for the data source.",
    "CREDENTIALS_MISSING": "Credentials are missing for the source.",
    "NETWORK_ERROR": "A network operation failed.",
    "TIMEOUT": "The operation timed out.",
    "PERMISSION_DENIED": "The request is not permitted.",
    "LIVE_BROKER_READINESS_FAILED": "Broker readiness check failed; live mutation is blocked.",
    "LIVE_BROKER_REJECTED": "The broker rejected the trade request.",
    "LIVE_SESSION_INACTIVE": "No active live session; start a session before trading.",
    "INVALID_INPUT": "The request input is invalid.",
    "VALIDATION_FAILED": "Response validation failed.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
}


def to_brokers_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Brokers error payload.

    Use this at the brokers tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Brokers functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "BROKER_UNAVAILABLE"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Brokers service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}
