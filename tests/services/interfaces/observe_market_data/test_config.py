"""Unit tests for observe-market-data configuration parsing."""

import pytest
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig


def test_config_defaults() -> None:
    """Verify default configuration values."""
    config = ObserveMarketDataConfig()
    assert config.stale_after_seconds == 5.0
    assert config.max_symbols == 50


def test_config_from_dict_none_returns_defaults() -> None:
    """Verify None maps to defaults."""
    assert ObserveMarketDataConfig.from_dict(None) == ObserveMarketDataConfig()


def test_config_from_dict_valid_values() -> None:
    """Verify valid overrides are accepted."""
    config = ObserveMarketDataConfig.from_dict(
        {"stale_after_seconds": 2, "max_symbols": 200}
    )
    assert config.stale_after_seconds == 2.0
    assert config.max_symbols == 200


def test_config_from_dict_rejects_unknown_keys() -> None:
    """Verify unknown configuration keys fail closed."""
    with pytest.raises(ValueError, match="Unknown observe-market-data"):
        ObserveMarketDataConfig.from_dict({"symbols": ["EURUSD"]})


def test_config_from_dict_rejects_invalid_types() -> None:
    """Verify wrong value types raise TypeError."""
    with pytest.raises(TypeError, match="stale_after_seconds"):
        ObserveMarketDataConfig.from_dict({"stale_after_seconds": "soon"})
    with pytest.raises(TypeError, match="stale_after_seconds"):
        ObserveMarketDataConfig.from_dict({"stale_after_seconds": True})
    with pytest.raises(TypeError, match="max_symbols"):
        ObserveMarketDataConfig.from_dict({"max_symbols": "many"})


def test_config_rejects_invalid_constructor_values() -> None:
    """Verify direct construction bounds."""
    with pytest.raises(ValueError, match="stale_after_seconds"):
        ObserveMarketDataConfig(stale_after_seconds=0)
    with pytest.raises(ValueError, match="max_symbols"):
        ObserveMarketDataConfig(max_symbols=0)
    with pytest.raises(ValueError, match="max_symbols"):
        ObserveMarketDataConfig(max_symbols=201)
