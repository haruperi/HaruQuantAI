"""Tests for gateway REST configuration."""

from __future__ import annotations

import pytest
from app.services.gateway.rest import RestConfig


def test_rest_config_defaults() -> None:
    """Verify default REST configuration values."""
    config = RestConfig()
    assert config.api_prefix == "/api/v1"
    assert config.default_page_limit == 50
    assert config.max_page_limit == 500


def test_rest_config_validation() -> None:
    """Verify REST config validation."""
    with pytest.raises(ValueError, match="api_prefix must start with '/'"):
        RestConfig(api_prefix="api/v1")

    with pytest.raises(ValueError, match="default_page_limit must be > 0"):
        RestConfig(default_page_limit=0)

    with pytest.raises(ValueError, match=r"max_page_limit .* cannot be less than"):
        RestConfig(default_page_limit=100, max_page_limit=50)
