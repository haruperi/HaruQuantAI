"""Unit tests for all 13 indicator block families and condition helpers."""

from __future__ import annotations

import numpy as np
import pytest
from app.services.indicators.base import IndicatorSeries
from app.services.indicators.momentum.cci import CCI
from app.services.indicators.momentum.macd import MACD
from app.services.indicators.momentum.qqe import QQE
from app.services.indicators.momentum.stochastic import Stochastic
from app.services.indicators.momentum.wave_trend import WaveTrend
from app.services.indicators.trend.adx import ADX
from app.services.indicators.trend.ichimoku import Ichimoku
from app.services.indicators.trend.moving_average import MovingAverage
from app.services.indicators.volatility.bar_range import BarRange
from app.services.indicators.volatility.bollinger_bands import BollingerBands
from app.services.indicators.volatility.keltner_channel import KeltnerChannel
from app.services.indicators.volume.cot import COT
from app.services.indicators.volume.volume_profile import VolumeProfile


def test_adx_calculate_and_all_conditions() -> None:
    """Verify ADX calculation and all 8 Main + 5 DI/trend condition helpers."""
    high = np.linspace(10.0, 25.0, 30)
    low = high - 1.5
    close = high - 0.3
    adx_dict = ADX.calculate(high, low, close, period=5)
    assert "main" in adx_dict and "di_plus" in adx_dict and "di_minus" in adx_dict

    # Short series branch & invalid period fallback
    short_adx = ADX.calculate([1.0, 2.0], [0.5, 1.0], [0.8, 1.5], period=0)
    assert np.isnan(short_adx["main"].get(0))

    s = IndicatorSeries([15.0, 12.0, 18.0, 22.0])
    d = {
        "main": s,
        "di_plus": IndicatorSeries([10.0, 20.0]),
        "di_minus": IndicatorSeries([15.0, 12.0]),
    }
    assert ADX.is_rising(d, shift=0) is True
    assert ADX.is_falling(d, shift=2) is True
    assert ADX.is_higher(d, 20.0, shift=0) is True
    assert ADX.is_lower(d, 20.0, shift=1) is True
    assert ADX.crosses_above(d, 20.0, shift=0) is True
    assert ADX.crosses_below(d, 14.0, shift=2) is True
    assert ADX.changes_up(d, shift=1) is True
    assert ADX.changes_down(IndicatorSeries([10.0, 20.0, 15.0]), shift=0) is True
    assert ADX.di_plus_crosses_above_di_minus(d, shift=0) is True
    assert ADX.di_plus_crosses_below_di_minus(d, shift=0) is False
    assert ADX.di_plus_higher_di_minus(d, shift=0) is True
    assert ADX.di_plus_lower_di_minus(d, shift=0) is False
    assert ADX.is_trending(d, threshold=20.0, shift=0) is True


def test_bar_range_time_windows_and_conditions() -> None:
    """Verify BarRange time-window extrema, fixed_pips, and range conditions."""
    high = np.array([10.0, 12.0, 11.5, 14.0, 13.0, 12.5])
    low = np.array([9.0, 10.5, 10.8, 11.0, 12.0, 11.0])
    rng = BarRange.calculate(high, low)
    assert len(rng) == 6
    assert BarRange.fixed_pips(50, 0.0001) == pytest.approx(0.005)
    assert BarRange.is_biggest_range(rng, period=3, shift=2) is True
    assert BarRange.is_smallest_range(rng, period=3, shift=3) is True
    assert BarRange.is_highest_in_range(rng, lookback=1, shift=2) is True
    assert BarRange.is_lowest_in_range(rng, lookback=1, shift=1) is True
    assert BarRange.in_range_pips(rng, 50.0, 50000.0, pip_size=0.01, shift=0) is True
    assert BarRange.is_rising(rng, shift=0) is True
    assert BarRange.is_falling(rng, shift=1) is True
    assert BarRange.is_greater(rng, 1.0, shift=0) is True
    assert BarRange.is_lower(rng, 2.0, shift=0) is True

    # Time-window HighestInRange and LowestInRange (epoch seconds)
    base_sec = 1700006400  # midnight UTC
    ts = [base_sec + h * 3600 for h in (8, 9, 10, 11, 12, 13)]
    hi_rng = BarRange.highest_in_range(ts, high, time_from=900, time_to=1100)
    lo_rng = BarRange.lowest_in_range(ts, low, time_from=900, time_to=1100)
    assert hi_rng.get(0) == pytest.approx(12.0)
    assert lo_rng.get(0) == pytest.approx(10.5)
    assert len(BarRange.highest_in_range([], [], 900, 1100)) == 0
    assert len(BarRange.lowest_in_range([], [], 900, 1100)) == 0


