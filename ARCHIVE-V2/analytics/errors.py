"""Deterministic error-code mapping for the analytics service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Analytics, and provides a single redacted mapping
helper for official Analytics tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class AnalyticsError(Exception):
    """Base exception for analytics domain errors."""

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class AnalyticsValidationError(AnalyticsError):
    """Validation exception for analytics domain."""

    code = "VALIDATION_FAILED"


ANALYTICS_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "SERVICE_UNAVAILABLE",
        "DATA_NOT_FOUND",
        "OBSERVABILITY_ERROR",
        "METRICS_EXPORT_FAILED",
        "REPORT_GENERATION_FAILED",
        "CALCULATION_FAILED",
        "UNKNOWN_ERROR",
    }
)
"""Deterministic codes expected at the Analytics official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "VALIDATION_FAILED": "Response validation failed.",
    "INVALID_INPUT": "The request input is invalid.",
    "UNSUPPORTED_OPERATION": "The requested operation is unsupported.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "DATA_NOT_FOUND": "The requested data was not found.",
    "OBSERVABILITY_ERROR": "An observability operation failed.",
    "METRICS_EXPORT_FAILED": "Metrics export failed.",
    "REPORT_GENERATION_FAILED": "Risk report generation failed.",
    "CALCULATION_FAILED": "A specific risk calculation failed.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
}


def to_analytics_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Analytics error payload.

    Use this at the analytics tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Analytics functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "CALCULATION_FAILED"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Analytics service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}
