"""Unit tests for ChartDef and DataInfo market data abstractions.

Description:
    Tests verification of ChartDef and DataInfo classes in app/services/libs/data.py,
    including timeframe calculations, resample compatibility predicates,
    cloning, serialization, and catalog-to-chart-def conversion.

Purpose:
    FEAT-LIBS-DATA: Stage 2A market data abstraction testing.

Key Capabilities:
    - FR-DATA-CHART-DEF-AND-CATALOG: Verification of ChartDef and DataInfo.
      Associated: `ChartDef`, `DataInfo`.
      Logging: Change-scoped test execution.

Python API Usage:
    ```python
    pytest tests/unit/services/test_chart_def_data_info.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_chart_def_data_info.py --no-cov
    ```
"""

from __future__ import annotations

from app.services.data import ChartDef, DataInfo, Timeframe
from app.services.data.catalog import ChartDef as CatalogChartDef
from app.services.data.catalog import DataInfo as CatalogDataInfo


class TestChartDef:
    """Tests for ChartDef market data specification container."""

    def test_initialization_defaults(self) -> None:
        """Verify default attribute values and hash initialization."""
        chart = ChartDef("EURUSD")
        assert chart.symbol == "EURUSD"
        assert chart.timeframe == "M1"
        assert chart.instrument == "Forex"
        assert chart.session == "Default"
        assert chart.connection_name == ""
        assert chart.history_from == 0
        assert chart.history_to == 0
        assert chart.loaded_history_from == 0
        assert chart.spread == 0.0
        assert chart.real_spread is False
        assert chart.bar_time_type == 0
        assert chart.min_distance == 0.0
        assert chart.is_backtest_data_def is False
        assert chart.backload_type == 0
        assert chart.backload_number == 0
        assert chart.registered is False
        assert chart.symbol_hash > 0
        assert chart.is_symbol_recognized() is True

    def test_initialization_with_timeframe_enum_and_connection(self) -> None:
        """Verify initialization with Timeframe enum normalizes to string and sets hash."""
        chart = ChartDef(
            symbol="GBPUSD",
            timeframe=Timeframe.PERIOD_H1,
            connection_name="Dukascopy",
        )
        assert chart.timeframe == "H1"
        assert chart.connection_name == "Dukascopy"
        assert chart.connection_hash > 0
        assert chart.symbol_hash > 0

    def test_getters_and_setters(self) -> None:
        """Verify accessors and mutating setters."""
        chart = ChartDef("USDJPY")
        assert chart.get_symbol() == "USDJPY"
        assert chart.get_timeframe() == "M1"
        assert chart.get_instrument() == "Forex"
        assert chart.get_instrument_info() == "Forex"
        assert chart.get_symbol_info() == "Forex"
        assert chart.get_session() == "Default"
        assert chart.get_spread() == 0.0
        assert chart.is_registered() is False

        chart.set_symbol("EURJPY")
        assert chart.get_symbol() == "EURJPY"

        chart.set_session("Tokyo")
        assert chart.get_session() == "Tokyo"

        chart.set_spread(1.5)
        assert chart.get_spread() == 1.5

        chart.modify_spread(2.0)
        assert chart.get_spread() == 2.0

        chart.set_real_spread(True)
        assert chart.real_spread is True

        chart.set_registered(True)
        assert chart.is_registered() is True

        chart.set_history_from(1000)
        assert chart.get_history_from() == 1000

        chart.set_history_to(5000)
        assert chart.get_history_to() == 5000

        chart.set_loaded_history_from(1500)
        assert chart.get_loaded_history_from() == 1500

        chart.set_min_distance(5.0)
        assert chart.get_min_distance() == 5.0

        assert chart.get_bar_time_type() == 0
        assert chart.get_effective_bar_time_type() == 0
        assert chart.get_backload_type() == 0
        assert chart.get_backload_number() == 0
        assert chart.is_backtest_data_def is False
        assert chart.get_is_backtest_data_def() is False

    def test_timeframe_seconds(self) -> None:
        """Verify timeframe conversion to seconds across variants."""
        assert ChartDef("EURUSD", "M1").timeframe_seconds == 60
        assert ChartDef("EURUSD", "M5").timeframe_seconds == 300
        assert ChartDef("EURUSD", "H1").timeframe_seconds == 3600
        assert ChartDef("EURUSD", "D1").timeframe_seconds == 86400
        assert ChartDef("EURUSD", "W1").timeframe_seconds == 604800
        assert ChartDef("EURUSD", "TICK").timeframe_seconds == 0
        assert ChartDef("EURUSD", "S30").timeframe_seconds == 30
        assert ChartDef("EURUSD", "UNKNOWN").timeframe_seconds == 0

    def test_is_smaller_than(self) -> None:
        """Verify is_smaller_than compares timeframe durations correctly."""
        c_m1 = ChartDef("EURUSD", "M1")
        c_m5 = ChartDef("EURUSD", "M5")
        c_h1 = ChartDef("EURUSD", "H1")
        c_d1 = ChartDef("EURUSD", "D1")

        assert c_m1.is_smaller_than(c_m5) is True
        assert c_m5.is_smaller_than(c_h1) is True
        assert c_h1.is_smaller_than(c_d1) is True
        assert c_d1.is_smaller_than(c_h1) is False
        assert c_m1.is_smaller_than(c_m1) is False

    def test_can_be_computed_from(self) -> None:
        """Verify resample compatibility conditions."""
        c_m1 = ChartDef("EURUSD", "M1", history_from=1000, history_to=5000)
        c_m5 = ChartDef("EURUSD", "M5", history_from=1000, history_to=5000)
        c_h1 = ChartDef("EURUSD", "H1", history_from=1000, history_to=5000)
        c_tick = ChartDef("EURUSD", "TICK", history_from=500, history_to=6000)

        # Higher timeframes can be computed from lower divisible timeframes
        assert c_m5.can_be_computed_from(c_m1) is True
        assert c_h1.can_be_computed_from(c_m5) is True
        assert c_m1.can_be_computed_from(c_tick) is True

        # Lower cannot be computed from higher
        assert c_m1.can_be_computed_from(c_m5) is False

        # Non-divisible timeframes (M7 from M5)
        c_m7 = ChartDef("EURUSD", "M7")
        assert c_m7.can_be_computed_from(c_m5) is False

        # Different symbols
        c_gbp = ChartDef("GBPUSD", "M1", history_from=1000, history_to=5000)
        assert c_m5.can_be_computed_from(c_gbp) is False

        # Session mismatch
        c_rth = ChartDef("EURUSD", "M1", session="RTH")
        c_eth = ChartDef("EURUSD", "M5", session="ETH")
        assert c_eth.can_be_computed_from(c_rth) is False

        # History bounds check: source starts too late
        c_m1_late = ChartDef("EURUSD", "M1", history_from=2000, history_to=5000)
        assert c_m5.can_be_computed_from(c_m1_late) is False

        # History bounds check: source ends too early
        c_m1_early_end = ChartDef("EURUSD", "M1", history_from=1000, history_to=4000)
        assert c_m5.can_be_computed_from(c_m1_early_end) is False

    def test_is_same_connection_symbol(self) -> None:
        """Verify connection and symbol equality comparison."""
        c1 = ChartDef("EURUSD", connection_name="MetaTrader")
        c2 = ChartDef("eurusd", connection_name="metatrader")
        c3 = ChartDef("GBPUSD", connection_name="MetaTrader")
        c4 = ChartDef("EURUSD", connection_name="Dukascopy")

        assert c1.is_same_connection_symbol(c2) is True
        assert c1.is_same_connection_symbol(c3) is False
        assert c1.is_same_connection_symbol(c4) is False

    def test_get_charts_hash(self) -> None:
        """Verify unique charts hash format."""
        chart = ChartDef("EURUSD", "H1", session="Default", connection_name="MT5")
        assert chart.get_charts_hash() == "MT5_EURUSD_H1_Default"

    def test_clone_and_get_clone(self) -> None:
        """Verify cloning and optional field overrides."""
        chart = ChartDef(
            symbol="EURUSD",
            timeframe="M5",
            spread=1.2,
            history_from=1000,
            history_to=5000,
        )
        cloned = chart.clone(symbol="USDCHF", history_from=2000)
        assert cloned.symbol == "USDCHF"
        assert cloned.timeframe == "M5"
        assert cloned.spread == 1.2
        assert cloned.history_from == 2000
        assert cloned.history_to == 5000
        assert cloned.symbol_hash == abs(hash("USDCHF"))

        # SQX alias
        cloned2 = chart.get_clone(history_to=9000)
        assert cloned2.history_to == 9000
        assert cloned2.symbol == "EURUSD"

    def test_serialization_round_trip(self) -> None:
        """Verify to_dict and from_dict serialization."""
        chart = ChartDef(
            symbol="EURUSD",
            timeframe="M15",
            instrument="Forex",
            session="London",
            connection_name="Dukascopy",
            spread=0.8,
            real_spread=True,
            history_from=100000,
            history_to=200000,
            registered=True,
        )
        d = chart.to_dict()
        assert isinstance(d, dict)
        assert d["symbol"] == "EURUSD"
        assert d["timeframe"] == "M15"
        assert d["session"] == "London"

        restored = ChartDef.from_dict(d)
        assert restored == chart


