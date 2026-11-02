"""Unit tests for StrategyQuant exit methods, price clamping, and catalogue registry."""

from __future__ import annotations

import pytest
from app.extend.exit_methods.base import ExitType, correct_sl_pt
from app.extend.exit_methods.catalogue import (
    EXIT_METHODS_CATALOGUE,
    create_exit_method,
    get_exit_method_descriptor,
    list_exit_methods,
)
from app.extend.exit_methods.exit_after_bars import ExitAfterBars
from app.extend.exit_methods.move_sl_2_be import MoveSL2BE
from app.extend.exit_methods.profit_target import ProfitTarget
from app.extend.exit_methods.stop_loss import StopLoss
from app.extend.exit_methods.trailing_stop import TrailingStop


class TestCorrectSLPT:
    """Test suite for correct_sl_pt price clamping algorithm."""

    def test_stop_loss_clamping_long(self) -> None:
        """Assert min/max clamping for Long StopLoss."""
        # Entry 1.1000, tick_size 0.0001
        # Raw proposed SL is 1.0990 (10 pips away, too close for min 20)
        clamped = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.0990,
            direction=1,
            tick_size=0.0001,
            is_stop_loss=True,
            min_sl_pips=20,
        )
        assert clamped == pytest.approx(1.0980)

        # Max SL 50 pips -> SL cannot be further than 1.0950
        clamped_max = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.0900,
            direction=1,
            tick_size=0.0001,
            is_stop_loss=True,
            max_sl_pips=50,
        )
        assert clamped_max == pytest.approx(1.0950)

    def test_stop_loss_clamping_short(self) -> None:
        """Assert min/max clamping for Short StopLoss."""
        # Entry 1.1000, tick_size 0.0001, direction -1, is_sl True -> n2 = 1
        # Min SL 20 pips -> min limit = 1.1000 + (1 * 20) * 0.0001 = 1.1020
        clamped = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.1010,
            direction=-1,
            tick_size=0.0001,
            is_stop_loss=True,
            min_sl_pips=20,
        )
        assert clamped == pytest.approx(1.1020)

        # Max SL 50 pips -> max limit = 1.1000 + 50 * 0.0001 = 1.1050
        clamped_max = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.1100,
            direction=-1,
            tick_size=0.0001,
            is_stop_loss=True,
            max_sl_pips=50,
        )
        assert clamped_max == pytest.approx(1.1050)

    def test_profit_target_clamping_long(self) -> None:
        """Assert min/max clamping for Long ProfitTarget."""
        # Entry 1.1000, direction 1, is_sl False -> n2 = 1
        # Min PT 30 pips -> limit = 1.1000 + 30 * 0.0001 = 1.1030
        clamped = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.1010,
            direction=1,
            tick_size=0.0001,
            is_stop_loss=False,
            min_pt_pips=30,
        )
        assert clamped == pytest.approx(1.1030)

        # Max PT 100 pips -> limit = 1.1000 + 100 * 0.0001 = 1.1100
        clamped_max = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.1200,
            direction=1,
            tick_size=0.0001,
            is_stop_loss=False,
            max_pt_pips=100,
        )
        assert clamped_max == pytest.approx(1.1100)

    def test_profit_target_clamping_short(self) -> None:
        """Assert min/max clamping for Short ProfitTarget."""
        # Entry 1.1000, direction -1, is_sl False -> n2 = -1
        # Min PT 30 pips -> limit = 1.1000 - 30 * 0.0001 = 1.0970
        clamped = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.0990,
            direction=-1,
            tick_size=0.0001,
            is_stop_loss=False,
            min_pt_pips=30,
        )
        assert clamped == pytest.approx(1.0970)

        # Max PT 100 pips -> limit = 1.1000 - 100 * 0.0001 = 1.0900
        clamped_max = correct_sl_pt(
            entry_price=1.1000,
            exit_price=1.0800,
            direction=-1,
            tick_size=0.0001,
            is_stop_loss=False,
            max_pt_pips=100,
        )
        assert clamped_max == pytest.approx(1.0900)