def test_bollinger_bands_value_and_bar_conditions() -> None:
    """Verify BollingerBands range, width ratio, slopes, and 12 bar open/close checks."""
    close = np.array([10.0, 10.2, 10.5, 10.3, 10.8, 11.5, 12.2])
    bb = BollingerBands.calculate(close, period=3, deviation=2.0)
    assert "range" in bb
    assert len(BollingerBands.bb_range(close, period=3, deviation=2.0)) == len(close)
    assert len(BollingerBands.bb_width_ratio(close, period=3, deviation=2.0)) == len(
        close
    )

    bands = {
        "upper": IndicatorSeries([11.0, 12.0, 13.0]),
        "middle": IndicatorSeries([10.0, 10.5, 11.0]),
        "lower": IndicatorSeries([9.0, 8.5, 8.0]),
    }
    c_ser = IndicatorSeries([10.0, 11.5, 13.5])
    o_ser = IndicatorSeries([10.0, 11.5, 12.5])

    assert BollingerBands.upper_is_rising(bands, shift=0) is True
    assert BollingerBands.upper_is_falling(bands, shift=0) is False
    assert BollingerBands.lower_is_falling(bands, shift=0) is True
    assert BollingerBands.lower_is_rising(bands, shift=0) is False
    assert BollingerBands.price_crosses_above_upper(c_ser, bands, shift=0) is True
    assert BollingerBands.price_higher_upper(c_ser, bands, shift=0) is True
    assert BollingerBands.bar_closes_above_upper(c_ser, bands, shift=0) is True
    assert BollingerBands.bar_closes_below_upper(c_ser, bands, shift=1) is True
    assert BollingerBands.bar_closes_above_lower(c_ser, bands, shift=0) is True
    assert (
        BollingerBands.bar_closes_below_lower([7.0, 7.5, 7.0], bands, shift=0) is True
    )
    assert BollingerBands.bar_opens_above_upper(o_ser, bands, shift=0) is True
    assert BollingerBands.bar_opens_below_upper([10.0, 11.0, 11.5], bands, shift=0)
    assert BollingerBands.bar_opens_above_lower(o_ser, bands, shift=0) is True
    assert BollingerBands.bar_opens_below_lower([9.0, 8.0, 7.5], bands, shift=0) is True
    assert (
        BollingerBands.bar_opens_above_upper_after_open_below(o_ser, bands, shift=0)
        is True
    )
    assert (
        BollingerBands.bar_opens_below_upper_after_open_above(
            [10.0, 12.5, 11.5], bands, shift=0
        )
        is True
    )
    assert (
        BollingerBands.bar_opens_above_lower_after_open_below(
            [9.0, 8.0, 9.0], bands, shift=0
        )
        is True
    )
    assert (
        BollingerBands.bar_opens_below_lower_after_open_above(
            [9.0, 9.0, 8.0], bands, shift=0
        )
        is True
    )


def test_cci_and_woodies_patterns() -> None:
    """Verify CCI standard conditions and all 10 Woodies CCI pattern blocks."""
    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 14.0, 15.0])
    low = high - 1.0
    close = high - 0.2
    cci = CCI.calculate(high, low, close, period=3)
    assert len(cci) == 7

    s_turn = IndicatorSeries([20.0, 10.0, 30.0])
    assert CCI.is_rising(s_turn, shift=0) is True
    assert CCI.is_falling(s_turn, shift=1) is True
    assert CCI.changes_up(s_turn, shift=0) is True
    assert CCI.changes_down(IndicatorSeries([10.0, 30.0, 20.0]), shift=0) is True
    assert CCI.crosses_above(s_turn, 15.0, shift=0) is True
    assert CCI.crosses_below(s_turn, 15.0, shift=1) is True
    assert CCI.is_higher(s_turn, lookback=1, shift=0) is True
    assert CCI.is_lower(s_turn, lookback=1, shift=1) is True
    assert CCI.is_greater(s_turn, 25.0, shift=0) is True
    assert CCI.is_lower_level(s_turn, 25.0, shift=1) is True

    assert CCI.woodies_zero_line_break_up(IndicatorSeries([-5.0, 10.0])) is True
    assert CCI.woodies_zero_line_break_down(IndicatorSeries([5.0, -10.0])) is True
    assert (
        CCI.woodies_trend_up(IndicatorSeries([10.0, 20.0, 30.0, 40.0, 50.0, 60.0]))
        is True
    )
    assert (
        CCI.woodies_trend_down(
            IndicatorSeries([-10.0, -20.0, -30.0, -40.0, -50.0, -60.0])
        )
        is True
    )
    # Woodies ZLR Up: 6 bars > 0, c2 > c1, curr > c1, diffs > factor, all in (-100, 100)
    zlr_up = IndicatorSeries([20.0, 30.0, 40.0, 60.0, 30.0, 55.0])
    assert CCI.woodies_zlr_up(zlr_up, factor=15.0) is True
    zlr_dn = IndicatorSeries([-20.0, -30.0, -40.0, -60.0, -30.0, -55.0])
    assert CCI.woodies_zlr_down(zlr_dn, factor=15.0) is True

    # Woodies Famir Up: c6..c1 < 0, c2 > c1 and c2 > c3 by > factor, curr > c1 and curr > -50
    famir_up = IndicatorSeries([-60.0, -50.0, -40.0, -50.0, -20.0, -45.0, -10.0])
    assert CCI.woodies_famir_up(famir_up, factor=15.0) is True
    famir_dn = IndicatorSeries([60.0, 50.0, 40.0, 50.0, 20.0, 45.0, 10.0])
    assert CCI.woodies_famir_down(famir_dn, factor=15.0) is True

    # Woodies Vegas Trade Up: c6..c1 < 0, one of c5..c1 < -200, c1<c2, c1<c3, c4<c2, c4<c3, c2-c1>F, c3-c4>F, curr > (c3+c2)/2
    vegas_up = IndicatorSeries([-50.0, -220.0, -90.0, -60.0, -50.0, -80.0, -40.0])
    assert CCI.woodies_vegas_trade_up(vegas_up, factor=15.0) is True
    vegas_dn = IndicatorSeries([50.0, 220.0, 90.0, 60.0, 50.0, 80.0, 40.0])
    assert CCI.woodies_vegas_trade_down(vegas_dn, factor=15.0) is True


