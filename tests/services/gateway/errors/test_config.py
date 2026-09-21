"""Tests for gateway errors configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.errors import ErrorsConfig


def test_errors_config_defaults() -> None:
    """Verify default errors configuration values."""
    config = ErrorsConfig()
    assert not config.debug_mode
    assert config.doc_base_url == "https://errors.haruquant.ai"


def test_errors_config_validation() -> None:
    """Verify errors configuration validation on invalid doc URL."""
    with pytest.raises(ValueError, match="doc_base_url must be a valid HTTP URL"):
        ErrorsConfig(doc_base_url="not-a-url")