class TestExitAfterBars:
    """Test suite for ExitAfterBars exit method."""

    def test_validation(self) -> None:
        """Assert negative exit_after_bars raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ExitAfterBars(exit_after_bars=-1)

    def test_should_exit(self) -> None:
        """Assert should_exit triggers only when bars meet or exceed threshold."""
        exit_method = ExitAfterBars(exit_after_bars=5)
        assert exit_method.should_exit(bars_in_trade=0) is False
        assert exit_method.should_exit(bars_in_trade=4) is False
        assert exit_method.should_exit(bars_in_trade=5) is True
        assert exit_method.should_exit(bars_in_trade=10) is True
        assert exit_method.evaluate(bars_in_trade=5) is True

        # When set to 0, never triggers
        disabled = ExitAfterBars(exit_after_bars=0)
        assert disabled.should_exit(bars_in_trade=100) is False

    def test_compute_value_not_supported(self) -> None:
        """Assert compute_value raises NotImplementedError."""
        exit_method = ExitAfterBars(exit_after_bars=5)
        with pytest.raises(NotImplementedError):
            exit_method.compute_value(direction=1, price=1.1000)

    def test_to_policy(self) -> None:
        """Assert conversion to trading execution policy."""
        exit_method = ExitAfterBars(exit_after_bars=15)
        policy = exit_method.to_policy()
        assert policy.bars == 15
        assert exit_method.exit_type == ExitType.EXIT_AFTER_BARS
        assert exit_method.sort_order == 500


class TestMoveSL2BE:
    """Test suite for MoveSL2BE exit method."""

    def test_validation(self) -> None:
        """Assert negative distance parameters raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            MoveSL2BE(move_sl_to_be=-0.001)
        with pytest.raises(ValueError, match="non-negative"):
            MoveSL2BE(sl_to_be_add_pips=-1.0)

    def test_long_move_sl_2_be(self) -> None:
        """Assert Long position moves SL to breakeven + offset."""
        sl2be = MoveSL2BE(move_sl_to_be=0.0020, sl_to_be_add_pips=2.0)
        open_price = 1.1000
        tick_size = 0.0001
        # Below trigger (gain 15 pips < 20 pips)
        assert (
            sl2be.evaluate_new_sl(
                open_price=open_price,
                current_price=1.1015,
                direction=1,
                tick_size=tick_size,
            )
            is None
        )

        # Reached trigger (gain 25 pips >= 20 pips)
        # Expected new SL = 1.1000 + 2 * 0.0001 = 1.1002
        new_sl = sl2be.evaluate_new_sl(
            open_price=open_price,
            current_price=1.1025,
            direction=1,
            tick_size=tick_size,
        )
        assert new_sl == pytest.approx(1.1002)

        # If existing SL is already tighter (1.1010), don't loosen
        assert (
            sl2be.evaluate_new_sl(
                open_price=open_price,
                current_price=1.1025,
                direction=1,
                current_sl=1.1010,
                tick_size=tick_size,
            )
            is None
        )

    def test_short_move_sl_2_be(self) -> None:
        """Assert Short position moves SL to breakeven - offset."""
        sl2be = MoveSL2BE(move_sl_to_be=0.0020, sl_to_be_add_pips=3.0)
        open_price = 1.1000
        tick_size = 0.0001

        # Below trigger (gain 10 pips < 20 pips)
        assert (
            sl2be.evaluate_new_sl(
                open_price=open_price,
                current_price=1.0990,
                direction=-1,
                tick_size=tick_size,
            )
            is None
        )

        # Reached trigger (gain 25 pips >= 20 pips)
        # Expected new SL = 1.1000 - 3 * 0.0001 = 1.0997
        new_sl = sl2be.evaluate_new_sl(
            open_price=open_price,
            current_price=1.0975,
            direction=-1,
            tick_size=tick_size,
        )
        assert new_sl == pytest.approx(1.0997)

        # Existing SL already tighter (1.0990) -> returns None
        assert (
            sl2be.evaluate_new_sl(
                open_price=open_price,
                current_price=1.0975,
                direction=-1,
                current_sl=1.0990,
                tick_size=tick_size,
            )
            is None
        )

    def test_zero_activation_and_policy(self) -> None:
        """Assert zero activation returns None and to_policy converts properly."""
        sl2be = MoveSL2BE(move_sl_to_be=0.0)
        assert sl2be.evaluate(1.1000, 1.1050, 1) is None
        with pytest.raises(NotImplementedError):
            sl2be.compute_value(direction=1, price=1.1000)
        policy = sl2be.to_policy()
        assert policy.activation == 0.0
        assert sl2be.exit_type == ExitType.MOVE_SL_2_BE


