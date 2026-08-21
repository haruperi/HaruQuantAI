"""Tests for FR-DATA-VALIDATE_CONFIG."""

import pytest

from app.services.data.historical_bars.config import HistoricalBarsConfig


def test_historical_bars_config_defaults() -> None:
    """Test default values of HistoricalBarsConfig."""
    cfg = HistoricalBarsConfig.from_dict(None)
    assert cfg.default_timeframe == "M1"
    assert cfg.cache_enabled is True


def test_historical_bars_config_custom_valid() -> None:
    """Test parsing custom valid timeframe and cache setting."""
    cfg = HistoricalBarsConfig.from_dict(
        {"default_timeframe": "H1", "cache_enabled": False}
    )
    assert cfg.default_timeframe == "H1"
    assert cfg.cache_enabled is False


def test_historical_bars_config_invalid_timeframe_raises() -> None:
    """Test unsupported timeframe raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported default_timeframe: 'INVALID'"):
        HistoricalBarsConfig.from_dict({"default_timeframe": "INVALID"})
