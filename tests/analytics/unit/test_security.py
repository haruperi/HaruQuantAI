"""Security and redaction evidence for Analytics public failures."""

# ruff: noqa: INP001
from app.services.analytics.contracts.errors import (
    AnalyticsValidationError,
    to_analytics_error_payload,
)
from app.utils import logger


def test_error_payload_redacts_secret_material() -> None:
    """Controlled public error payloads never expose secret values."""
    logger.info("Testing Analytics error-payload redaction")
    secret = "analytics-super-secret"  # pragma: allowlist secret
    payload = to_analytics_error_payload(
        AnalyticsValidationError(f"password={secret}"),
        max_detail_bytes=256,
    )
    assert secret not in repr(payload)
    assert "[redacted]" in repr(payload).lower()
