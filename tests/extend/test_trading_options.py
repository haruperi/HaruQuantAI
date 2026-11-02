"""Unit tests for TradingOptions cohort."""

from __future__ import annotations

from app.extend.blocks.bar_time._common import DateTime
from app.extend.trading_options import (
    BaseTradingOption,
    DontTradeOnWeekends,
    ExitAtEndOfDay,
    ExitOnFriday,
    LimitTimeRange,
    MaxDistanceFromMarket,
    MaxTradesPerDay,
    MinMaxSLPT,
    TradingOption,
    UseInitialSLPT,
)
from app.extend.trading_options.base import _in_time_window, _parse_hhmm
from app.extend.trading_options.options import (
    DontTradeOnWeekends as OptionsDontTradeOnWeekends,
)


class TestTradingOptionsBase:
    """Test suite for base classes and time utility functions."""

    def test_base_trading_option_aliases_and_attributes(self) -> None:
        """Verify BaseTradingOption and TradingOption alias attributes."""
        opt = BaseTradingOption()
        assert opt.name == "BaseTradingOption"
        assert opt.category == "TradingOptions"
        assert TradingOption is BaseTradingOption

    def test_parse_hhmm_variants(self) -> None:
        """Verify _parse_hhmm with integer, string with colon, and plain string."""
        assert _parse_hhmm(1430) == 1430
        assert _parse_hhmm("14:30") == 1430
        assert _parse_hhmm(" 08:00 ") == 800
        assert _parse_hhmm("2300") == 2300

    def test_in_time_window_standard_and_cross_midnight(self) -> None:
        """Verify _in_time_window for both standard and overnight windows."""
        # Standard window: 0800 - 1700
        assert _in_time_window(1200, 800, 1700) is True
        assert _in_time_window(800, 800, 1700) is True
        assert _in_time_window(1700, 800, 1700) is True
        assert _in_time_window(759, 800, 1700) is False
        assert _in_time_window(1701, 800, 1700) is False

        # Cross-midnight window: 2200 - 0400
        assert _in_time_window(2300, 2200, 400) is True
        assert _in_time_window(200, 2200, 400) is True
        assert _in_time_window(2200, 2200, 400) is True
        assert _in_time_window(400, 2200, 400) is True
        assert _in_time_window(1200, 2200, 400) is False


class TestDontTradeOnWeekends:
    """Test suite for DontTradeOnWeekends."""

    def test_weekend_blackout_and_open_windows(self) -> None:
        """Verify weekend blackout logic across weekdays and weekend days."""
        fri_early = DateTime.to_long(2024, 1, 5, 18, 0, 0)
        fri_late = DateTime.to_long(2024, 1, 5, 21, 0, 0)
        sat_noon = DateTime.to_long(2024, 1, 6, 12, 0, 0)
        sun_early = DateTime.to_long(2024, 1, 7, 18, 0, 0)
        sun_late = DateTime.to_long(2024, 1, 7, 22, 30, 0)
        mon_morning = DateTime.to_long(2024, 1, 8, 10, 0, 0)

        opt = DontTradeOnWeekends(friday_close_time="20:00", sunday_open_time="22:00")
        assert opt.is_trading_allowed(fri_early) is True
        assert opt.is_trading_allowed(fri_late) is False
        assert opt.is_trading_allowed(sat_noon) is False
        assert opt.is_trading_allowed(sun_early) is False
        assert opt.is_trading_allowed(sun_late) is True
        assert opt.is_trading_allowed(mon_morning) is True


class TestExitAtEndOfDay:
    """Test suite for ExitAtEndOfDay."""

    def test_should_exit_timing(self) -> None:
        """Verify exit trigger based on configured exit time."""
        before_cutoff = DateTime.to_long(2024, 1, 5, 22, 0, 0)
        at_cutoff = DateTime.to_long(2024, 1, 5, 23, 0, 0)
        after_cutoff = DateTime.to_long(2024, 1, 5, 23, 30, 0)

        opt = ExitAtEndOfDay(exit_time="23:00")
        assert opt.should_exit(before_cutoff) is False
        assert opt.should_exit(at_cutoff) is True
        assert opt.should_exit(after_cutoff) is True


class TestExitOnFriday:
    """Test suite for ExitOnFriday."""

    def test_should_exit_friday_only(self) -> None:
        """Verify Friday cutoff only triggers on Friday."""
        fri_before = DateTime.to_long(2024, 1, 5, 19, 0, 0)
        fri_after = DateTime.to_long(2024, 1, 5, 20, 30, 0)
        thu_after = DateTime.to_long(2024, 1, 4, 21, 0, 0)

        opt = ExitOnFriday(exit_time="20:00")
        assert opt.should_exit(fri_before) is False
        assert opt.should_exit(fri_after) is True
        assert opt.should_exit(thu_after) is False


