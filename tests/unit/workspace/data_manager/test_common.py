"""Unit tests for foundational market data contracts in data_manager workspace."""

from __future__ import annotations

import pytest
from app.services.brokers.base import BridgeError as BaseBridgeError
from app.workspace.data_manager import (
    MAX_POSITION,
    MAX_RECORDS,
    MAX_UNDERLYING_DISPLAY_LEN,
    READ_TIMEOUT,
    TIMEFRAME_SECONDS,
    TRUNCATE_LEN,
    BridgeError,
    ChartDef,
    DataInfo,
    InstrumentAliasRecord,
    InstrumentInfo,
    MarketBar,
    MarketTick,
    Timeframe,
    format_dataset_table,
    format_home_dashboard,
)


class TestContractsTimeframe:
    """Verify Timeframe enum properties, calculations, and parsers."""

    def test_timeframe_string_values_and_aliases(self) -> None:
        """Verify enum string values and shorthand aliases match."""
        assert Timeframe.PERIOD_M1.value == "M1"
        assert Timeframe.M1.value == "M1"
        assert Timeframe.PERIOD_H1.value == "H1"
        assert Timeframe.H1.value == "H1"
        assert Timeframe.PERIOD_D1.value == "D1"
        assert Timeframe.D1.value == "D1"
        assert Timeframe.PERIOD_W1.value == "W1"
        assert Timeframe.W1.value == "W1"
        assert Timeframe.PERIOD_MN1.value == "MN1"
        assert Timeframe.MN1.value == "MN1"

    def test_to_seconds_and_to_minutes(self) -> None:
        """Verify seconds and minutes duration calculations across timeframes."""
        assert Timeframe.PERIOD_M1.to_seconds() == 60
        assert Timeframe.PERIOD_M1.to_minutes() == 1

        assert Timeframe.PERIOD_M5.to_seconds() == 300
        assert Timeframe.PERIOD_M5.to_minutes() == 5

        assert Timeframe.PERIOD_H1.to_seconds() == 3600
        assert Timeframe.PERIOD_H1.to_minutes() == 60

        assert Timeframe.PERIOD_H4.to_seconds() == 14400
        assert Timeframe.PERIOD_H4.to_minutes() == 240

        assert Timeframe.PERIOD_D1.to_seconds() == 86400
        assert Timeframe.PERIOD_D1.to_minutes() == 1440

        assert Timeframe.PERIOD_W1.to_seconds() == 604800
        assert Timeframe.PERIOD_W1.to_minutes() == 10080

        assert Timeframe.PERIOD_MN1.to_seconds() == 2419200
        assert Timeframe.PERIOD_MN1.to_minutes() == 40320

        assert Timeframe.PERIOD_CURRENT.to_seconds() == 0
        assert Timeframe.PERIOD_CURRENT.to_minutes() == 0

    def test_from_string_valid(self) -> None:
        """Verify parsing standard timeframe representations."""
        test_cases = [
            ("M1", Timeframe.PERIOD_M1),
            ("1m", Timeframe.PERIOD_M1),
            ("1MIN", Timeframe.PERIOD_M1),
            ("M2", Timeframe.PERIOD_M2),
            ("2m", Timeframe.PERIOD_M2),
            ("M3", Timeframe.PERIOD_M3),
            ("3m", Timeframe.PERIOD_M3),
            ("M4", Timeframe.PERIOD_M4),
            ("4m", Timeframe.PERIOD_M4),
            ("M5", Timeframe.PERIOD_M5),
            ("5m", Timeframe.PERIOD_M5),
            ("5MIN", Timeframe.PERIOD_M5),
            ("M6", Timeframe.PERIOD_M6),
            ("6m", Timeframe.PERIOD_M6),
            ("M10", Timeframe.PERIOD_M10),
            ("10m", Timeframe.PERIOD_M10),
            ("M12", Timeframe.PERIOD_M12),
            ("12m", Timeframe.PERIOD_M12),
            ("M15", Timeframe.PERIOD_M15),
            ("15m", Timeframe.PERIOD_M15),
            ("15MIN", Timeframe.PERIOD_M15),
            ("M20", Timeframe.PERIOD_M20),
            ("20m", Timeframe.PERIOD_M20),
            ("M30", Timeframe.PERIOD_M30),
            ("30m", Timeframe.PERIOD_M30),
            ("30MIN", Timeframe.PERIOD_M30),
            ("H1", Timeframe.PERIOD_H1),
            ("1h", Timeframe.PERIOD_H1),
            ("60m", Timeframe.PERIOD_H1),
            ("H2", Timeframe.PERIOD_H2),
            ("2h", Timeframe.PERIOD_H2),
            ("H3", Timeframe.PERIOD_H3),
            ("3h", Timeframe.PERIOD_H3),
            ("H4", Timeframe.PERIOD_H4),
            ("4h", Timeframe.PERIOD_H4),
            ("240m", Timeframe.PERIOD_H4),
            ("H6", Timeframe.PERIOD_H6),
            ("6h", Timeframe.PERIOD_H6),
            ("H8", Timeframe.PERIOD_H8),
            ("8h", Timeframe.PERIOD_H8),
            ("H12", Timeframe.PERIOD_H12),
            ("12h", Timeframe.PERIOD_H12),
            ("D1", Timeframe.PERIOD_D1),
            ("1d", Timeframe.PERIOD_D1),
            ("day", Timeframe.PERIOD_D1),
            ("W1", Timeframe.PERIOD_W1),
            ("1w", Timeframe.PERIOD_W1),
            ("week", Timeframe.PERIOD_W1),
            ("MN1", Timeframe.PERIOD_MN1),
            ("1mn", Timeframe.PERIOD_MN1),
            ("month", Timeframe.PERIOD_MN1),
        ]
        for raw, expected in test_cases:
            assert Timeframe.from_string(raw) == expected

    def test_from_string_invalid(self) -> None:
        """Verify invalid timeframe identifier raises ValueError."""
        with pytest.raises(ValueError, match="Unknown timeframe identifier"):
            Timeframe.from_string("INVALID_TF")

    def test_timeframe_seconds_mapping(self) -> None:
        """Verify TIMEFRAME_SECONDS contains expected frames excluding CURRENT."""
        assert Timeframe.PERIOD_CURRENT not in TIMEFRAME_SECONDS
        assert TIMEFRAME_SECONDS[Timeframe.PERIOD_M1] == 60
        assert TIMEFRAME_SECONDS[Timeframe.PERIOD_D1] == 86400