def test_ichimoku_kijun_cross_and_strength() -> None:
    """Verify Ichimoku Kijun-sen crosses and signal_strength cloud filters."""
    high = np.linspace(100.0, 130.0, 60)
    low = high - 2.0
    close = high - 0.5
    ichi = Ichimoku.calculate(high, low, close, tenkan=9, kijun=26, senkou=52)
    assert set(ichi.keys()) == {
        "tenkan_sen",
        "kijun_sen",
        "senkou_span_a",
        "senkou_span_b",
        "chikou_span",
    }

    o = IndicatorSeries([98.0, 99.0])
    c = IndicatorSeries([100.0, 105.0])
    ks = IndicatorSeries([100.0, 102.0])
    sa = IndicatorSeries([95.0, 96.0])
    sb = IndicatorSeries([90.0, 92.0])

    assert (
        Ichimoku.kijun_sen_cross_bullish(o, c, ks, sa, sb, signal_strength=2, shift=0)
        is True
    )
    assert (
        Ichimoku.kijun_sen_cross_bearish(
            c, o, ks, IndicatorSeries([110.0, 110.0]), sb, signal_strength=1, shift=0
        )
        is True
    )
    assert (
        Ichimoku.tenkan_kijun_cross_bullish(
            IndicatorSeries([100.0, 105.0]),
            IndicatorSeries([101.0, 102.0]),
            senkou_span_a=sa,
            senkou_span_b=sb,
            signal_strength=2,
        )
        is True
    )
    assert (
        Ichimoku.senkou_span_cross_bullish(
            IndicatorSeries([90.0, 98.0]),
            IndicatorSeries([95.0, 94.0]),
            close_prices=c,
            signal_strength=2,
        )
        is True
    )
    assert (
        Ichimoku.tenkan_kijun_cross_bearish(
            IndicatorSeries([105.0, 100.0]),
            IndicatorSeries([102.0, 101.0]),
            senkou_span_a=IndicatorSeries([110.0, 110.0]),
            senkou_span_b=IndicatorSeries([108.0, 108.0]),
            signal_strength=2,
        )
        is True
    )
    assert (
        Ichimoku.senkou_span_cross_bearish(
            IndicatorSeries([98.0, 90.0]),
            IndicatorSeries([94.0, 95.0]),
            close_prices=IndicatorSeries([90.0, 85.0]),
            signal_strength=2,
        )
        is True
    )
    assert (
        Ichimoku.kumo_breakout_bullish(IndicatorSeries([94.0, 100.0]), sa, sb, shift=0)
        is True
    )
    assert (
        Ichimoku.kumo_breakout_bullish(
            IndicatorSeries([94.0, 100.0]),
            sa,
            sb,
            open_prices=IndicatorSeries([90.0, 94.0]),
        )
        is True
    )
    assert (
        Ichimoku.kumo_breakout_bearish(IndicatorSeries([93.0, 88.0]), sa, sb, shift=0)
        is True
    )
    assert (
        Ichimoku.kumo_breakout_bearish(
            IndicatorSeries([93.0, 88.0]),
            sa,
            sb,
            open_prices=IndicatorSeries([95.0, 95.0]),
        )
        is True
    )
    assert (
        Ichimoku.kijun_sen_cross_bullish(o, c, ks, sa, sb, signal_strength=1, shift=0)
        is True
    )
    assert Ichimoku.kijun_sen_cross_bullish(c, o, ks, shift=0) is False
    assert Ichimoku.kijun_sen_cross_bearish(o, c, ks, shift=0) is False
    assert Ichimoku.tenkan_kijun_cross_bullish(ks, ks) is False
    assert Ichimoku.tenkan_kijun_cross_bearish(ks, ks) is False
    assert Ichimoku.senkou_span_cross_bullish(sa, sa) is False
    assert Ichimoku.senkou_span_cross_bearish(sa, sa) is False
    with pytest.raises(ValueError, match="All lookback periods"):
        Ichimoku.calculate(high, low, close, tenkan=0)
    with pytest.raises(ValueError, match="empty"):
        Ichimoku.calculate(np.array([]), np.array([]), np.array([]))
    with pytest.raises(ValueError, match="lengths must match"):
        Ichimoku.calculate(high, low[:5], close)


