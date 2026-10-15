"""Unit tests for foundational market data contracts in data_manager workspace."""

from __future__ import annotations

import pytest
from app.services.brokers.base import BridgeError as BaseBridgeError
from app.workspace.data_manager.contracts import (
    MAX_POSITION,
    MAX_RECORDS,
    READ_TIMEOUT,
    TIMEFRAME_SECONDS,
    BridgeError,
    MarketBar,
    MarketTick,
    Timeframe,
    main,
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
    """Verify boundary limits, bridge error re-export, and main demonstration."""

    def test_constants_and_bridge_error(self) -> None:
        """Verify boundary constants and BridgeError identity."""
        assert MAX_RECORDS == 1000
        assert MAX_POSITION == 2**31 - 1
        assert READ_TIMEOUT == 60.0
        assert BridgeError is BaseBridgeError

    def test_main_demonstration(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify that contracts main() executes and prints expected diagnostics."""
        main()
        captured = capsys.readouterr().out
        assert "Timeframe: M1" in captured
        assert "Bar: bullish=True" in captured
        assert "Tick: mid=" in captured