class TestContractsMarketBar:
    """Verify MarketBar data structure and computed properties."""

    def test_bullish_bar(self) -> None:
        """Verify bullish candle computations."""
        bar = MarketBar(
            time=1700000000,
            open=1.0850,
            high=1.0870,
            low=1.0840,
            close=1.0865,
            tick_volume=150,
            spread=3,
        )
        assert bar.is_bullish is True
        assert bar.is_bearish is False
        assert bar.is_doji is False
        assert pytest.approx(bar.range, rel=1e-6) == 0.0030
        assert pytest.approx(bar.body, rel=1e-6) == 0.0015
        assert bar.volume == 150.0

    def test_bearish_and_doji_bar(self) -> None:
        """Verify bearish and doji candle computations."""
        bearish = MarketBar(
            time=1700000060,
            open=1.0865,
            high=1.0870,
            low=1.0830,
            close=1.0835,
            tick_volume=100,
            real_volume=500,
        )
        assert bearish.is_bullish is False
        assert bearish.is_bearish is True
        assert bearish.is_doji is False
        assert pytest.approx(bearish.range, rel=1e-6) == 0.0040
        assert pytest.approx(bearish.body, rel=1e-6) == 0.0030
        assert bearish.volume == 500.0

        doji = MarketBar(
            time=1700000120,
            open=1.0835,
            high=1.0845,
            low=1.0825,
            close=1.0835,
        )
        assert doji.is_bullish is False
        assert doji.is_bearish is False
        assert doji.is_doji is True
        assert pytest.approx(doji.body, rel=1e-6) == 0.0

    def test_immutability(self) -> None:
        """Verify MarketBar is frozen and rejects attribute assignment."""
        bar = MarketBar(time=1700000000, open=1.0, high=1.1, low=0.9, close=1.05)
        with pytest.raises((AttributeError, TypeError)):
            bar.close = 1.10  # type: ignore[misc]


