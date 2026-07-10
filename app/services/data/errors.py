"""Deterministic error-code mapping for the market data service boundary.

Reuses the shared HaruQuant error taxonomy from ``app.utils.errors`` instead of
defining a parallel code registry. This module documents the subset of
approved codes relevant to Data, and provides a single redacted mapping
helper for official Data tool boundaries in ``public_api.py``.
"""

from app.utils.errors import ErrorPayload, exception_to_error_payload
from app.utils.logger import logger
from app.utils.security import redact_text

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
"""Deterministic codes expected at the Data official-tool boundary.

Every member is a subset of ``app.utils.errors.APPROVED_ERROR_CODES``; Data
does not define its own competing code registry.
"""


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
    payload = exception_to_error_payload(exception, default_code="DATA_NOT_FOUND")
    safe_details = redact_text(payload["details"])
    logger.warning(
        f"Data service error mapped to boundary payload: code={payload['code']}",
        extra={"request_id": request_id},
    )
    return {"code": payload["code"], "details": safe_details}
