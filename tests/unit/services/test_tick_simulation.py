"""Unit tests for streaming tick simulator cursors and batch tick generation.

Key Capabilities:
    - FR-DATA-STREAMING-TICK-SIMULATOR: In-memory streaming tick cursors.
    - FR-DATA-BATCH-TICK-GENERATOR: Vectorized batch tick generation and Parquet
      streaming.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pyarrow.parquet as pq
import pytest
from app.services.data import (
    PHASE_CLOSE_CODE,
    PHASE_HIGH_CODE,
    PHASE_LOW_CODE,
    PHASE_OPEN_CODE,
    SPREAD_FIXED,
    SPREAD_VARIABLE,
    SUPPORTED_SPREAD_MODELS,
    SUPPORTED_TICK_MODELS,
    TICK_MODEL_GENERATED,
    TICK_MODEL_OHLC_M1,
    TICK_MODEL_REAL,
    TICK_MODEL_TRADING_BAR,
    DefaultTickSimulator,
    MarketBar,
    MarketTick,
    SpreadsMap,
    TickEvent,
    TicksGenerator,
    TSTickSimulator,
    generate_ticks,
    generate_ticks_to_parquet,
)


class TestTickEvent:
    """Unit tests for TickEvent mutable buffer."""

    def test_default_initialization(self) -> None:
        """Verify default field values."""
        event = TickEvent()
        assert event.time == 0
        assert event.bid == 0.0
        assert event.ask == 0.0
        assert event.volume == 0.0
        assert event.symbol == ""
        assert event.symbol_hash == 0
        assert not event.is_bar_open
        assert not event.is_bar_close
        assert not event.is_set

    def test_set_mutations(self) -> None:
        """Verify set() updates fields in place."""
        event = TickEvent()
        event.set(
            time=1700000000000,
            bid=1.0500,
            ask=1.0502,
            volume=5.0,
            symbol_hash=12345,
            is_bar_open=True,
            is_bar_close=False,
        )
        assert event.is_set
        assert event.time == 1700000000000
        assert event.bid == 1.0500
        assert event.ask == 1.0502
        assert event.volume == 5.0
        assert event.symbol_hash == 12345
        assert event.is_bar_open
        assert not event.is_bar_close

    def test_copy_from(self) -> None:
        """Verify copying from another TickEvent."""
        src = TickEvent()
        src.set(
            time=1000,
            bid=1.1,
            ask=1.2,
            volume=10.0,
            symbol_hash=42,
            is_bar_open=False,
            is_bar_close=True,
        )
        src.symbol = "EURUSD"

        dst = TickEvent()
        dst.copy_from(src)
        assert dst.time == 1000
        assert dst.bid == 1.1
        assert dst.ask == 1.2
        assert dst.volume == 10.0
        assert dst.symbol == "EURUSD"
        assert dst.symbol_hash == 42
        assert not dst.is_bar_open
        assert dst.is_bar_close
        assert dst.is_set

    def test_reset(self) -> None:
        """Verify resetting event state."""
        event = TickEvent()
        event.set(time=100, bid=1.0, ask=1.1)
        event.symbol = "GBPUSD"
        event.reset()
        assert event.time == 0
        assert event.bid == 0.0
        assert event.symbol == ""
        assert not event.is_set

    def test_to_market_tick(self) -> None:
        """Verify conversion to immutable MarketTick."""
        event = TickEvent()
        event.set(time=5000, bid=1.25, ask=1.27, volume=2.5)
        tick = event.to_market_tick()
        assert isinstance(tick, MarketTick)
        assert tick.time == 5000
        assert tick.bid == 1.25
        assert tick.ask == 1.27
        assert tick.last == 1.25
        assert tick.volume == 2
        assert tick.volume_real == 2.5


class TestSpreadsMap:
    """Unit tests for SpreadsMap container."""

    def test_empty_map(self) -> None:
        """Verify empty map operations."""
        smap = SpreadsMap()
        assert not smap.contains_key("EURUSD")
        assert smap.get_spread("EURUSD", default=1.5) == 1.5

    def test_dict_initialization_and_mutations(self) -> None:
        """Verify dict loading and set_spread."""
        smap = SpreadsMap({"EURUSD": 2.0, 101: 3.5})
        assert smap.contains_key("EURUSD")
        assert smap.contains_key(101)
        assert smap.get_spread("EURUSD") == 2.0
        assert smap.get_spread(101) == 3.5

        smap.set_spread("EURUSD", 1.8)
        assert smap.get_spread("EURUSD") == 1.8


class TestDefaultTickSimulator:
    """Unit tests for DefaultTickSimulator streaming cursor."""

    @pytest.fixture
    def sample_bars(self) -> list[MarketBar]:
        """Provide sample bullish and bearish MarketBars."""
        return [
            MarketBar(
                time=100_000,
                open=1.1000,
                high=1.1050,
                low=1.0980,
                close=1.1020,
                tick_volume=100,
                spread=1,
            ),
            MarketBar(
                time=160_000,
                open=1.1020,
                high=1.1040,
                low=1.0950,
                close=1.0960,
                tick_volume=80,
                spread=2,
            ),
        ]

    def test_bullish_and_bearish_tick_traversal(
        self, sample_bars: list[MarketBar]
    ) -> None:
        """Verify 4-tick progression: Open->Low->High->Close vs Open->High->Low->Close."""
        sim = DefaultTickSimulator(point_value=0.0001, bar_duration_seconds=60)
        sim.init(sample_bars)

        event = TickEvent()
        ticks: list[tuple[float, bool, bool]] = []
        while sim.get_next_tick(event):
            ticks.append((event.bid, event.is_bar_open, event.is_bar_close))

        # Total 8 ticks (2 bars * 4 ticks)
        assert len(ticks) == 8

        # Bar 1 (Bullish: close 1.1020 >= open 1.1000): Open, Low, High, Close
        assert ticks[0][0] == pytest.approx(1.1000)
        assert (ticks[0][1], ticks[0][2]) == (True, False)
        assert ticks[1][0] == pytest.approx(1.0980)
        assert (ticks[1][1], ticks[1][2]) == (False, False)
        assert ticks[2][0] == pytest.approx(1.1050)
        assert (ticks[2][1], ticks[2][2]) == (False, False)
        assert ticks[3][0] == pytest.approx(1.1020)
        assert (ticks[3][1], ticks[3][2]) == (False, True)

        # Bar 2 (Bearish: close 1.0960 < open 1.1020): Open, High, Low, Close
        assert ticks[4][0] == pytest.approx(1.1020)
        assert (ticks[4][1], ticks[4][2]) == (True, False)
        assert ticks[5][0] == pytest.approx(1.1040)
        assert (ticks[5][1], ticks[5][2]) == (False, False)
        assert ticks[6][0] == pytest.approx(1.0950)
        assert (ticks[6][1], ticks[6][2]) == (False, False)
        assert ticks[7][0] == pytest.approx(1.0960)
        assert (ticks[7][1], ticks[7][2]) == (False, True)

    def test_spread_application(self, sample_bars: list[MarketBar]) -> None:
        """Verify spread points applied to Ask price."""
        sim = DefaultTickSimulator(
            point_value=0.0001, symbol="EURUSD", bar_duration_seconds=60
        )
        sim.set_symbols_spread({"EURUSD": 3.0})
        sim.init(sample_bars[:1])

        event = TickEvent()
        assert sim.get_next_tick(event)
        assert event.bid == pytest.approx(1.1000)
        # Ask = Bid + 3.0 * 0.0001 = 1.1003
        assert event.ask == pytest.approx(1.1003)

    def test_timestamp_offsets(self, sample_bars: list[MarketBar]) -> None:
        """Verify intra-bar millisecond distribution."""
        sim = DefaultTickSimulator(bar_duration_seconds=60)
        sim.init(sample_bars[:1])

        event = TickEvent()
        times: list[int] = []
        while sim.get_next_tick(event):
            times.append(event.time)

        assert len(times) == 4
        # Bar 1 starts at 100_000s = 100_000_000ms, 60s bar = 60_000ms
        assert times[0] == 100_000_000  # 0ms
        assert times[1] == 100_000_000 + 20_000  # 20_000ms
        assert times[2] == 100_000_000 + 40_000  # 40_000ms
        assert times[3] == 100_000_000 + 59_999  # 59_999ms

    def test_stream_ticks_generator(self, sample_bars: list[MarketBar]) -> None:
        """Verify stream_ticks yields immutable MarketTicks."""
        sim = DefaultTickSimulator()
        ticks = list(sim.stream_ticks(sample_bars))
        assert len(ticks) == 8
        assert all(isinstance(t, MarketTick) for t in ticks)

    def test_dict_bars_support(self) -> None:
        """Verify support for dict bar records."""
        dict_bars = [
            {"time": 1000, "open": 10.0, "high": 12.0, "low": 9.0, "close": 11.0}
        ]
        sim = DefaultTickSimulator()
        sim.init(dict_bars)
        event = TickEvent()
        count = 0
        while sim.get_next_tick(event):
            count += 1
        assert count == 4


class TestTSTickSimulator:
    """Unit tests for TradeStation intra-bar tick simulator."""

    def test_flat_bar(self) -> None:
        """Single-price bar emits 1 tick."""
        bar = MarketBar(
            time=1000, open=10.0, high=10.0, low=10.0, close=10.0, tick_volume=10
        )
        sim = TSTickSimulator()
        sim.init([bar])
        event = TickEvent()
        ticks = []
        while sim.get_next_tick(event):
            ticks.append(event.bid)
        assert len(ticks) == 1
        assert ticks[0] == 10.0

    def test_flat_top_and_bottom(self) -> None:
        """Flat top emits 3 ticks (Open, Low, Close); Flat bottom emits (Open, High, Close)."""
        flat_top = MarketBar(
            time=1000, open=15.0, high=15.0, low=10.0, close=12.0, tick_volume=10
        )
        flat_bottom = MarketBar(
            time=2000, open=10.0, high=15.0, low=10.0, close=12.0, tick_volume=10
        )
        sim = TSTickSimulator()
        sim.init([flat_top, flat_bottom])

        ticks = []
        event = TickEvent()
        while sim.get_next_tick(event):
            ticks.append(event.bid)

        # 3 ticks for flat top + 3 ticks for flat bottom = 6
        assert len(ticks) == 6
        # Flat top: Open(15) -> Low(10) -> Close(12)
        assert ticks[0:3] == [15.0, 10.0, 12.0]
        # Flat bottom: Open(10) -> High(15) -> Close(12)
        assert ticks[3:6] == [10.0, 15.0, 12.0]

    def test_proximity_branching(self) -> None:
        """Proximity to low vs high determines turn direction."""
        # Open=11, High=20, Low=10, Close=15: dist_to_low=1 < dist_to_high=9 -> Low first
        bar = MarketBar(
            time=1000, open=11.0, high=20.0, low=10.0, close=15.0, tick_volume=10
        )
        sim = TSTickSimulator()
        sim.init([bar])
        event = TickEvent()
        ticks = []
        while sim.get_next_tick(event):
            ticks.append(event.bid)
        assert ticks == [11.0, 10.0, 20.0, 15.0]


class TestTicksGenerator:
    """Unit tests for vectorized TicksGenerator and generate_ticks."""

    @pytest.fixture
    def ohlc_df(self) -> pd.DataFrame:
        """Provide a simple OHLC bar DataFrame with DatetimeIndex."""
        idx = pd.date_range("2026-01-01 10:00:00", periods=3, freq="1min")
        return pd.DataFrame(
            {
                "Open": [1.1000, 1.1020, 1.0980],
                "High": [1.1050, 1.1040, 1.1000],
                "Low": [1.0980, 1.0950, 1.0960],
                "Close": [1.1020, 1.0960, 1.0990],
                "Volume": [10.0, 20.0, 15.0],
                "Spread": [1.0, 2.0, 1.5],
            },
            index=idx,
        )

    def test_constants_and_supported_models(self) -> None:
        """Verify supported model enumerations."""
        assert "trading_bar" in SUPPORTED_TICK_MODELS
        assert "ohlc_m1" in SUPPORTED_TICK_MODELS
        assert "generated" in SUPPORTED_TICK_MODELS
        assert "real" in SUPPORTED_TICK_MODELS
        assert "native_spread" in SUPPORTED_SPREAD_MODELS
        assert "fixed_spread" in SUPPORTED_SPREAD_MODELS
        assert "variable_spread" in SUPPORTED_SPREAD_MODELS

    def test_trading_bar_generation(self, ohlc_df: pd.DataFrame) -> None:
        """Verify 4-tick generation per bar without signal columns."""
        gen = TicksGenerator(model=TICK_MODEL_TRADING_BAR, trading_timeframe="M1")
        df = gen.generate(ohlc_df)

        assert len(df) == 12  # 3 bars * 4 ticks
        assert list(df.columns) == [
            "bid",
            "ask",
            "last",
            "spread",
            "tick_index_in_bar",
            "is_bar_close",
            "source_bar_time",
        ]
        # Check phase bitmasks on first bar: Open=1, Low=4, High=2, Close=8
        phases = df["is_bar_close"].iloc[0:4].to_list()
        assert phases == [
            PHASE_OPEN_CODE,
            PHASE_LOW_CODE,
            PHASE_HIGH_CODE,
            PHASE_CLOSE_CODE,
        ]

    def test_generated_volume_interpolation(self, ohlc_df: pd.DataFrame) -> None:
        """Verify piecewise linear volume interpolation."""
        gen = TicksGenerator(
            model=TICK_MODEL_GENERATED,
            trading_timeframe="M1",
            spread_model=SPREAD_FIXED,
            fixed_spread_points=2.0,
        )
        df = gen.generate(ohlc_df)
        # Expected rows = sum(Volume) = 10 + 20 + 15 = 45
        assert len(df) == 45
        assert (df["spread"] == 2).all()
        # Verify first price is Open(0) and last price in bar 0 is Close(0)
        assert df["bid"].iloc[0] == pytest.approx(1.1000)
        assert df["bid"].iloc[9] == pytest.approx(1.1020)

    def test_variable_spread_stochastic_draws(self, ohlc_df: pd.DataFrame) -> None:
        """Verify variable spread generates bounded stochastic values."""
        gen = TicksGenerator(
            model=TICK_MODEL_TRADING_BAR,
            trading_timeframe="M1",
            spread_model=SPREAD_VARIABLE,
            min_spread_points=1.0,
            max_spread_points=5.0,
            random_seed=42,
        )
        df = gen.generate(ohlc_df)
        assert (df["spread"] >= 1).all()
        assert (df["spread"] <= 5).all()

    def test_ohlc_m1_model(self, ohlc_df: pd.DataFrame) -> None:
        """Verify TICK_MODEL_OHLC_M1 requires and uses m1_bars."""
        with pytest.raises(ValueError, match="requires non-empty m1_bars"):
            TicksGenerator(model=TICK_MODEL_OHLC_M1, trading_timeframe="M5").generate(
                ohlc_df
            )

        gen = TicksGenerator(
            model=TICK_MODEL_OHLC_M1,
            trading_timeframe="M5",
            m1_bars=ohlc_df,
        )
        df = gen.generate(pd.DataFrame())
        assert len(df) == 12

    def test_real_model(self) -> None:
        """Verify TICK_MODEL_REAL standardizes real ticks."""
        real_idx = pd.date_range("2026-01-01 10:00:00", periods=5, freq="1s")
        real_ticks = pd.DataFrame(
            {"bid": [1.1, 1.2, 1.3, 1.4, 1.5], "ask": [1.12, 1.22, 1.32, 1.42, 1.52]},
            index=real_idx,
        )
        gen = TicksGenerator(
            model=TICK_MODEL_REAL,
            trading_timeframe="M1",
            real_ticks=real_ticks,
        )
        df = gen.generate(pd.DataFrame())
        assert len(df) == 5
        assert "bid" in df.columns
        assert "ask" in df.columns

    def test_generate_ticks_facade(self, ohlc_df: pd.DataFrame) -> None:
        """Verify high-level generate_ticks helper adds timestamp column."""
        result = generate_ticks(
            model=TICK_MODEL_TRADING_BAR,
            trading_timeframe="M1",
            bars=ohlc_df,
        )
        assert "timestamp" in result.columns
        assert len(result) == 12
        assert isinstance(result.index, pd.RangeIndex)

    def test_config_validations(self) -> None:
        """Verify configuration boundary rejections."""
        with pytest.raises(ValueError, match="Unsupported ticks model"):
            TicksGenerator(model="invalid_model", trading_timeframe="M1")

        with pytest.raises(ValueError, match="point_value must be > 0"):
            TicksGenerator(
                model=TICK_MODEL_TRADING_BAR, trading_timeframe="M1", point_value=-1
            )

        with pytest.raises(ValueError, match="fixed_spread_points is required"):
            TicksGenerator(
                model=TICK_MODEL_TRADING_BAR,
                trading_timeframe="M1",
                spread_model=SPREAD_FIXED,
            )

        with pytest.raises(
            ValueError, match="min_spread_points and max_spread_points are required"
        ):
            TicksGenerator(
                model=TICK_MODEL_TRADING_BAR,
                trading_timeframe="M1",
                spread_model=SPREAD_VARIABLE,
            )

        with pytest.raises(
            ValueError, match="min_spread_points cannot exceed max_spread_points"
        ):
            TicksGenerator(
                model=TICK_MODEL_TRADING_BAR,
                trading_timeframe="M1",
                spread_model=SPREAD_VARIABLE,
                min_spread_points=10.0,
                max_spread_points=5.0,
            )


class TestParquetTickStreaming:
    """Unit tests for out-of-core Parquet streaming."""

    def test_generate_ticks_to_parquet(self, tmp_path: Path) -> None:
        """Verify streaming chunked output to a valid Parquet file."""
        idx = pd.date_range("2026-01-01 10:00:00", periods=50, freq="1min")
        bars = pd.DataFrame(
            {
                "Open": np.linspace(10.0, 15.0, 50),
                "High": np.linspace(11.0, 16.0, 50),
                "Low": np.linspace(9.0, 14.0, 50),
                "Close": np.linspace(10.5, 15.5, 50),
                "Volume": np.full(50, 8.0),
                "Spread": np.full(50, 1.0),
            },
            index=idx,
        )

        out_file = tmp_path / "test_ticks.parquet"
        result = generate_ticks_to_parquet(
            model=TICK_MODEL_TRADING_BAR,
            trading_timeframe="M1",
            path=out_file,
            bars=bars,
            chunk_size=10,
            max_output_rows_per_chunk=40,
        )

        assert Path(result["path"]).exists()
        # 50 bars * 4 ticks = 200 ticks
        assert result["rows"] == 200

        # Read back via pyarrow.parquet
        table = pq.read_table(out_file)
        assert table.num_rows == 200
        assert "bid" in table.column_names
        assert "ask" in table.column_names
        assert "timestamp" in table.column_names

    def test_empty_bars_parquet(self, tmp_path: Path) -> None:
        """Verify empty bars output to valid empty Parquet file."""
        out_file = tmp_path / "empty_ticks.parquet"
        result = generate_ticks_to_parquet(
            model=TICK_MODEL_TRADING_BAR,
            trading_timeframe="M1",
            path=out_file,
            bars=pd.DataFrame(),
        )
        assert result["rows"] == 0
        table = pq.read_table(out_file)
        assert table.num_rows == 0