class TestDataInfo:
    """Tests for DataInfo market data catalog metadata record."""

    def test_initialization_defaults(self) -> None:
        """Verify default attribute values for DataInfo."""
        info = DataInfo(id=1, symbol="EURUSD")
        assert info.id == 1
        assert info.symbol == "EURUSD"
        assert info.timeframe == "M1"
        assert info.instrument == "Forex"
        assert info.connection == ""
        assert info.timezone == "UTC"
        assert info.decimals == 4
        assert info.date_from == 0
        assert info.date_to == 0
        assert info.rows == 0
        assert info.total_days == 0
        assert info.filename == ""
        assert info.file_hash == 0
        assert info.bar_time_type == 0
        assert info.remove_weekends is True
        assert info.show is True
        assert info.source == 0
        assert info.basket_id == 0
        assert info.broker_id == 0

    def test_clone(self) -> None:
        """Verify DataInfo clone produces an independent equal copy."""
        info = DataInfo(
            id=42,
            symbol="GBPUSD",
            timeframe="H1",
            rows=5000,
            decimals=5,
        )
        cloned = info.clone()
        assert cloned == info
        assert cloned is not info

    def test_to_chart_def(self) -> None:
        """Verify conversion from DataInfo catalog metadata to ChartDef."""
        info = DataInfo(
            id=10,
            symbol="USDJPY",
            timeframe="M5",
            instrument="Forex",
            connection="MetaTrader",
            date_from=1000,
            date_to=8000,
            bar_time_type=1,
        )
        chart_def = info.to_chart_def()
        assert isinstance(chart_def, ChartDef)
        assert chart_def.symbol == "USDJPY"
        assert chart_def.timeframe == "M5"
        assert chart_def.instrument == "Forex"
        assert chart_def.connection_name == "MetaTrader"
        assert chart_def.history_from == 1000
        assert chart_def.history_to == 8000
        assert chart_def.bar_time_type == 1

    def test_serialization_round_trip(self) -> None:
        """Verify to_dict and from_dict serialization."""
        info = DataInfo(
            id=99,
            symbol="BTCUSD",
            timeframe="D1",
            instrument="Crypto",
            connection="Binance",
            timezone="UTC",
            decimals=2,
            date_from=1600000000,
            date_to=1700000000,
            rows=1000,
            total_days=365,
            filename="btcusd_d1.parquet",
            file_hash=123456789,
            bar_time_type=0,
            remove_weekends=False,
            show=True,
        )
        d = info.to_dict()
        assert isinstance(d, dict)
        assert d["symbol"] == "BTCUSD"
        assert d["rows"] == 1000

        restored = DataInfo.from_dict(d)
        assert restored == info


class TestPackageReExports:
    """Verify ChartDef and DataInfo are re-exported from app.services.data."""

    def test_re_exports_match(self) -> None:
        """Ensure package exports point to the exact same classes."""
        assert CatalogChartDef is ChartDef
        assert CatalogDataInfo is DataInfo