class TestContractsMarketTick:
    """Verify MarketTick data structure and computed properties."""

    def test_tick_properties(self) -> None:
        """Verify tick spread, midpoint, and time alias."""
        tick = MarketTick(
            time_msc=1700000000123,
            bid=1.0854,
            ask=1.0856,
            last=1.0855,
            volume=50,
        )
        assert tick.time == 1700000000123
        assert pytest.approx(tick.spread, rel=1e-6) == 0.0002
        assert pytest.approx(tick.mid, rel=1e-6) == 1.0855

    def test_immutability(self) -> None:
        """Verify MarketTick is frozen and rejects attribute assignment."""
        tick = MarketTick(time_msc=1700000000123, bid=1.0854, ask=1.0856)
        with pytest.raises((AttributeError, TypeError)):
            tick.bid = 1.0850  # type: ignore[misc]


class TestContractsConstantsAndReexports:
    """Verify boundary limits, bridge error re-export, and DataInfo export."""

    def test_constants_and_bridge_error(self) -> None:
        """Verify boundary constants and BridgeError identity."""
        assert MAX_RECORDS == 1000
        assert MAX_POSITION == 2**31 - 1
        assert READ_TIMEOUT == 60.0
        assert BridgeError is BaseBridgeError

    def test_datainfo_contract(self) -> None:
        """Verify DataInfo is exported from contracts and initializes cleanly."""
        info = DataInfo(symbol="EURUSD", timeframe="M1", bars=100)
        assert info.symbol == "EURUSD"
        assert info.timeframe == "M1"
        assert info.bars == 100
        assert info.total_records == 100
        assert info.data_type == "Forex"

    def test_chart_def_contract(self) -> None:
        """Verify ChartDef is exported from contracts and initializes cleanly."""
        chart = ChartDef(symbol="EURUSD", timeframe="M1", connection_name="dukascopy")
        assert chart.symbol == "EURUSD"
        assert chart.timeframe == "M1"
        assert chart.timeframe_seconds == 60
        assert chart.connection_name == "dukascopy"
        assert chart.is_symbol_recognized()
        # Verify DataInfo.to_chart_def() interoperability
        info = DataInfo(symbol="EURUSD", timeframe="M1", connection="dukascopy")
        converted = info.to_chart_def()
        assert isinstance(converted, ChartDef)
        assert converted.symbol == "EURUSD"
        assert converted.connection_name == "dukascopy"


