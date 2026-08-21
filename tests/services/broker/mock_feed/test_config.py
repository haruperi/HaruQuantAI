"""Tests for FR-BROKER-VALIDATE_FEED_CONFIG."""

import pytest

from app.services.broker.mock_feed.config import MockFeedConfig


def test_mock_feed_config_defaults() -> None:
    """Test default values for MockFeedConfig."""
    cfg = MockFeedConfig.from_dict(None)
    assert cfg.base_price == 1.1000
    assert cfg.spread == 0.0002


def test_mock_feed_config_custom_valid() -> None:
    """Test parsing custom valid feed configuration."""
    cfg = MockFeedConfig.from_dict({"base_price": 25000.0, "spread": 0.5})
    assert cfg.base_price == 25000.0
    assert cfg.spread == 0.5


def test_mock_feed_config_invalid_base_price_raises() -> None:
    """Test non-positive base price raises ValueError."""
    with pytest.raises(ValueError, match="base_price must be positive"):
        MockFeedConfig.from_dict({"base_price": -10.0})


def test_mock_feed_config_invalid_spread_raises() -> None:
    """Test negative spread raises ValueError."""
    with pytest.raises(ValueError, match="spread cannot be negative"):
        MockFeedConfig.from_dict({"spread": -0.01})