class TestProfitTarget:
    """Test suite for ProfitTarget exit method."""

    def test_validation(self) -> None:
        """Assert negative profit target raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            ProfitTarget(profit_target=-0.001)

    def test_compute_value_and_clamping(self) -> None:
        """Assert target computation for Long and Short."""
        pt = ProfitTarget(profit_target=0.0050)
        # Long: 1.1000 + 0.0050 = 1.1050
        assert pt.compute_value(direction=1, price=1.1000) == pytest.approx(1.1050)
        # Short: 1.1000 - 0.0050 = 1.0950
        assert pt.compute_value(direction=-1, price=1.1000) == pytest.approx(1.0950)

    def test_should_exit_and_evaluate(self) -> None:
        """Assert trigger evaluation for Long and Short."""
        pt = ProfitTarget(profit_target=0.0050)
        target = 1.1050
        assert not pt.should_exit(
            current_price=1.1040, direction=1, target_price=target
        )
        assert pt.should_exit(current_price=1.1050, direction=1, target_price=target)
        assert pt.should_exit(current_price=1.1060, direction=1, target_price=target)

        short_target = 1.0950
        assert not pt.should_exit(
            current_price=1.0960, direction=-1, target_price=short_target
        )
        assert pt.should_exit(
            current_price=1.0950, direction=-1, target_price=short_target
        )

        # Polymorphic evaluate
        assert pt.evaluate(1, 1.1000) == pytest.approx(1.1050)
        assert pt.evaluate(1.1060, 1, 1.1050) is True

    def test_to_policy(self) -> None:
        """Assert to_policy conversion."""
        pt = ProfitTarget(profit_target=0.0050)
        policy = pt.to_policy(price=1.1050)
        assert policy.price == 1.1050
        assert pt.exit_type == ExitType.PROFIT_TARGET


class TestStopLoss:
    """Test suite for StopLoss exit method."""

    def test_validation(self) -> None:
        """Assert negative stop loss raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            StopLoss(stop_loss=-0.001)

    def test_compute_value_and_clamping(self) -> None:
        """Assert stop loss computation for Long and Short."""
        sl = StopLoss(stop_loss=0.0030)
        # Long: 1.1000 - 0.0030 = 1.0970
        assert sl.compute_value(direction=1, price=1.1000) == pytest.approx(1.0970)
        # Short: 1.1000 + 0.0030 = 1.1030
        assert sl.compute_value(direction=-1, price=1.1000) == pytest.approx(1.1030)

    def test_fix_initial_stop_distance(self) -> None:
        """Assert distance rounding and tie-break behavior."""
        # Standard rounding
        assert StopLoss.fix_initial_stop_distance(
            0.00254, 0.0001, is_long=True
        ) == pytest.approx(0.0025)
        assert StopLoss.fix_initial_stop_distance(
            0.00256, 0.0001, is_long=True
        ) == pytest.approx(0.0026)
        # Non-positive tick step returns distance unchanged
        assert StopLoss.fix_initial_stop_distance(0.0025, 0.0, is_long=True) == 0.0025

        # Tie-break with rounds_ties_up=True for long
        assert StopLoss.fix_initial_stop_distance(
            0.00255, 0.0001, is_long=True, rounds_ties_up=True
        ) == pytest.approx(0.0025)

    def test_should_exit_and_evaluate(self) -> None:
        """Assert stop loss triggers for Long and Short."""
        sl = StopLoss(stop_loss=0.0030)
        stop = 1.0970
        assert not sl.should_exit(current_price=1.0980, direction=1, stop_price=stop)
        assert sl.should_exit(current_price=1.0970, direction=1, stop_price=stop)
        assert sl.should_exit(current_price=1.0960, direction=1, stop_price=stop)

        short_stop = 1.1030
        assert not sl.should_exit(
            current_price=1.1020, direction=-1, stop_price=short_stop
        )
        assert sl.should_exit(current_price=1.1030, direction=-1, stop_price=short_stop)

        # Polymorphic evaluate
        assert sl.evaluate(1, 1.1000) == pytest.approx(1.0970)
        assert sl.evaluate(1.0960, 1, 1.0970) is True

    def test_to_policy(self) -> None:
        """Assert to_policy conversion."""
        sl = StopLoss(stop_loss=0.0030)
        policy = sl.to_policy(price=1.0970)
        assert policy.price == 1.0970
        assert sl.exit_type == ExitType.STOP_LOSS