class TestFormatters:
    """Verify dataset table and home dashboard standalone formatters."""

    def test_format_dataset_table_and_truncation(self) -> None:
        """Verify format_dataset_table renders correctly and truncates long underlying."""
        short_ds = DataInfo(
            symbol="EURUSD",
            instrument="Forex",
            broker="dukascopy",
            underlying="EUR/USD",
            timeframe="M1",
            timezone="UTC",
            date_from="2025-01-01",
            date_to="2025-01-02",
            total_days=1,
            total_records=1440,
            source="file",
            data_type="Forex",
        )
        long_ds = DataInfo(
            symbol="LONG_SYM",
            instrument="Crypto",
            broker="binance",
            underlying="VERY_LONG_UNDERLYING_NAME_THAT_EXCEEDS_MAX_LENGTH",
            timeframe="H1",
            timezone="UTC",
            date_from="2025-01-01",
            date_to="2025-01-02",
            total_days=1,
            total_records=24,
            source="api",
            data_type="Crypto",
        )
        rendered = format_dataset_table([short_ds, long_ds])
        assert "=== Saved Datasets Catalog (2 items) ===" in rendered
        assert "EURUSD" in rendered
        assert "EUR/USD" in rendered
        assert "VERY_LONG_UNDERLYING_NAME_THAT" in rendered
        assert ".." in rendered
        assert MAX_UNDERLYING_DISPLAY_LEN == 32
        assert TRUNCATE_LEN == 30

    def test_format_home_dashboard_mapping_and_object(self) -> None:
        """Verify format_home_dashboard renders summary block with mapping or object."""
        ds = DataInfo(symbol="AAPL", timeframe="D1", bars=250)
        overview_dict = {
            "datasets_count": 5,
            "total_bars": 100000,
            "instruments_count": 12,
            "sessions_count": 3,
            "baskets_count": 2,
            "active_providers_count": 4,
        }
        rendered_map = format_home_dashboard(overview_dict, [ds])
        assert "=== Data Manager Home: Live Database Overview ===" in rendered_map
        assert "Total Datasets:       5" in rendered_map
        assert "Historical Bars:      100,000" in rendered_map
        assert "Instruments Catalog:  12" in rendered_map
        assert "AAPL" in rendered_map

        class _MockOverview:
            datasets_count = 1
            total_bars = 500
            instruments_count = 2
            sessions_count = 1
            baskets_count = 0
            active_providers_count = 1

        rendered_obj = format_home_dashboard(_MockOverview(), [ds])
        assert "Total Datasets:       1" in rendered_obj
        assert "Historical Bars:      500" in rendered_obj


class TestContractsInstrumentInfo:
    """Verify InstrumentInfo model defaults, tick rounding, and conversions."""

    def test_instrument_info_defaults_and_tick_rounding(self) -> None:
        """Verify price rounding to tick size and decimal precision."""
        inst = InstrumentInfo(
            symbol="EURUSD",
            tick_size=0.00001,
            decimals=5,
            point_value=100000.0,
            tick_value_in_money=10.0,
        )
        assert inst.symbol == "EURUSD"
        assert inst.decimals == 5
        assert inst.round_to_tick_size(1.085427) == 1.08543
        assert inst.round_to_tick_size(1.085422) == 1.08542

    def test_instrument_info_to_symbol_spec(self) -> None:
        """Verify conversion to Tier 2 trading domain SymbolSpec."""
        inst = InstrumentInfo(
            symbol="EURUSD",
            tick_size=0.00001,
            decimals=5,
            point_value=100000.0,
            tick_value_in_money=10.0,
            min_volume=0.01,
            max_volume=100.0,
            lot_step=0.01,
            margin_rate=0.033,
        )
        spec = inst.to_symbol_spec()
        assert spec.name == "EURUSD"
        assert spec.digits == 5
        assert spec.point == 0.00001
        assert spec.trade_contract_size == 100000.0
        assert spec.volume_min == 0.01
        assert spec.volume_max == 100.0

    def test_instrument_info_to_dict_and_from_dict(self) -> None:
        """Verify bidirectional serialization with dictionary payloads."""
        inst = InstrumentInfo(
            symbol="BTCUSDT",
            data_type="Crypto",
            tick_size=0.01,
            point_value=1.0,
            decimals=2,
        )
        d = inst.to_dict()
        assert d["symbol"] == "BTCUSDT"
        assert d["data_type"] == "Crypto"
        rebuilt = InstrumentInfo.from_dict(d)
        assert rebuilt.symbol == "BTCUSDT"
        assert rebuilt.data_type == "Crypto"
        assert rebuilt.tick_size == 0.01


class TestContractsInstrumentAliasRecord:
    """Verify InstrumentAliasRecord dataclass serialization."""

    def test_alias_record_to_dict(self) -> None:
        """Verify alias record fields and dictionary output."""
        rec = InstrumentAliasRecord(
            alias="EUR.USD",
            instrument="EURUSD",
            description="Broker symbol format",
        )
        assert rec.alias == "EUR.USD"
        assert rec.instrument == "EURUSD"
        d = rec.to_dict()
        assert d == {
            "alias": "EUR.USD",
            "instrument": "EURUSD",
            "description": "Broker symbol format",
        }
