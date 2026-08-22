"""Tests for HistoricalBarsConfig validation."""

import pytest

from app.services.data.historical_bars.config import HistoricalBarsConfig


def test_historical_bars_config_defaults() -> None:
    """Default timeframe is M1."""
    assert HistoricalBarsConfig.from_dict(None).default_timeframe == "M1"


def test_historical_bars_config_custom_valid() -> None:
    """Supported timeframes are normalized to uppercase."""
    assert (
        HistoricalBarsConfig.from_dict({"default_timeframe": "h1"}).default_timeframe
        == "H1"
    )


def test_historical_bars_config_invalid_timeframe_raises() -> None:
    """Unsupported timeframes are rejected."""
    with pytest.raises(ValueError, match="Unsupported default_timeframe: 'INVALID'"):
        HistoricalBarsConfig.from_dict({"default_timeframe": "INVALID"})


def test_historical_bars_config_unknown_key_raises() -> None:
    """Undocumented configuration fields cannot silently drift into runtime."""
    with pytest.raises(ValueError, match="Unknown Historical Bars configuration"):
        HistoricalBarsConfig.from_dict({"cache_enabled": True})