def test_keltner_channel_bar_opens_and_closes() -> None:
    """Verify KeltnerChannel calculation and all 8 bar_opens_* condition methods."""
    high = np.linspace(10.0, 15.0, 25)
    low = high - 1.0
    close = high - 0.3
    kc = KeltnerChannel.calculate(high, low, close, period=5, deviation=1.5)
    assert set(kc.keys()) == {"upper", "middle", "lower"}

    kc_mock = {
        "upper": IndicatorSeries([11.0, 12.0, 13.0]),
        "middle": IndicatorSeries([10.0, 10.5, 11.0]),
        "lower": IndicatorSeries([9.0, 8.5, 8.0]),
    }
    assert KeltnerChannel.bar_closes_above_upper([10.0, 11.0, 14.0], kc_mock) is True
    assert KeltnerChannel.bar_closes_below_upper([10.0, 11.0, 12.0], kc_mock) is True
    assert KeltnerChannel.bar_closes_above_lower([10.0, 11.0, 9.0], kc_mock) is True
    assert KeltnerChannel.bar_closes_below_lower([10.0, 11.0, 7.0], kc_mock) is True
    assert KeltnerChannel.bar_opens_above_upper([10.0, 11.5, 12.5], kc_mock) is True
    assert KeltnerChannel.bar_opens_below_upper([10.0, 11.5, 11.5], kc_mock) is True
    assert KeltnerChannel.bar_opens_above_lower([10.0, 8.0, 9.0], kc_mock) is True
    assert KeltnerChannel.bar_opens_below_lower([10.0, 9.0, 8.0], kc_mock) is True
    assert (
        KeltnerChannel.bar_opens_above_upper_after_open_below(
            [10.0, 11.5, 12.5], kc_mock
        )
        is True
    )
    assert (
        KeltnerChannel.bar_opens_below_upper_after_open_above(
            [10.0, 12.5, 11.5], kc_mock
        )
        is True
    )
    assert (
        KeltnerChannel.bar_opens_above_lower_after_open_below([10.0, 8.0, 9.0], kc_mock)
        is True
    )
    assert (
        KeltnerChannel.bar_opens_below_lower_after_open_above([10.0, 9.0, 8.0], kc_mock)
        is True
    )
    assert KeltnerChannel.upper_is_rising(kc_mock) is True
    assert KeltnerChannel.upper_is_falling(kc_mock) is False
    assert KeltnerChannel.lower_is_falling(kc_mock) is True
    assert KeltnerChannel.lower_is_rising(kc_mock) is False


def test_macd_all_18_conditions() -> None:
    """Verify MACD calculation and all 18 condition helpers."""
    close = np.linspace(10.0, 30.0, 40)
    res = MACD.calculate(close, fast=5, slow=10, smooth=3)
    assert set(res.keys()) == {"main", "signal", "histogram"}

    d = {
        "main": IndicatorSeries([-0.5, -1.0, 0.5]),
        "signal": IndicatorSeries([-0.2, -0.5, 0.1]),
        "histogram": IndicatorSeries([-0.3, -0.5, 0.4]),
    }
    assert MACD.main_crosses_above_signal(d) is True
    assert MACD.main_crosses_below_signal(d) is False
    assert MACD.main_higher_signal(d) is True
    assert MACD.main_lower_signal(d, shift=1) is True
    assert MACD.main_crosses_above_zero(d) is True
    assert MACD.main_crosses_below_zero(d) is False
    assert MACD.main_changes_up(d) is True
    assert MACD.main_changes_down(d) is False
    assert MACD.main_crosses_above(d, 0.2) is True
    assert MACD.main_crosses_below(d, -0.8, shift=1) is True
    assert MACD.main_is_rising(d) is True
    assert MACD.main_is_falling(d, shift=1) is True
    assert MACD.main_is_higher(d, 0.2) is True
    assert MACD.main_is_lower(d, 0.0, shift=1) is True
    assert MACD.main_higher_zero(d) is True
    assert MACD.main_lower_zero(d, shift=1) is True
    assert MACD.signal_is_rising(d) is True
    assert MACD.signal_is_falling(d, shift=1) is True


def test_moving_average_tema_and_bar_conditions() -> None:
    """Verify MovingAverage TEMA and all 6 bar open/close vs. MA helpers."""
    data = np.linspace(10.0, 25.0, 20)
    for m in (
        MovingAverage.SMA,
        MovingAverage.EMA,
        MovingAverage.SMMA,
        MovingAverage.LWMA,
        MovingAverage.TEMA,
    ):
        s = MovingAverage.calculate(data, period=4, method=m)
        assert not np.isnan(s.get(0))

    ma = IndicatorSeries([10.0, 11.0, 12.0])
    assert MovingAverage.is_rising(ma) is True
    assert MovingAverage.is_falling(ma) is False
    assert MovingAverage.crosses_above(ma, 11.5) is True
    assert MovingAverage.crosses_below(ma, 11.5) is False
    assert MovingAverage.is_greater(ma, 11.5) is True
    assert MovingAverage.is_lower(ma, 12.5) is True
    assert MovingAverage.bar_closes_above([10.0, 11.0, 12.5], ma) is True
    assert MovingAverage.bar_closes_below([10.0, 11.0, 11.5], ma) is True
    assert MovingAverage.bar_opens_above([10.0, 10.5, 11.5], ma) is True
    assert MovingAverage.bar_opens_below([10.0, 11.5, 10.5], ma) is True
    assert (
        MovingAverage.bar_opens_above_after_open_below([10.0, 10.5, 11.5], ma) is True
    )
    assert (
        MovingAverage.bar_opens_below_after_open_above([10.0, 11.5, 10.5], ma) is True
    )


