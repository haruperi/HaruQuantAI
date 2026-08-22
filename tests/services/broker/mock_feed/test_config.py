"""Tests for MockFeedConfig validation."""

import pytest

from app.services.broker.mock_feed.config import MockFeedConfig


def test_mock_feed_config_defaults() -> None:
    """Default base price is deterministic."""
    assert MockFeedConfig.from_dict(None).base_price == 1.1000


def test_mock_feed_config_custom_valid() -> None:
    """Positive custom base prices are accepted."""
    assert MockFeedConfig.from_dict({"base_price": 25000.0}).base_price == 25000.0


def test_mock_feed_config_invalid_base_price_raises() -> None:
    """Non-positive prices are rejected."""
    with pytest.raises(ValueError, match="base_price must be positive"):
        MockFeedConfig.from_dict({"base_price": -10.0})


def test_mock_feed_config_unknown_key_raises() -> None:
    """Removed fields cannot remain as undocumented no-ops."""
    with pytest.raises(ValueError, match="Unknown Mock Feed configuration"):
        MockFeedConfig.from_dict({"spread": 0.0002})