class TestTrailingStop:
    """Test suite for TrailingStop exit method."""

    def test_validation(self) -> None:
        """Assert negative distance parameters raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            TrailingStop(trailing_stop=-0.001)
        with pytest.raises(ValueError, match="non-negative"):
            TrailingStop(trailing_activation=-0.001)

    def test_long_trailing_stop(self) -> None:
        """Assert Long position ratchets stop forward without loosening."""
        ts = TrailingStop(trailing_stop=0.0020, trailing_activation=0.0030)
        open_price = 1.1000

        # Gain 20 pips < activation 30 pips -> returns None
        assert (
            ts.evaluate_trailing_stop(
                open_price=open_price, current_price=1.1020, direction=1
            )
            is None
        )

        # Gain 40 pips >= activation 30 pips -> candidate SL = 1.1040 - 0.0020 = 1.1020
        new_sl = ts.evaluate_trailing_stop(
            open_price=open_price, current_price=1.1040, direction=1
        )
        assert new_sl == pytest.approx(1.1020)

        # Current SL is already 1.1025 -> candidate 1.1020 is not tighter -> returns None
        assert (
            ts.evaluate_trailing_stop(
                open_price=open_price,
                current_price=1.1040,
                direction=1,
                current_sl=1.1025,
            )
            is None
        )

    def test_short_trailing_stop(self) -> None:
        """Assert Short position ratchets stop forward without loosening."""
        ts = TrailingStop(trailing_stop=0.0020, trailing_activation=0.0030)
        open_price = 1.1000

        # Gain 20 pips < activation 30 pips -> returns None
        assert (
            ts.evaluate_trailing_stop(
                open_price=open_price, current_price=1.0980, direction=-1
            )
            is None
        )

        # Gain 40 pips >= activation 30 pips -> candidate SL = 1.0960 + 0.0020 = 1.0980
        new_sl = ts.evaluate_trailing_stop(
            open_price=open_price, current_price=1.0960, direction=-1
        )
        assert new_sl == pytest.approx(1.0980)

        # Current SL already 1.0975 -> candidate 1.0980 is higher (looser) -> returns None
        assert (
            ts.evaluate_trailing_stop(
                open_price=open_price,
                current_price=1.0960,
                direction=-1,
                current_sl=1.0975,
            )
            is None
        )

    def test_zero_distance_and_policy(self) -> None:
        """Assert zero trailing_stop returns None and to_policy converts properly."""
        ts = TrailingStop(trailing_stop=0.0)
        assert ts.evaluate(1.1000, 1.1050, 1) is None
        with pytest.raises(NotImplementedError):
            ts.compute_value(direction=1, price=1.1000)
        with pytest.raises(ValueError, match="positive"):
            ts.to_policy()

        active_ts = TrailingStop(trailing_stop=0.0020, trailing_activation=0.0010)
        policy = active_ts.to_policy()
        assert policy.distance == 0.0020
        assert active_ts.exit_type == ExitType.TRAILING_STOP


class TestCatalogue:
    """Test suite for ExitMethods catalogue registry."""

    def test_list_exit_methods(self) -> None:
        """Assert catalogue contains exactly all 5 exit method definitions."""
        methods = list_exit_methods()
        assert len(methods) == 5
        names = [m.class_name for m in methods]
        assert names == [
            "StopLoss",
            "ProfitTarget",
            "MoveSL2BE",
            "TrailingStop",
            "ExitAfterBars",
        ]

    def test_get_descriptor(self) -> None:
        """Assert descriptor lookup by name."""
        desc = get_exit_method_descriptor("ExitAfterBars")
        assert desc is not None
        assert desc.display_name == "Exit After Bars"
        assert desc.exit_type == ExitType.EXIT_AFTER_BARS

        assert get_exit_method_descriptor("NonExistent") is None

    def test_create_exit_method(self) -> None:
        """Assert factory instantiation by name."""
        for name in EXIT_METHODS_CATALOGUE:
            instance = create_exit_method(name)
            assert instance.name == EXIT_METHODS_CATALOGUE[name].display_name

        with pytest.raises(KeyError, match="Unknown exit method"):
            create_exit_method("UnknownMethod")
