"""Unit tests for recursive Research masking."""

from app.composition.logging import get_logger
from app.services.research import mask_research_artifact

logger = get_logger(__name__)


def test_masking_covers_nested_sensitive_fields() -> None:
    """Verify nested credentials, accounts, and forward fields are masked."""
    logger.debug("Testing nested Research artifact masking")
    source = {
        "nested": {
            "api_key": "secret",  # pragma: allowlist secret
            "account_id": "123",
        },
        "forward_5": 1.0,
    }
    masked = mask_research_artifact(source)
    assert masked["nested"]["api_key"] == "[REDACTED]"
    assert masked["nested"]["account_id"] == "[REDACTED]"
    assert masked["forward_5"] == "[REDACTED]"
    assert source["nested"]["api_key"] == "secret"  # pragma: allowlist secret
