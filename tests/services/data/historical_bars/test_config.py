"""Tests for FR-DATA-VALIDATE_CONFIG."""

import pytest

from app.services.data.historical_bars.config import HistoricalBarsConfig


def test_historical_bars_config_defaults() -> None:
    """Test default values of HistoricalBarsConfig."""
    cfg = HistoricalBarsConfig.from_dict(None)
    assert cfg.default_timeframe == "M1"


def test_historical_bars_config_custom_valid() -> None:
    """Test parsing custom valid timeframe."""
    cfg = HistoricalBarsConfig.from_dict({"default_timeframe": "H1"})
    assert cfg.default_timeframe == "H1"


def test_historical_bars_config_invalid_timeframe_raises() -> None:
    """Test unsupported timeframe raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported default_timeframe: 'INVALID'"):
        HistoricalBarsConfig.from_dict({"default_timeframe": "INVALID"})
