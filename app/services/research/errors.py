"""Deterministic error-code mapping for the research service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Research, and provides a single redacted mapping
helper for official Research tool boundaries.
"""

from typing import TypedDict

from app.utils.logger import logger
from app.utils.security import redact_text


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class ResearchError(Exception):
    """Base exception for research domain errors."""

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class ResearchValidationError(ResearchError):
    """Validation exception for research domain."""

    code = "VALIDATION_FAILED"


RESEARCH_ERROR_CODES: frozenset[str] = frozenset(
    {
        "VALIDATION_FAILED",
        "INVALID_INPUT",
        "UNSUPPORTED_OPERATION",
        "SERVICE_UNAVAILABLE",
        "DATA_NOT_FOUND",
        "SIM_RESEARCH_PROTOCOL_MISSING",
        "UNKNOWN_ERROR",
    }
)
"""Deterministic codes expected at the Research official-tool boundary."""


ERROR_MESSAGES: dict[str, str] = {
    "VALIDATION_FAILED": "Response validation failed.",
    "INVALID_INPUT": "The request input is invalid.",
    "UNSUPPORTED_OPERATION": "The requested operation is unsupported.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "DATA_NOT_FOUND": "The requested data was not found.",
    "SIM_RESEARCH_PROTOCOL_MISSING": "Research protocol configuration is missing.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
}


def to_research_error_payload(
    exception: BaseException,
    *,
    request_id: str | None = None,
) -> ErrorPayload:
    """Map an exception to a redacted, deterministic Research error payload.

    Use this at the research tool boundary instead of returning raw exceptions
    or unredacted messages to callers.

    Args:
        exception: Exception raised by native Research functions.
        request_id: Optional trace identifier for log correlation.

    Returns:
        ErrorPayload: Mapping with deterministic ``code`` and redacted
        ``details`` text.
    """
    raw_code = getattr(exception, "code", None)
    code = (
        raw_code
        if isinstance(raw_code, str) and raw_code.strip()
        else "VALIDATION_FAILED"
    )
    details = f"{exception.__class__.__name__}: {exception}"
    safe_details = redact_text(details)
    logger.warning(
        f"Research service error mapped to boundary payload: code={code}",
        extra={"request_id": request_id},
    )
    return {"code": code, "details": safe_details}