class TestLimitTimeRange:
    """Test suite for LimitTimeRange."""

    def test_entry_and_exit_ranges(self) -> None:
        """Verify entry permission and conditional exit outside range."""
        inside_time = DateTime.to_long(2024, 1, 8, 11, 0, 0)
        outside_time = DateTime.to_long(2024, 1, 8, 18, 0, 0)

        opt_no_exit = LimitTimeRange(
            range_from="09:00", range_to="16:00", exit_at_end_of_range=False
        )
        assert opt_no_exit.is_entry_allowed(inside_time) is True
        assert opt_no_exit.is_entry_allowed(outside_time) is False
        assert opt_no_exit.should_exit(inside_time) is False
        assert opt_no_exit.should_exit(outside_time) is False

        opt_with_exit = LimitTimeRange(
            range_from="09:00", range_to="16:00", exit_at_end_of_range=True
        )
        assert opt_with_exit.should_exit(inside_time) is False
        assert opt_with_exit.should_exit(outside_time) is True


class TestMaxDistanceFromMarket:
    """Test suite for MaxDistanceFromMarket."""

    def test_order_price_validity(self) -> None:
        """Verify price percentage distance clamping and zero/negative guards."""
        opt = MaxDistanceFromMarket(max_distance_pct=5.0)
        assert opt.is_order_price_valid(market_price=100.0, order_price=104.0) is True
        assert opt.is_order_price_valid(market_price=100.0, order_price=106.0) is False
        # Invalid inputs
        assert opt.is_order_price_valid(market_price=0.0, order_price=100.0) is False
        assert opt.is_order_price_valid(market_price=100.0, order_price=0.0) is False

        # Zero distance pct disables check
        opt_zero = MaxDistanceFromMarket(max_distance_pct=0.0)
        assert (
            opt_zero.is_order_price_valid(market_price=100.0, order_price=200.0) is True
        )


class TestMaxTradesPerDay:
    """Test suite for MaxTradesPerDay."""

    def test_trades_limit(self) -> None:
        """Verify maximum trades per day enforcement."""
        opt = MaxTradesPerDay(max_trades=3)
        assert opt.is_entry_allowed(2) is True
        assert opt.is_entry_allowed(3) is False
        assert opt.is_entry_allowed(4) is False

        # Zero or negative max_trades disables limit
        opt_unlimited = MaxTradesPerDay(max_trades=0)
        assert opt_unlimited.is_entry_allowed(100) is True


class TestMinMaxSLPT:
    """Test suite for MinMaxSLPT."""

    def test_clamp_sl_and_pt(self) -> None:
        """Verify clamping stop-loss and profit-target pip distances."""
        opt = MinMaxSLPT(min_sl=10.0, max_sl=100.0, min_pt=15.0, max_pt=200.0)
        assert opt.clamp_sl_pips(0.0) == 0.0
        assert opt.clamp_sl_pips(5.0) == 10.0
        assert opt.clamp_sl_pips(50.0) == 50.0
        assert opt.clamp_sl_pips(150.0) == 100.0

        assert opt.clamp_pt_pips(0.0) == 0.0
        assert opt.clamp_pt_pips(10.0) == 15.0
        assert opt.clamp_pt_pips(100.0) == 100.0
        assert opt.clamp_pt_pips(250.0) == 200.0

        # Zero boundaries disable clamping
        opt_zero = MinMaxSLPT(min_sl=0.0, max_sl=0.0, min_pt=0.0, max_pt=0.0)
        assert opt_zero.clamp_sl_pips(500.0) == 500.0
        assert opt_zero.clamp_pt_pips(500.0) == 500.0


class TestUseInitialSLPT:
    """Test suite for UseInitialSLPT."""

    def test_should_attach_initial_brackets(self) -> None:
        """Verify initial bracket attachment flag."""
        opt_true = UseInitialSLPT(use_initial_sl_pt=True)
        assert opt_true.should_attach_initial_brackets() is True

        opt_false = UseInitialSLPT(use_initial_sl_pt=False)
        assert opt_false.should_attach_initial_brackets() is False


class TestFacadeReExport:
    """Verify options facade backward compatibility."""

    def test_facade_re_export(self) -> None:
        """Verify options.py re-exports match individual modules."""
        assert OptionsDontTradeOnWeekends is DontTradeOnWeekends