def test_qqe_all_14_conditions() -> None:
    """Verify QQE calculation and all 14 condition helpers."""
    close = np.linspace(100.0, 120.0, 30) + np.sin(np.arange(30))
    res = QQE.calculate(close, rsi_period=5, sf=3, wf=4.236)
    assert "value1" in res and "value2" in res

    v1 = IndicatorSeries([50.0, 45.0, 55.0])
    v2 = IndicatorSeries([48.0, 48.0, 50.0])
    assert QQE.value1_crosses_above_value2(v1, v2) is True
    assert QQE.value1_crosses_below_value2(v1, v2, shift=1) is True
    assert QQE.value1_higher_value2(v1, v2) is True
    assert QQE.value1_lower_value2(v1, v2, shift=1) is True
    assert QQE.value1_is_rising(v1) is True
    assert QQE.value1_is_falling(v1, shift=1) is True
    assert QQE.value1_changes_up(v1) is True
    assert QQE.value1_changes_down(IndicatorSeries([45.0, 55.0, 50.0])) is True
    assert QQE.value1_crosses_above(v1, 50.0) is True
    assert QQE.value1_crosses_below(v1, 48.0, shift=1) is True
    assert QQE.value1_is_higher(v1, 52.0) is True
    assert QQE.value1_is_lower(v1, 48.0, shift=1) is True
    assert QQE.value2_is_rising(v2) is True
    assert QQE.value2_is_falling(IndicatorSeries([52.0, 50.0])) is True


def test_stochastic_all_12_conditions() -> None:
    """Verify Stochastic calculation and all 12 FastK and SlowD condition helpers."""
    high = np.linspace(10.0, 20.0, 25)
    low = high - 1.5
    close = high - 0.3
    st = Stochastic.calculate(high, low, close, k_period=5, d_period=3, slowing=3)
    assert "k" in st and "d" in st

    mock = {
        "k": IndicatorSeries([40.0, 30.0, 60.0]),
        "d": IndicatorSeries([45.0, 35.0, 50.0]),
    }
    assert Stochastic.k_crosses_above_d(mock) is True
    assert Stochastic.k_crosses_below_d(mock) is False
    assert Stochastic.k_higher_d(mock) is True
    assert Stochastic.k_lower_d(mock, shift=1) is True
    assert Stochastic.k_crosses_above(mock, 50.0) is True
    assert Stochastic.k_crosses_below(mock, 35.0, shift=1) is True
    assert Stochastic.d_changes_up(mock) is True
    assert Stochastic.d_changes_down(mock) is False
    assert Stochastic.d_crosses_above(mock, 40.0) is True
    assert Stochastic.d_crosses_below(mock, 40.0, shift=1) is True
    assert Stochastic.d_is_rising(mock) is True
    assert Stochastic.d_is_falling(mock, shift=1) is True
    assert Stochastic.d_is_higher(mock, 45.0) is True
    assert Stochastic.d_is_lower(mock, 40.0, shift=1) is True


def test_wave_trend_all_18_conditions() -> None:
    """Verify WaveTrend calculation and all 18 WT1/WT2 condition helpers."""
    high = np.linspace(50.0, 70.0, 30)
    low = high - 1.5
    close = high - 0.4
    wt = WaveTrend.calculate(
        high, low, close, channel_length=5, average_length=7, signal_length=3
    )
    assert "wt1" in wt and "wt2" in wt

    w1 = IndicatorSeries([5.0, -5.0, 10.0])
    w2 = IndicatorSeries([2.0, 0.0, 4.0])
    assert WaveTrend.wt1_crosses_above_wt2(w1, w2) is True
    assert WaveTrend.wt1_crosses_below_wt2(w1, w2, shift=1) is True
    assert WaveTrend.wt1_crosses_above_zero(w1) is True
    assert WaveTrend.wt1_crosses_below_zero(w1, shift=1) is True
    assert WaveTrend.wt1_is_rising(w1) is True
    assert WaveTrend.wt1_is_falling(w1, shift=1) is True
    assert WaveTrend.wt1_changes_up(w1) is True
    assert WaveTrend.wt1_changes_down(IndicatorSeries([-5.0, 10.0, 2.0])) is True
    assert WaveTrend.wt1_crosses_above(w1, 5.0) is True
    assert WaveTrend.wt1_crosses_below(w1, 0.0, shift=1) is True
    assert WaveTrend.wt1_is_higher(w1, 5.0) is True
    assert WaveTrend.wt1_is_lower(w1, 0.0, shift=1) is True
    assert WaveTrend.wt1_higher_wt2(w1, w2) is True
    assert WaveTrend.wt1_lower_wt2(w1, w2, shift=1) is True
    assert WaveTrend.wt1_higher_zero(w1) is True
    assert WaveTrend.wt1_lower_zero(w1, shift=1) is True
    assert WaveTrend.wt2_is_rising(w2) is True
    assert WaveTrend.wt2_is_falling(w2, shift=1) is True


