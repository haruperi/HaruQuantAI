"""Unit tests for SettingsAutoRetestDataService."""

import pytest
from app.core.lib.errors import DomainError
from app.workspace.retester.settings_auto_retest_data import (
    AutoRetestDataSettings,
    SettingsAutoRetestDataService,
)


class TestSettingsAutoRetestData:
    """Test suite for AutoRetestDataSettings and service normalization."""

    def test_from_raw_golden_fixture(self) -> None:
        """Assert golden fixture: false -> custom, true -> strategy."""
        payload = {
            "symbol_source": "false",
            "symbol": "GBPUSD",
            "timeframe_source": "true",
            "timeframe": "M15",
        }
        settings = SettingsAutoRetestDataService.from_raw(payload)
        assert settings.symbol_source == "custom"
        assert settings.symbol == "GBPUSD"
        assert settings.timeframe_source == "strategy"
        assert settings.timeframe == "M15"
        assert settings.spread_pips == 1.0
        assert settings.initial_capital == 10000.0

    def test_default_construction(self) -> None:
        """Assert defaults when payload is empty."""
        settings = SettingsAutoRetestDataService.from_raw({})
        assert settings.symbol_source == "strategy"
        assert settings.symbol == "EURUSD"
        assert settings.timeframe == "H1"
        assert settings.initial_capital == 10000.0

    def test_invalid_data_bounds(self) -> None:
        """Assert negative spread or non-positive capital raises RETESTER_INVALID_DATA_SETTINGS."""
        with pytest.raises(DomainError) as exc_info1:
            SettingsAutoRetestDataService.from_raw({"spread_pips": -0.5})
        assert exc_info1.value.code == "RETESTER_INVALID_DATA_SETTINGS"

        with pytest.raises(DomainError) as exc_info2:
            SettingsAutoRetestDataService.from_raw({"initial_capital": 0.0})
        assert exc_info2.value.code == "RETESTER_INVALID_DATA_SETTINGS"

        with pytest.raises(DomainError) as exc_info3:
            SettingsAutoRetestDataService.from_raw({"initial_capital": -100.0})
        assert exc_info3.value.code == "RETESTER_INVALID_DATA_SETTINGS"

    def test_to_dict(self) -> None:
        """Assert serialization to dictionary."""
        settings = AutoRetestDataSettings(symbol="USDJPY", spread_pips=2.5)
        d = settings.to_dict()
        assert d["symbol"] == "USDJPY"
        assert d["spread_pips"] == 2.5
        assert d["symbol_source"] == "strategy"
