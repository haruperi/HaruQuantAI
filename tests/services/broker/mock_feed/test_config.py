"""Tests for FR-BROKER-VALIDATE_FEED_CONFIG."""

import pytest

from app.services.broker.mock_feed.config import MockFeedConfig


def test_mock_feed_config_defaults() -> None:
    """Test default values for MockFeedConfig."""
    cfg = MockFeedConfig.from_dict(None)
    assert cfg.base_price == 1.1000


def test_mock_feed_config_custom_valid() -> None:
    """Test parsing custom valid feed configuration."""
    cfg = MockFeedConfig.from_dict({"base_price": 25000.0})
    assert cfg.base_price == 25000.0


def test_mock_feed_config_invalid_base_price_raises() -> None:
    """Test non-positive base price raises ValueError."""
    with pytest.raises(ValueError, match="base_price must be positive"):
        MockFeedConfig.from_dict({"base_price": -10.0})
