"""Deterministic error-code mapping for the optimization service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Optimization, and provides a single redacted mapping
helper for official Optimization tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class OptimizationError(Exception):
    """Base exception for optimization domain errors."""

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class OptimizationValidationError(OptimizationError):
    """Validation exception for optimization domain."""

    code = "VALIDATION_FAILED"


OPTIMIZATION_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "SERVICE_UNAVAILABLE",
        "TIMEOUT",
        "SIM_OPTIMIZATION_FAILED",
        "CALCULATION_FAILED",
        "UNKNOWN_ERROR",
    }
)
"""Deterministic codes expected at the Optimization official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "VALIDATION_FAILED": "Response validation failed.",
    "INVALID_INPUT": "The request input is invalid.",
    "UNSUPPORTED_OPERATION": "The requested operation is unsupported.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "TIMEOUT": "The operation timed out.",
    "SIM_OPTIMIZATION_FAILED": "Optimization engine failed to converge.",
    "CALCULATION_FAILED": "A specific risk calculation failed.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
}


def to_optimization_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Optimization error payload.

    Use this at the optimization tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Optimization functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "SIM_OPTIMIZATION_FAILED"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Optimization service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}
