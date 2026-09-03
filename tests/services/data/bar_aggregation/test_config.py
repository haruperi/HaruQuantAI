"""Unit tests for Bar Aggregation config."""

import pytest
from app.services.data.bar_aggregation.config import BarAggregationConfig


def test_config_defaults() -> None:
    """Verify default configuration values."""
    cfg = BarAggregationConfig()
    assert cfg.max_bars_per_request == 100_000
    assert cfg.default_timezone == "UTC"
    assert cfg.allow_custom_timeframes is True


def test_config_custom_values() -> None:
    """Verify custom configuration values."""
    cfg = BarAggregationConfig(
        max_bars_per_request=50_000,
        default_timezone="America/New_York",
        allow_custom_timeframes=False,
    )
    assert cfg.max_bars_per_request == 50_000
    assert cfg.default_timezone == "America/New_York"
    assert cfg.allow_custom_timeframes is False


def test_config_invalid_values() -> None:
    """Verify ValueError on invalid configuration settings."""
    with pytest.raises(
        ValueError, match="max_bars_per_request must be a positive integer"
    ):
        BarAggregationConfig(max_bars_per_request=0)

    with pytest.raises(ValueError, match="default_timezone must be a non-empty string"):
        BarAggregationConfig(default_timezone="")
