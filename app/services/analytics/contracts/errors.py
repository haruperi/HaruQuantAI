"""Analytics error taxonomy and bounded public error conversion."""

from __future__ import annotations

from app.utils import logger, redact_mapping_value, redact_text_value


class AnalyticsError(Exception):
    """Base exception for direct Analytics feature APIs."""


class AnalyticsValidationError(AnalyticsError, ValueError):
    """Raised when Analytics evidence is invalid, missing, or unsafe."""


def to_analytics_error_payload(
    error: Exception,
    *,
    max_detail_bytes: int,
) -> dict[str, object]:
    """Convert an exception into a bounded redacted public payload.

    Args:
        error: Controlled exception to convert.
        max_detail_bytes: Positive maximum UTF-8 detail size.

    Returns:
        Stable secret-safe error payload.

    Raises:
        AnalyticsValidationError: If the bound is not positive.
    """
    logger.info("Converting Analytics error to a bounded public payload")
    if max_detail_bytes <= 0:
        raise AnalyticsValidationError("max_detail_bytes must be positive")
    code = (
        "ANALYTICS_VALIDATION_FAILED"
        if isinstance(error, AnalyticsValidationError)
        else "ANALYTICS_EXECUTION_FAILED"
    )
    raw_message = str(error) or error.__class__.__name__
    redacted_message = redact_text_value(raw_message).value
    if not isinstance(redacted_message, str):
        raise AnalyticsValidationError("redacted error message is invalid")
    message = redacted_message
    encoded = message.encode("utf-8")
    truncated = len(encoded) > max_detail_bytes
    if truncated:
        message = encoded[:max_detail_bytes].decode("utf-8", errors="ignore")
    redacted = redact_mapping_value(
        {"code": code, "message": message, "truncated": truncated}
    )
    if not isinstance(redacted.value, dict):
        raise AnalyticsValidationError("redacted error payload is invalid")
    return dict(redacted.value)


__all__ = [
    "AnalyticsError",
    "AnalyticsValidationError",
    "to_analytics_error_payload",
]
