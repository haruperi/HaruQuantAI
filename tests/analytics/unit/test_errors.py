"""Unit tests for the Analytics error taxonomy."""

# ruff: noqa: INP001

import pytest
from app.services.analytics.contracts import (
    AnalyticsError,
    AnalyticsValidationError,
    to_analytics_error_payload,
)
from app.utils import logger


def test_analytics_error_is_domain_base() -> None:
    """AnalyticsError is the common direct-feature exception."""
    logger.debug("Testing Analytics base error")
    assert issubclass(AnalyticsValidationError, AnalyticsError)


def test_validation_error_is_analytics_error() -> None:
    """Validation failures remain distinguishable within Analytics."""
    logger.debug("Testing Analytics validation error")
    assert isinstance(AnalyticsValidationError("invalid"), AnalyticsError)


def test_error_payload_is_bounded_and_redacted() -> None:
    """Public error payloads redact secrets and obey the byte bound."""
    logger.debug("Testing bounded Analytics error payload")
    payload = to_analytics_error_payload(
        AnalyticsValidationError("access_token=secret"), max_detail_bytes=12
    )
    assert payload["code"] == "ANALYTICS_VALIDATION_FAILED"
    assert "secret" not in str(payload)
    assert payload["truncated"] is True


def test_error_payload_rejects_missing_bound() -> None:
    """The error converter has no silent non-positive fallback."""
    logger.debug("Testing Analytics error payload bound")
    with pytest.raises(AnalyticsValidationError):
        to_analytics_error_payload(ValueError("bad"), max_detail_bytes=0)