def test_cot_calculate_and_all_conditions() -> None:
    """Verify COT calculation, value helpers, and all specialized COT conditions."""
    comm = np.linspace(-100.0, 100.0, 30)
    spec = -comm
    small = np.linspace(20.0, -20.0, 30)
    oi = np.full(30, 500.0)
    res = COT.calculate(
        comm,
        spec,
        small_spec_net=small,
        open_interest=oi,
        period_fast=5,
        period_slow=10,
    )
    assert "composite_score" in res and "cpi_small" in res and "cti_hedger" in res

    h52 = IndicatorSeries([0.60, 0.70, 0.80, 0.85, 0.90])
    s52 = IndicatorSeries([0.40, 0.30, 0.20, 0.15, 0.10])
    h156 = IndicatorSeries([0.50, 0.55, 0.60, 0.65, 0.72])
    s156 = IndicatorSeries([0.50, 0.45, 0.40, 0.35, 0.28])
    sm52 = IndicatorSeries([0.50, 0.40, 0.30, 0.20, 0.15])
    score = IndicatorSeries([-0.30, -0.20, -0.05, 0.25, 0.70])

    assert COT.field_value(h52) == pytest.approx(0.90)
    assert COT.cross_field_spread(h52, s52) == pytest.approx(0.80)
    assert COT.momentum(h52, lookback=2) == pytest.approx(0.10)
    assert COT.multi_field_combo(h52, s52, sm52, s156) > 0.70

    assert COT.is_bullish_extreme(score, 0.60) is True
    assert COT.is_bearish_extreme(score, -0.20, shift=4) is True
    assert COT.is_bullish_regime(score) is True
    assert COT.is_bearish_regime(score, shift=3) is True
    assert COT.score_crosses_above_zero(score, shift=1) is True
    assert COT.score_crosses_below_zero(IndicatorSeries([0.2, -0.1])) is True
    assert COT.is_rising(score) is True
    assert COT.is_falling(IndicatorSeries([0.5, 0.2])) is True
    assert COT.changes_up(IndicatorSeries([0.5, 0.2, 0.6])) is True
    assert COT.changes_down(IndicatorSeries([0.2, 0.6, 0.3])) is True
    assert COT.crosses_above(score, 0.5) is True
    assert COT.crosses_below(IndicatorSeries([0.6, 0.3]), 0.5) is True
    assert COT.is_higher(score, 0.5) is True
    assert COT.is_lower(score, 0.8) is True

    assert COT.shift_52_vs_156_bullish(h52, s52, h156, s156, 0.10) is True
    assert COT.shift_52_vs_156_bearish(s52, h52, s156, h156, 0.10) is True
    assert COT.accumulation_bullish(h52, s52, min_weeks=3) is True
    assert COT.accumulation_bearish(s52, h52, min_weeks=3) is True
    assert COT.extreme_bullish(h52, s52, 0.80, 0.20, hedg156=h156, spec156=s156) is True
    assert COT.extreme_bearish(s52, h52, 0.20, 0.80, hedg156=s156, spec156=h156) is True
    assert (
        COT.convergence(IndicatorSeries([0.50]), IndicatorSeries([0.55]), 0.10) is True
    )
    assert (
        COT.crowding_unwind(
            IndicatorSeries([0.20, 0.20]),
            IndicatorSeries([0.90, 0.80]),
            direction=1,
            spec_extreme=0.85,
            hedger_opposing=0.30,
        )
        is True
    )
    assert (
        COT.extreme_exit_bullish(
            IndicatorSeries([0.90, 0.65]), extreme_threshold=0.85, exit_threshold=0.70
        )
        is True
    )
    assert (
        COT.extreme_exit_bearish(
            IndicatorSeries([0.90, 0.65]), extreme_threshold=0.85, exit_threshold=0.70
        )
        is True
    )
    assert COT.extreme_persistence(h52, extreme_threshold=0.75, min_weeks=3) is True
    assert (
        COT.extreme_unwind_bullish(
            IndicatorSeries([0.90, 0.80, 0.70]),
            crowded_threshold=0.85,
            normalize_threshold=0.75,
        )
        is True
    )
    assert (
        COT.extreme_unwind_bearish(
            IndicatorSeries([0.90, 0.80, 0.70]),
            crowded_threshold=0.85,
            normalize_threshold=0.75,
        )
        is True
    )
    assert COT.full_cycle_long(h52, entry_level=0.88) is True
    assert COT.full_cycle_short(s52, entry_level=0.12) is True
    assert COT.full_cycle_exit_long(h52, exit_level=0.50) is True
    assert COT.full_cycle_exit_short(s52, exit_level=0.50) is True
    assert COT.hedger_accel_bullish(h52, s52, h156, s156, 0.10) is True
    assert COT.hedger_accel_bearish(s52, h52, s156, h156, 0.10) is True
    assert COT.hedger_div_conf_bullish(h52, s52, 0.75, 0.25, mom_lookback=2) is True
    assert COT.hedger_div_conf_bearish(s52, h52, 0.25, 0.75, mom_lookback=2) is True
    assert COT.higher_low(score, short_window=2, long_window=5) is True
    assert (
        COT.lower_high(
            IndicatorSeries([0.4, 0.3, 0.2, 0.1, 0.05]), short_window=2, long_window=5
        )
        is True
    )
    assert (
        COT.momentum_rev_bullish(
            IndicatorSeries([0.5, 0.2, 0.0, 0.1, 0.3]), mom_period=2
        )
        is True
    )
    assert (
        COT.momentum_rev_bearish(
            IndicatorSeries([-0.5, -0.2, 0.1, 0.0, -0.3]), mom_period=2
        )
        is True
    )
    assert COT.multi_window_bullish(h52, s52, h156, s156) is True
    assert COT.multi_window_bearish(s52, h52, s156, h156) is True
    assert COT.neutral_zone(score, neutral_band=0.10, shift=2) is True
    assert (
        COT.regime_shift_bullish(
            IndicatorSeries([-0.2, -0.1, 0.0, 0.1, 0.3, 0.5]), shift_weeks=2
        )
        is True
    )
    assert (
        COT.regime_shift_bearish(
            IndicatorSeries([0.2, 0.1, 0.0, -0.1, -0.3, -0.5]), shift_weeks=2
        )
        is True
    )
    assert COT.roc_bullish(score, roc_period=2, roc_threshold=0.20) is True
    assert (
        COT.roc_bearish(
            IndicatorSeries([0.5, 0.2, -0.3]), roc_period=2, roc_threshold=0.20
        )
        is True
    )
    assert COT.score_above(score, 0.5) is True
    assert COT.score_below(score, 0.0, shift=3) is True
    assert COT.score_accel_bullish(score, mom_period=2, momentum_threshold=0.10) is True
    assert (
        COT.score_accel_bearish(
            IndicatorSeries([0.5, 0.4, 0.3, 0.1, -0.4]),
            mom_period=2,
            momentum_threshold=-0.10,
        )
        is True
    )
    assert COT.score_momentum_above(score, momentum_lookback=2) is True
    assert (
        COT.score_momentum_below(IndicatorSeries([0.3, 0.0, -0.4]), momentum_lookback=2)
        is True
    )
    assert (
        COT.seasonal_bullish(h52, seasonal_lookback=3, seasonal_threshold=0.05) is True
    )
    assert (
        COT.seasonal_bearish(s52, seasonal_lookback=3, seasonal_threshold=0.05) is True
    )
    assert COT.small_fade_bullish(sm52, 0.20) is True
    assert COT.small_fade_bearish(sm52, 0.40, shift=4) is True
    assert COT.smart_dumb_bullish(h52, sm52) is True
    assert COT.smart_dumb_bearish(s52, h52) is True
    assert (
        COT.spec_exhaustion_long(
            IndicatorSeries([0.80, 0.85]),
            IndicatorSeries([0.05, 0.15]),
            spec_extreme=0.90,
            hedger_threshold=0.70,
            lookback_weeks=1,
        )
        is True
    )
    assert (
        COT.spec_exhaustion_short(
            IndicatorSeries([0.20, 0.15]),
            IndicatorSeries([0.95, 0.85]),
            spec_extreme=0.90,
            hedger_threshold=0.30,
            lookback_weeks=1,
        )
        is True
    )
    assert (
        COT.spec_trend_long(
            IndicatorSeries([0.40, 0.50, 0.65]),
            IndicatorSeries([0.55, 0.55, 0.60]),
            lookback=2,
        )
        is True
    )
    assert (
        COT.spec_trend_short(
            IndicatorSeries([0.60, 0.50, 0.35]),
            IndicatorSeries([0.45, 0.45, 0.40]),
            lookback=2,
        )
        is True
    )
    assert COT.spread_zscore_bullish(h52, s52, period=4, z_threshold=1.0) is True
    assert COT.spread_zscore_bearish(s52, h52, period=4, z_threshold=1.0) is True
    assert COT.triple_div_bullish(h52, s52, sm52) is True
    assert COT.triple_div_bearish(s52, h52, h52) is True
    assert COT.vix_proxy_bullish(h52, s52) is True
    assert COT.vix_proxy_bearish(s52, h52) is True


def test_volume_profile_custom_hours_and_all_36_conditions() -> None:
    """Verify VolumeProfile calculation, custom-hour sessions, and all 36 VP* conditions."""
    base_sec = 1700006400
    ts = [base_sec + i * 3600 for i in range(15)]
    high = np.linspace(100.0, 114.0, 15)
    low = high - 2.0
    open_p = high - 1.2
    close = high - 0.4
    vol = np.linspace(100.0, 500.0, 15)

    vp = VolumeProfile.calculate(
        high, low, close, vol, open_prices=open_p, period=5, profile_rows=10
    )
    assert {"poc", "vah", "val", "bull_poc", "bear_poc", "delta", "ibh", "ibl"} <= set(
        vp.keys()
    )
    vp_ch = VolumeProfile.calculate_custom_hours(
        ts, high, low, close, vol, start_hhmm=800, end_hhmm=1600, period=5
    )
    vp_ms = VolumeProfile.calculate_custom_hours_multi_session(
        ts, high, low, close, vol, sessions=((800, 1200), (1300, 1700)), period=5
    )
    assert not np.isnan(vp_ch["poc"].get(0))
    assert not np.isnan(vp_ms["poc"].get(0))

    poc = IndicatorSeries([100.0, 101.0, 102.0, 104.0])
    vah = IndicatorSeries([102.0, 103.0, 104.0, 106.0])
    val = IndicatorSeries([98.0, 99.0, 100.0, 103.5])
    c_in = IndicatorSeries([97.0, 97.5, 98.0, 104.5])

    assert VolumeProfile.price_above_poc(c_in, poc) is True
    assert VolumeProfile.price_below_poc(IndicatorSeries([103.0]), poc) is True
    assert VolumeProfile.price_inside_va(c_in, vah, val) is True
    assert VolumeProfile.price_outside_va(c_in, vah, val, shift=1) is True
    assert VolumeProfile.poc_is_rising(poc) is True
    assert VolumeProfile.poc_is_falling(poc) is False
    assert VolumeProfile.vah_is_rising(vah) is True
    assert VolumeProfile.vah_is_falling(vah) is False
    assert VolumeProfile.val_is_rising(val) is True
    assert VolumeProfile.val_is_falling(val) is False
    assert VolumeProfile.is_narrow_value_area(vah, val, threshold=5.0) is True
    assert VolumeProfile.is_wide_value_area(vah, val, threshold=2.0) is True
    assert (
        VolumeProfile.bull_above_bear(
            IndicatorSeries([105.0]), IndicatorSeries([102.0])
        )
        is True
    )
    assert (
        VolumeProfile.bear_above_bull(
            IndicatorSeries([102.0]), IndicatorSeries([105.0])
        )
        is True
    )
    assert VolumeProfile.bottom_heavy_poc(IndicatorSeries([20.0]), 35.0) is True
    assert VolumeProfile.top_heavy_poc(IndicatorSeries([20.0]), 35.0) is True
    assert VolumeProfile.high_delta(IndicatorSeries([250.0]), 100.0) is True
    assert VolumeProfile.high_neg_delta(IndicatorSeries([-250.0]), 100.0) is True
    assert (
        VolumeProfile.ib_breakout_up(IndicatorSeries([108.0]), IndicatorSeries([105.0]))
        is True
    )
    assert (
        VolumeProfile.ib_breakout_down(IndicatorSeries([95.0]), IndicatorSeries([98.0]))
        is True
    )
    assert (
        VolumeProfile.ib_rejection_long(
            IndicatorSeries([97.0]),
            IndicatorSeries([99.0]),
            IndicatorSeries([98.0]),
        )
        is True
    )
    assert (
        VolumeProfile.ib_rejection_short(
            IndicatorSeries([106.0]),
            IndicatorSeries([104.0]),
            IndicatorSeries([105.0]),
        )
        is True
    )
    assert (
        VolumeProfile.excess_reversal_long(
            IndicatorSeries([104.0]),
            IndicatorSeries([105.0]),
            IndicatorSeries([101.0]),
            IndicatorSeries([104.2]),
            vah,
            val,
        )
        is True
    )
    assert (
        VolumeProfile.excess_reversal_short(
            IndicatorSeries([105.0]),
            IndicatorSeries([109.0]),
            IndicatorSeries([104.0]),
            IndicatorSeries([104.8]),
            vah,
            val,
        )
        is True
    )
    assert VolumeProfile.rising_poc(poc, lookback_bars=2, min_shift=1.0) is True
    assert (
        VolumeProfile.falling_poc(
            IndicatorSeries([105.0, 103.0, 100.0]), lookback_bars=2, min_shift=1.0
        )
        is True
    )
    assert VolumeProfile.late_acceptance_failure_long(c_in, vah, val) is True
    assert (
        VolumeProfile.late_acceptance_failure_short(
            IndicatorSeries([105.0, 105.0, 105.0, 104.5]), vah, val
        )
        is True
    )
    assert (
        VolumeProfile.open_drive_long(
            IndicatorSeries([100.0, 101.0, 102.0]),
            IndicatorSeries([101.0, 102.0, 104.0]),
            min_move=2.0,
        )
        is True
    )
    assert (
        VolumeProfile.open_drive_short(
            IndicatorSeries([104.0, 103.0, 102.0]),
            IndicatorSeries([103.0, 102.0, 100.0]),
            min_move=2.0,
        )
        is True
    )
    assert (
        VolumeProfile.poc_at_edge_long(
            IndicatorSeries([105.8]), vah, val, edge_pct=20.0
        )
        is True
    )
    assert (
        VolumeProfile.poc_at_edge_short(
            IndicatorSeries([103.7]), vah, val, edge_pct=20.0
        )
        is True
    )
    assert (
        VolumeProfile.poc_magnet_long(
            IndicatorSeries([103.6]), poc, vah, val, min_deviation=0.1
        )
        is True
    )
    assert (
        VolumeProfile.poc_magnet_short(
            IndicatorSeries([105.5]), poc, vah, val, min_deviation=0.1
        )
        is True
    )
    assert (
        VolumeProfile.vah_test_rejection(
            IndicatorSeries([107.0]), IndicatorSeries([105.0]), vah
        )
        is True
    )
    assert (
        VolumeProfile.val_test_rejection(
            IndicatorSeries([102.0]), IndicatorSeries([104.5]), val
        )
        is True
    )
    assert VolumeProfile.value_return_long(c_in, vah, val) is True
    assert (
        VolumeProfile.value_return_short(
            IndicatorSeries([100.0, 100.0, 105.0, 104.5]), vah, val
        )
        is True
    )
    assert VolumeProfile.value_shift_up(vah, val, lookback_bars=2) is True
    assert (
        VolumeProfile.value_shift_down(
            IndicatorSeries([105.0, 104.0, 97.0]),
            IndicatorSeries([100.0, 99.0, 95.0]),
            lookback_bars=2,
        )
        is True
    )
    assert (
        VolumeProfile.vwap_cross_up(
            IndicatorSeries([99.0, 102.0]), IndicatorSeries([100.0, 100.0])
        )
        is True
    )
    assert (
        VolumeProfile.vwap_cross_down(
            IndicatorSeries([102.0, 99.0]), IndicatorSeries([100.0, 100.0])
        )
        is True
    )
