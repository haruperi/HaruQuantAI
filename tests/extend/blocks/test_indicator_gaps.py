"""Unit tests for all indicator block families, condition helpers, and logging.

Description:
    Validates calculations, condition compositions, parameter spaces,
    and non-silent requirement logging across StrategyQuant-faithful indicator blocks.
Purpose:
    FEAT-INDICATORS-BLOCKS: Test suite for indicator building blocks.
Key Capabilities:
    - FR-indicator-gaps-tests: Comprehensive verification across 13 indicator families.
    - FR-indicator-logging-tests: Verify non-silent requirement diagnostics under caplog.
Python API Usage:
    pytest tests/extend/blocks/test_indicator_gaps.py --no-cov
CLI Usage:
    uv run pytest tests/extend/blocks/test_indicator_gaps.py --no-cov
"""

from __future__ import annotations

import app.extend.blocks.indicators.volume.cot as cot_signals
import numpy as np
import pytest
from app.core.trading.blocks.series import BarData, IndicatorSeries
from app.extend.blocks.comparisons.changes_down import changes_down
from app.extend.blocks.comparisons.changes_up import changes_up
from app.extend.blocks.comparisons.crosses_above import crosses_above
from app.extend.blocks.comparisons.crosses_below import crosses_below
from app.extend.blocks.comparisons.is_falling import is_falling
from app.extend.blocks.comparisons.is_greater import is_greater
from app.extend.blocks.comparisons.is_greater_count import is_greater_count
from app.extend.blocks.comparisons.is_lower import is_lower
from app.extend.blocks.comparisons.is_lower_count import is_lower_count
from app.extend.blocks.comparisons.is_rising import is_rising
from app.extend.blocks.indicators import (
    EMA,
    LWMA,
    MACD,
    SMA,
    SMMA,
    TEMA,
    BollingerBands,
)
from app.extend.blocks.indicators.momentum.cci import CCI
from app.extend.blocks.indicators.momentum.qqe import QQE
from app.extend.blocks.indicators.momentum.stochastic import Stochastic
from app.extend.blocks.indicators.momentum.wave_trend import WaveTrend
from app.extend.blocks.indicators.trend.adx import ADX
from app.extend.blocks.indicators.trend.ichimoku import Ichimoku
from app.extend.blocks.indicators.volatility.bar_range import BarRange
from app.extend.blocks.indicators.volatility.highest_in_range import HighestInRange
from app.extend.blocks.indicators.volatility.keltner_channel import KeltnerChannel
from app.extend.blocks.indicators.volatility.lowest_in_range import LowestInRange
from app.extend.blocks.indicators.volume.cot import COT
from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
from app.extend.blocks.price import BarPrice


def test_adx_calculate_and_all_conditions() -> None:
    """Verify ADX calculation and all 8 Main + 5 DI/trend condition helpers."""
    high = np.linspace(10.0, 25.0, 30)
    low = high - 1.5
    close = high - 0.3
    adx_dict = ADX(period=5).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
    )
    assert "main" in adx_dict and "di_plus" in adx_dict and ("di_minus" in adx_dict)
    short_adx = ADX(period=14).calculate(
        BarData.from_arrays(high=[1.0, 2.0], low=[0.5, 1.0], close=[0.8, 1.5])
    )
    assert np.isnan(short_adx["main"].get(0))
    with pytest.raises(ValueError):
        ADX(period=0)
    s = IndicatorSeries([15.0, 12.0, 18.0, 22.0])
    d = {
        "main": s,
        "di_plus": IndicatorSeries([10.0, 20.0]),
        "di_minus": IndicatorSeries([15.0, 12.0]),
    }
    assert is_rising(d["main"], shift=0) is True
    assert is_falling(d["main"], shift=2) is True
    assert is_greater(d["main"], 20.0, shift=0) is True
    assert is_lower(d["main"], 20.0, shift=1) is True
    assert crosses_above(d["main"], 20.0, shift=0) is True
    assert crosses_below(d["main"], 14.0, shift=2) is True
    assert changes_up(d["main"], shift=1) is True
    assert changes_down(IndicatorSeries([10.0, 20.0, 15.0]), shift=0) is True
    assert crosses_above(d["di_plus"], d["di_minus"], shift=0, round_digits=8) is True
    assert crosses_below(d["di_plus"], d["di_minus"], shift=0, round_digits=8) is False
    assert (
        is_greater(d["di_plus"], d["di_minus"], shift1=0, shift2=0, round_digits=8)
        is True
    )
    assert (
        is_lower(d["di_plus"], d["di_minus"], shift1=0, shift2=0, round_digits=8)
        is False
    )
    assert is_greater(d["main"], 20.0, shift1=0, round_digits=8) is True


def test_bar_range_time_windows_and_conditions() -> None:
    """Verify BarRange time-window extrema, fixed_pips, and range conditions."""
    high = np.array([10.0, 12.0, 11.5, 14.0, 13.0, 12.5])
    low = np.array([9.0, 10.5, 10.8, 11.0, 12.0, 11.0])
    rng = BarRange().calculate(BarData.from_arrays(high=high, low=low))["value"]
    assert len(rng) == 6
    assert BarRange.fixed_pips(50, 0.0001) == pytest.approx(0.005)
    assert BarRange.is_biggest_range(rng, period=3, shift=2) is True
    assert BarRange.is_smallest_range(rng, period=3, shift=3) is True
    assert is_greater(rng, rng, shift1=2, shift2=2 + 1) is True
    assert is_lower(rng, rng, shift1=1, shift2=1 + 1) is True
    assert BarRange.in_range_pips(rng, 50.0, 50000.0, pip_size=0.01, shift=0) is True
    assert is_rising(rng, shift=0) is True
    assert is_falling(rng, shift=1) is True
    assert is_greater(rng, 1.0, shift=0) is True
    assert is_lower(rng, 2.0, shift=0) is True
    base_sec = 1700006400
    ts = [base_sec + h * 3600 for h in (8, 9, 10, 11, 12, 13)]
    hi_rng = HighestInRange(time_from=900, time_to=1100).calculate(
        BarData.from_arrays(timestamps=ts, high=high)
    )["value"]
    lo_rng = LowestInRange(time_from=900, time_to=1100).calculate(
        BarData.from_arrays(timestamps=ts, low=low)
    )["value"]
    assert hi_rng.get(0) == pytest.approx(12.0)
    assert lo_rng.get(0) == pytest.approx(10.5)
    with pytest.raises(ValueError, match="cannot be empty"):
        BarData.from_arrays(timestamps=[], high=[])


def test_bollinger_bands_value_and_bar_conditions() -> None:
    """Verify BollingerBands range, width ratio, slopes, and 12 bar open/close checks."""
    close = np.array([10.0, 10.2, 10.5, 10.3, 10.8, 11.5, 12.2])
    bp = BarPrice(
        open_data=close,
        high_data=close,
        low_data=close,
        close_data=close,
        volume_data=np.ones_like(close),
    )
    bars = BarData(prices=bp)
    bb = BollingerBands(period=3, deviation=2.0).calculate(bars)
    assert "range" in bb
    assert "bandwidth" in bb
    assert len(bb["range"].values) == len(close)
    assert len(bb["bandwidth"].values) == len(close)
    bands = {
        "upper": IndicatorSeries([11.0, 12.0, 13.0]),
        "middle": IndicatorSeries([10.0, 10.5, 11.0]),
        "lower": IndicatorSeries([9.0, 8.5, 8.0]),
    }
    c_ser = IndicatorSeries([10.0, 11.5, 13.5])
    o_ser = IndicatorSeries([10.0, 11.5, 12.5])
    assert is_rising(bands["upper"], shift=0) is True
    assert is_falling(bands["upper"], shift=0) is False
    assert is_falling(bands["lower"], shift=0) is True
    assert is_rising(bands["lower"], shift=0) is False
    assert crosses_above(c_ser, bands["upper"], shift=0) is True
    assert is_greater(c_ser, bands["upper"], shift=0) is True
    assert is_greater(c_ser, bands["upper"], shift=0) is True
    assert is_lower(c_ser, bands["upper"], shift=1) is True
    assert is_greater(c_ser, bands["lower"], shift=0) is True
    assert is_lower([7.0, 7.5, 7.0], bands["lower"], shift=0) is True
    assert is_greater(o_ser, bands["upper"], shift1=0, shift2=1, round_digits=8) is True
    assert (
        is_lower([10.0, 11.0, 11.5], bands["upper"], shift1=0, shift2=1, round_digits=8)
        is True
    )
    assert is_greater(o_ser, bands["lower"], shift1=0, shift2=1, round_digits=8) is True
    assert (
        is_lower([9.0, 8.0, 7.5], bands["lower"], shift1=0, shift2=1, round_digits=8)
        is True
    )
    assert (
        is_lower(o_ser, bands["upper"], shift1=1, shift2=1, round_digits=8)
        and is_greater(o_ser, bands["upper"], shift1=0, shift2=1, round_digits=8)
    ) is True
    assert (
        is_greater(
            [10.0, 12.5, 11.5], bands["upper"], shift1=1, shift2=1, round_digits=8
        )
        and is_lower(
            [10.0, 12.5, 11.5], bands["upper"], shift1=0, shift2=1, round_digits=8
        )
    ) is True
    assert (
        is_lower([9.0, 8.0, 9.0], bands["lower"], shift1=1, shift2=1, round_digits=8)
        and is_greater(
            [9.0, 8.0, 9.0], bands["lower"], shift1=0, shift2=1, round_digits=8
        )
    ) is True
    assert (
        is_greater([9.0, 9.0, 8.0], bands["lower"], shift1=1, shift2=1, round_digits=8)
        and is_lower(
            [9.0, 9.0, 8.0], bands["lower"], shift1=0, shift2=1, round_digits=8
        )
    ) is True


def test_cci_and_woodies_patterns() -> None:
    """Verify CCI standard conditions and all 10 Woodies CCI pattern blocks."""
    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0, 14.0, 15.0])
    low = high - 1.0
    close = high - 0.2
    cci = CCI(period=3).calculate(BarData.from_arrays(high=high, low=low, close=close))[
        "value"
    ]
    assert len(cci) == 7
    s_turn = IndicatorSeries([20.0, 10.0, 30.0])
    assert is_rising(s_turn, shift=0) is True
    assert is_falling(s_turn, shift=1) is True
    assert changes_up(s_turn, shift=0) is True
    assert changes_down(IndicatorSeries([10.0, 30.0, 20.0]), shift=0) is True
    assert crosses_above(s_turn, 15.0, shift=0) is True
    assert crosses_below(s_turn, 15.0, shift=1) is True
    assert is_greater(s_turn, s_turn, shift1=0, shift2=0 + 1) is True
    assert is_lower(s_turn, s_turn, shift1=1, shift2=1 + 1) is True
    assert is_greater(s_turn, 25.0, shift=0) is True
    assert is_lower(s_turn, 25.0, shift=1) is True
    assert crosses_above(IndicatorSeries([-5.0, 10.0]), 0.0, shift=0) is True
    assert crosses_below(IndicatorSeries([5.0, -10.0]), 0.0, shift=0) is True
    assert (
        is_greater_count(
            IndicatorSeries([10.0, 20.0, 30.0, 40.0, 50.0, 60.0]), 0.0, bars=6, shift=0
        )
        is True
    )
    assert (
        is_lower_count(
            IndicatorSeries([-10.0, -20.0, -30.0, -40.0, -50.0, -60.0]),
            0.0,
            bars=6,
            shift=0,
        )
        is True
    )
    zlr_up = IndicatorSeries([20.0, 30.0, 40.0, 60.0, 30.0, 55.0])
    assert CCI.woodies_zlr_up(zlr_up, factor=15.0) is True
    zlr_dn = IndicatorSeries([-20.0, -30.0, -40.0, -60.0, -30.0, -55.0])
    assert CCI.woodies_zlr_down(zlr_dn, factor=15.0) is True
    famir_up = IndicatorSeries([-60.0, -50.0, -40.0, -50.0, -20.0, -45.0, -10.0])
    assert CCI.woodies_famir_up(famir_up, factor=15.0) is True
    famir_dn = IndicatorSeries([60.0, 50.0, 40.0, 50.0, 20.0, 45.0, 10.0])
    assert CCI.woodies_famir_down(famir_dn, factor=15.0) is True
    vegas_up = IndicatorSeries([-50.0, -220.0, -90.0, -60.0, -50.0, -80.0, -40.0])
    assert CCI.woodies_vegas_trade_up(vegas_up, factor=15.0) is True
    vegas_dn = IndicatorSeries([50.0, 220.0, 90.0, 60.0, 50.0, 80.0, 40.0])
    assert CCI.woodies_vegas_trade_down(vegas_dn, factor=15.0) is True


def test_ichimoku_kijun_cross_and_strength() -> None:
    """Verify Ichimoku Kijun-sen crosses and signal_strength cloud filters."""
    high = np.linspace(100.0, 130.0, 60)
    low = high - 2.0
    close = high - 0.5
    ichi = Ichimoku(tenkan=9, kijun=26, senkou=52).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
    )
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
    with pytest.raises(ValueError, match="tenkan"):
        Ichimoku(tenkan=0).calculate(
            BarData.from_arrays(high=high, low=low, close=close)
        )
    with pytest.raises(ValueError, match="empty"):
        Ichimoku().calculate(
            BarData.from_arrays(high=np.array([]), low=np.array([]), close=np.array([]))
        )
    with pytest.raises(ValueError, match="aligned series"):
        Ichimoku().calculate(BarData.from_arrays(high=high, low=low[:5], close=close))


def test_keltner_channel_bar_opens_and_closes() -> None:
    """Verify KeltnerChannel calculation and all 8 bar_opens_* condition methods."""
    high = np.linspace(10.0, 15.0, 25)
    low = high - 1.0
    close = high - 0.3
    kc = KeltnerChannel(period=5, deviation=1.5).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
    )
    assert set(kc.keys()) == {"upper", "middle", "lower"}
    kc_mock = {
        "upper": IndicatorSeries([11.0, 12.0, 13.0]),
        "middle": IndicatorSeries([10.0, 10.5, 11.0]),
        "lower": IndicatorSeries([9.0, 8.5, 8.0]),
    }
    assert is_greater([10.0, 11.0, 14.0], kc_mock["upper"], shift=0) is True
    assert is_lower([10.0, 11.0, 12.0], kc_mock["upper"], shift=0) is True
    assert is_greater([10.0, 11.0, 9.0], kc_mock["lower"], shift=0) is True
    assert is_lower([10.0, 11.0, 7.0], kc_mock["lower"], shift=0) is True
    assert (
        is_greater(
            [10.0, 11.5, 12.5], kc_mock["upper"], shift1=0, shift2=0 + 1, round_digits=8
        )
        is True
    )
    assert (
        is_lower(
            [10.0, 11.5, 11.5], kc_mock["upper"], shift1=0, shift2=0 + 1, round_digits=8
        )
        is True
    )
    assert (
        is_greater(
            [10.0, 8.0, 9.0], kc_mock["lower"], shift1=0, shift2=0 + 1, round_digits=8
        )
        is True
    )
    assert (
        is_lower(
            [10.0, 9.0, 8.0], kc_mock["lower"], shift1=0, shift2=0 + 1, round_digits=8
        )
        is True
    )
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
    assert is_rising(kc_mock["upper"], shift=0) is True
    assert is_falling(kc_mock["upper"], shift=0) is False
    assert is_falling(kc_mock["lower"], shift=0) is True
    assert is_rising(kc_mock["lower"], shift=0) is False


def test_macd_all_18_conditions() -> None:
    """Verify MACD calculation and all 18 condition helpers."""
    close = np.linspace(10.0, 30.0, 40)
    bp = BarPrice(
        open_data=close,
        high_data=close,
        low_data=close,
        close_data=close,
        volume_data=np.ones_like(close),
    )
    bars = BarData(prices=bp)
    res = MACD(fast=5, slow=10, smooth=3).calculate(bars)
    assert set(res.keys()) == {"main", "signal", "histogram"}
    d = {
        "main": IndicatorSeries([-0.5, -1.0, 0.5]),
        "signal": IndicatorSeries([-0.2, -0.5, 0.1]),
        "histogram": IndicatorSeries([-0.3, -0.5, 0.4]),
    }
    assert crosses_above(d["main"], d["signal"]) is True
    assert crosses_below(d["main"], d["signal"]) is False
    assert is_greater(d["main"], d["signal"]) is True
    assert is_lower(d["main"], d["signal"], shift=1) is True
    assert crosses_above(d["main"], 0.0) is True
    assert crosses_below(d["main"], 0.0) is False
    assert changes_up(d["main"]) is True
    assert changes_down(d["main"]) is False
    assert crosses_above(d["main"], 0.2) is True
    assert crosses_below(d["main"], -0.8, shift=1) is True
    assert is_rising(d["main"]) is True
    assert is_falling(d["main"], shift=1) is True
    assert is_greater(d["main"], 0.2) is True
    assert is_lower(d["main"], 0.0, shift=1) is True
    assert is_greater(d["main"], 0.0) is True
    assert is_lower(d["main"], 0.0, shift=1) is True
    assert is_rising(d["signal"]) is True
    assert is_falling(d["signal"], shift=1) is True


def test_moving_average_tema_and_bar_conditions() -> None:
    """Verify MovingAverage family (SMA, EMA, SMMA, LWMA, TEMA) and bar open/close conditions."""
    data = np.linspace(10.0, 25.0, 20)
    bp = BarPrice(
        open_data=data,
        high_data=data,
        low_data=data,
        close_data=data,
        volume_data=np.ones_like(data),
    )
    bars = BarData(prices=bp)
    for cls in (SMA, EMA, SMMA, LWMA, TEMA):
        res = cls(period=4).calculate(bars)
        s = res["value"]
        assert not np.isnan(s.get(0))
    ma = IndicatorSeries([10.0, 11.0, 12.0])
    assert is_rising(ma) is True
    assert is_falling(ma) is False
    assert crosses_above(ma, 11.5) is True
    assert crosses_below(ma, 11.5) is False
    assert is_greater(ma, 11.5) is True
    assert is_lower(ma, 12.5) is True
    assert is_greater([10.0, 11.0, 12.5], ma, shift=0) is True
    assert is_lower([10.0, 11.0, 11.5], ma, shift=0) is True
    assert (
        is_greater([10.0, 10.5, 11.5], ma, shift1=0, shift2=1, round_digits=8) is True
    )
    assert is_lower([10.0, 11.5, 10.5], ma, shift1=0, shift2=1, round_digits=8) is True
    assert (
        is_lower([10.0, 10.5, 11.5], ma, shift1=1, shift2=1, round_digits=8)
        and is_greater([10.0, 10.5, 11.5], ma, shift1=0, shift2=1, round_digits=8)
    ) is True
    assert (
        is_greater([10.0, 11.5, 10.5], ma, shift1=1, shift2=1, round_digits=8)
        and is_lower([10.0, 11.5, 10.5], ma, shift1=0, shift2=1, round_digits=8)
    ) is True


def test_qqe_all_14_conditions() -> None:
    """Verify QQE calculation and all 14 condition helpers."""
    close = np.linspace(100.0, 120.0, 30) + np.sin(np.arange(30))
    res = QQE(rsi_period=5, sf=3, wf=4.236).calculate(BarData.from_arrays(price=close))
    assert "value1" in res and "value2" in res
    v1 = IndicatorSeries([50.0, 45.0, 55.0])
    v2 = IndicatorSeries([48.0, 48.0, 50.0])
    assert QQE.value1_crosses_above_value2(v1, v2) is True
    assert QQE.value1_crosses_below_value2(v1, v2, shift=1) is True
    assert QQE.value1_higher_value2(v1, v2) is True
    assert QQE.value1_lower_value2(v1, v2, shift=1) is True
    assert QQE.value1_is_rising(v1) is True
    assert QQE.value1_is_falling(v1, shift=1) is True
    assert changes_up(v1, shift=0) is True
    assert changes_down(IndicatorSeries([45.0, 55.0, 50.0]), shift=0) is True
    assert crosses_above(v1, 50.0, shift=0) is True
    assert crosses_below(v1, 48.0, shift=1) is True
    assert is_greater(v1, 52.0, shift=0) is True
    assert is_lower(v1, 48.0, shift=1) is True
    assert is_rising(v2, shift=0) is True
    assert is_falling(IndicatorSeries([52.0, 50.0]), shift=0) is True


def test_stochastic_all_12_conditions() -> None:
    """Verify Stochastic calculation and all 12 FastK and SlowD condition helpers."""
    high = np.linspace(10.0, 20.0, 25)
    low = high - 1.5
    close = high - 0.3
    st = Stochastic(k_period=5, d_period=3, slowing=3).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
    )
    assert "k" in st and "d" in st
    mock = {
        "k": IndicatorSeries([40.0, 30.0, 60.0]),
        "d": IndicatorSeries([45.0, 35.0, 50.0]),
    }
    assert crosses_above(mock["k"], mock["d"], shift=0) is True
    assert crosses_below(mock["k"], mock["d"], shift=0) is False
    assert is_greater(mock["k"], mock["d"], shift=0) is True
    assert is_lower(mock["k"], mock["d"], shift=1) is True
    assert crosses_above(mock["k"], 50.0, shift=0) is True
    assert crosses_below(mock["k"], 35.0, shift=1) is True
    assert changes_up(mock["d"], shift=0) is True
    assert changes_down(mock["d"], shift=0) is False
    assert crosses_above(mock["d"], 40.0, shift=0) is True
    assert crosses_below(mock["d"], 40.0, shift=1) is True
    assert is_rising(mock["d"], shift=0) is True
    assert is_falling(mock["d"], shift=1) is True
    assert is_greater(mock["d"], 45.0, shift=0) is True
    assert is_lower(mock["d"], 40.0, shift=1) is True


def test_wave_trend_all_18_conditions() -> None:
    """Verify WaveTrend calculation and all 18 WT1/WT2 condition helpers."""
    high = np.linspace(50.0, 70.0, 30)
    low = high - 1.5
    close = high - 0.4
    wt = WaveTrend(channel_length=5, average_length=7, signal_length=3).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
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
    assert changes_up(w1, shift=0) is True
    assert changes_down(IndicatorSeries([-5.0, 10.0, 2.0]), shift=0) is True
    assert crosses_above(w1, 5.0, shift=0) is True
    assert crosses_below(w1, 0.0, shift=1) is True
    assert is_greater(w1, 5.0, shift=0) is True
    assert is_lower(w1, 0.0, shift=1) is True
    assert is_greater(w1, w2, shift=0) is True
    assert is_lower(w1, w2, shift=1) is True
    assert is_greater(w1, 0.0, shift=0) is True
    assert is_lower(w1, 0.0, shift=1) is True
    assert is_rising(w2, shift=0) is True
    assert is_falling(w2, shift=1) is True


def test_cot_calculate_and_all_conditions() -> None:
    """Verify COT calculation, value helpers, and all specialized COT conditions."""
    comm = np.linspace(-100.0, 100.0, 30)
    spec = -comm
    small = np.linspace(20.0, -20.0, 30)
    oi = np.full(30, 500.0)
    res = COT(period_fast=5, period_slow=10).calculate(
        BarData.from_arrays(
            commercial_net=comm,
            speculator_net=spec,
            small_spec_net=small,
            open_interest=oi,
        )
    )
    assert "composite_score" in res and "cpi_small" in res and ("cti_hedger" in res)
    h52 = IndicatorSeries([0.6, 0.7, 0.8, 0.85, 0.9])
    s52 = IndicatorSeries([0.4, 0.3, 0.2, 0.15, 0.1])
    h156 = IndicatorSeries([0.5, 0.55, 0.6, 0.65, 0.72])
    s156 = IndicatorSeries([0.5, 0.45, 0.4, 0.35, 0.28])
    sm52 = IndicatorSeries([0.5, 0.4, 0.3, 0.2, 0.15])
    score = IndicatorSeries([-0.3, -0.2, -0.05, 0.25, 0.7])
    assert cot_signals.field_value(h52) == pytest.approx(0.9)
    assert cot_signals.cross_field_spread(h52, s52) == pytest.approx(0.8)
    assert cot_signals.momentum(h52, lookback=2) == pytest.approx(0.1)
    assert cot_signals.multi_field_combo(h52, s52, sm52, s156) > 0.7
    assert is_greater(score, 0.6, shift1=0) is True
    assert is_lower(score, -0.2, shift1=4) is True
    assert is_greater(score, 0.0, shift1=0) is True
    assert is_lower(score, 0.0, shift1=3) is True
    assert crosses_above(score, 0.0, shift=1) is True
    assert crosses_below(IndicatorSeries([0.2, -0.1]), 0.0, shift=0) is True
    assert is_rising(score) is True
    assert is_falling(IndicatorSeries([0.5, 0.2])) is True
    assert changes_up(IndicatorSeries([0.5, 0.2, 0.6])) is True
    assert changes_down(IndicatorSeries([0.2, 0.6, 0.3])) is True
    assert crosses_above(score, 0.5) is True
    assert crosses_below(IndicatorSeries([0.6, 0.3]), 0.5) is True
    assert is_greater(score, 0.5) is True
    assert is_lower(score, 0.8) is True
    assert cot_signals.shift_52_vs_156_bullish(h52, s52, h156, s156, 0.1) is True
    assert cot_signals.shift_52_vs_156_bearish(s52, h52, s156, h156, 0.1) is True
    assert cot_signals.accumulation_bullish(h52, s52, min_weeks=3) is True
    assert cot_signals.accumulation_bearish(s52, h52, min_weeks=3) is True
    assert (
        cot_signals.extreme_bullish(h52, s52, 0.8, 0.2, hedg156=h156, spec156=s156)
        is True
    )
    assert (
        cot_signals.extreme_bearish(s52, h52, 0.2, 0.8, hedg156=s156, spec156=h156)
        is True
    )
    assert (
        cot_signals.convergence(IndicatorSeries([0.5]), IndicatorSeries([0.55]), 0.1)
        is True
    )
    assert (
        cot_signals.crowding_unwind(
            IndicatorSeries([0.2, 0.2]),
            IndicatorSeries([0.9, 0.8]),
            direction=1,
            spec_extreme=0.85,
            hedger_opposing=0.3,
        )
        is True
    )
    assert (
        cot_signals.extreme_exit_bullish(
            IndicatorSeries([0.9, 0.65]), extreme_threshold=0.85, exit_threshold=0.7
        )
        is True
    )
    assert (
        cot_signals.extreme_exit_bearish(
            IndicatorSeries([0.9, 0.65]), extreme_threshold=0.85, exit_threshold=0.7
        )
        is True
    )
    assert (
        cot_signals.extreme_persistence(h52, extreme_threshold=0.75, min_weeks=3)
        is True
    )
    assert (
        cot_signals.extreme_unwind_bullish(
            IndicatorSeries([0.9, 0.8, 0.7]),
            crowded_threshold=0.85,
            normalize_threshold=0.75,
        )
        is True
    )
    assert (
        cot_signals.extreme_unwind_bearish(
            IndicatorSeries([0.9, 0.8, 0.7]),
            crowded_threshold=0.85,
            normalize_threshold=0.75,
        )
        is True
    )
    assert cot_signals.full_cycle_long(h52, entry_level=0.88) is True
    assert cot_signals.full_cycle_short(s52, entry_level=0.12) is True
    assert cot_signals.full_cycle_exit_long(h52, exit_level=0.5) is True
    assert cot_signals.full_cycle_exit_short(s52, exit_level=0.5) is True
    assert cot_signals.hedger_accel_bullish(h52, s52, h156, s156, 0.1) is True
    assert cot_signals.hedger_accel_bearish(s52, h52, s156, h156, 0.1) is True
    assert (
        cot_signals.hedger_div_conf_bullish(h52, s52, 0.75, 0.25, mom_lookback=2)
        is True
    )
    assert (
        cot_signals.hedger_div_conf_bearish(s52, h52, 0.25, 0.75, mom_lookback=2)
        is True
    )
    assert cot_signals.higher_low(score, short_window=2, long_window=5) is True
    assert (
        cot_signals.lower_high(
            IndicatorSeries([0.4, 0.3, 0.2, 0.1, 0.05]), short_window=2, long_window=5
        )
        is True
    )
    assert (
        cot_signals.momentum_rev_bullish(
            IndicatorSeries([0.5, 0.2, 0.0, 0.1, 0.3]), mom_period=2
        )
        is True
    )
    assert (
        cot_signals.momentum_rev_bearish(
            IndicatorSeries([-0.5, -0.2, 0.1, 0.0, -0.3]), mom_period=2
        )
        is True
    )
    assert cot_signals.multi_window_bullish(h52, s52, h156, s156) is True
    assert cot_signals.multi_window_bearish(s52, h52, s156, h156) is True
    assert cot_signals.neutral_zone(score, neutral_band=0.1, shift=2) is True
    assert (
        cot_signals.regime_shift_bullish(
            IndicatorSeries([-0.2, -0.1, 0.0, 0.1, 0.3, 0.5]), shift_weeks=2
        )
        is True
    )
    assert (
        cot_signals.regime_shift_bearish(
            IndicatorSeries([0.2, 0.1, 0.0, -0.1, -0.3, -0.5]), shift_weeks=2
        )
        is True
    )
    assert cot_signals.roc_bullish(score, roc_period=2, roc_threshold=0.2) is True
    assert (
        cot_signals.roc_bearish(
            IndicatorSeries([0.5, 0.2, -0.3]), roc_period=2, roc_threshold=0.2
        )
        is True
    )
    assert is_greater(score, 0.5, shift1=0) is True
    assert is_lower(score, 0.0, shift1=3) is True
    assert (
        cot_signals.score_accel_bullish(score, mom_period=2, momentum_threshold=0.1)
        is True
    )
    assert (
        cot_signals.score_accel_bearish(
            IndicatorSeries([0.5, 0.4, 0.3, 0.1, -0.4]),
            mom_period=2,
            momentum_threshold=-0.1,
        )
        is True
    )
    assert cot_signals.score_momentum_above(score, momentum_lookback=2) is True
    assert (
        cot_signals.score_momentum_below(
            IndicatorSeries([0.3, 0.0, -0.4]), momentum_lookback=2
        )
        is True
    )
    assert (
        cot_signals.seasonal_bullish(h52, seasonal_lookback=3, seasonal_threshold=0.05)
        is True
    )
    assert (
        cot_signals.seasonal_bearish(s52, seasonal_lookback=3, seasonal_threshold=0.05)
        is True
    )
    assert is_lower(sm52, 0.2, shift1=0) is True
    assert is_greater(sm52, 0.4, shift1=4) is True
    assert cot_signals.smart_dumb_bullish(h52, sm52) is True
    assert cot_signals.smart_dumb_bearish(s52, h52) is True
    assert (
        cot_signals.spec_exhaustion_long(
            IndicatorSeries([0.8, 0.85]),
            IndicatorSeries([0.05, 0.15]),
            spec_extreme=0.9,
            hedger_threshold=0.7,
            lookback_weeks=1,
        )
        is True
    )
    assert (
        cot_signals.spec_exhaustion_short(
            IndicatorSeries([0.2, 0.15]),
            IndicatorSeries([0.95, 0.85]),
            spec_extreme=0.9,
            hedger_threshold=0.3,
            lookback_weeks=1,
        )
        is True
    )
    assert (
        cot_signals.spec_trend_long(
            IndicatorSeries([0.4, 0.5, 0.65]),
            IndicatorSeries([0.55, 0.55, 0.6]),
            lookback=2,
        )
        is True
    )
    assert (
        cot_signals.spec_trend_short(
            IndicatorSeries([0.6, 0.5, 0.35]),
            IndicatorSeries([0.45, 0.45, 0.4]),
            lookback=2,
        )
        is True
    )
    assert (
        cot_signals.spread_zscore_bullish(h52, s52, period=4, z_threshold=1.0) is True
    )
    assert (
        cot_signals.spread_zscore_bearish(s52, h52, period=4, z_threshold=1.0) is True
    )
    assert cot_signals.triple_div_bullish(h52, s52, sm52) is True
    assert cot_signals.triple_div_bearish(s52, h52, h52) is True
    assert cot_signals.vix_proxy_bullish(h52, s52) is True
    assert cot_signals.vix_proxy_bearish(s52, h52) is True


def test_volume_profile_custom_hours_and_all_36_conditions() -> None:
    """Verify VolumeProfile calculation, custom-hour sessions, and all 36 VP* conditions."""
    base_sec = 1700006400
    ts = [base_sec + i * 3600 for i in range(15)]
    high = np.linspace(100.0, 114.0, 15)
    low = high - 2.0
    open_p = high - 1.2
    close = high - 0.4
    vol = np.linspace(100.0, 500.0, 15)
    bars = BarData.from_arrays(
        high=high, low=low, close=close, volume=vol, open_prices=open_p, timestamps=ts
    )
    vp = VolumeProfile(session_type=5, bin_size_mode=1, profile_rows=10).calculate(bars)
    assert {"poc", "vah", "val", "bull_poc", "bear_poc", "delta", "ibh", "ibl"} <= set(
        vp
    )
    vp_ch = VolumeProfile(
        profile_mode="custom", session_mode=2, bin_size_mode=1
    ).calculate(bars)
    vp_ms = VolumeProfile(
        profile_mode="multi", session_mode=2, bin_size_mode=1
    ).calculate(bars)
    assert not np.isnan(vp_ch["poc"].get(0))
    assert not np.isnan(vp_ms["poc"].get(0))
    poc = IndicatorSeries([100.0, 101.0, 102.0, 104.0])
    vah = IndicatorSeries([102.0, 103.0, 104.0, 106.0])
    val = IndicatorSeries([98.0, 99.0, 100.0, 103.5])
    c_in = IndicatorSeries([97.0, 97.5, 98.0, 104.5])
    assert is_greater(c_in, poc, shift1=0, shift2=0) is True
    assert is_lower(IndicatorSeries([103.0]), poc, shift1=0, shift2=0) is True
    assert VolumeProfile.price_inside_va(c_in, vah, val) is True
    assert VolumeProfile.price_outside_va(c_in, vah, val, shift=1) is True
    assert is_rising(poc, shift=0) is True
    assert is_falling(poc, shift=0) is False
    assert is_rising(vah, shift=0) is True
    assert is_falling(vah, shift=0) is False
    assert is_rising(val, shift=0) is True
    assert is_falling(val, shift=0) is False
    assert VolumeProfile.is_narrow_value_area(vah, val, threshold=5.0) is True
    assert VolumeProfile.is_wide_value_area(vah, val, threshold=2.0) is True
    assert (
        is_greater(
            IndicatorSeries([105.0]), IndicatorSeries([102.0]), shift1=0, shift2=0
        )
        is True
    )
    assert (
        is_greater(
            IndicatorSeries([105.0]), IndicatorSeries([102.0]), shift1=0, shift2=0
        )
        is True
    )
    assert VolumeProfile.bottom_heavy_poc(IndicatorSeries([20.0]), 35.0) is True
    assert VolumeProfile.top_heavy_poc(IndicatorSeries([20.0]), 35.0) is True
    assert is_greater(IndicatorSeries([250.0]), 100.0, shift1=0) is True
    assert is_lower(IndicatorSeries([-250.0]), -100.0, shift1=0) is True
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
            IndicatorSeries([97.0]), IndicatorSeries([99.0]), IndicatorSeries([98.0])
        )
        is True
    )
    assert (
        VolumeProfile.ib_rejection_short(
            IndicatorSeries([106.0]), IndicatorSeries([104.0]), IndicatorSeries([105.0])
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
            val=val,
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
            val=val,
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
        crosses_above(
            IndicatorSeries([99.0, 102.0]), IndicatorSeries([100.0, 100.0]), shift=0
        )
        is True
    )
    assert (
        crosses_below(
            IndicatorSeries([102.0, 99.0]), IndicatorSeries([100.0, 100.0]), shift=0
        )
        is True
    )


def test_williams_pr_and_series_data_only() -> None:
    """Verify WilliamsPR conditions and that IndicatorSeries has no comparison methods."""
    from app.extend.blocks.indicators.momentum.williams_pr import WilliamsPR

    high = np.array([12.0, 13.0, 14.0, 13.5, 15.0])
    low = np.array([10.0, 11.0, 12.0, 11.5, 13.0])
    close = np.array([11.5, 12.5, 13.5, 12.0, 14.5])
    wpr = WilliamsPR(period=3).calculate(
        BarData.from_arrays(high=high, low=low, close=close)
    )["value"]
    assert len(wpr) == 5
    for attr in (
        "is_rising",
        "is_falling",
        "crosses_above",
        "crosses_below",
        "is_greater",
        "is_lower",
        "is_higher",
        "changes_up",
        "changes_down",
    ):
        assert not hasattr(wpr, attr)
    s = IndicatorSeries([-60.0, -75.0, -40.0])
    assert is_rising(s, shift=0) is True
    assert is_falling(s, shift=1) is True
    assert crosses_above(s, -50.0, shift=0) is True
    assert crosses_below(s, -65.0, shift=1) is True
    assert is_greater(s, s, shift1=0, shift2=0 + 1) is True
    assert is_lower(s, s, shift1=1, shift2=1 + 1) is True
    assert changes_up(s, shift=0) is True
    assert changes_down(IndicatorSeries([-75.0, -40.0, -55.0]), shift=0) is True


def test_indicator_non_silent_requirement_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify indicator batch calculations emit non-silent requirement logs."""
    import logging

    from app.extend.blocks.indicators.momentum.rsi import RSI
    from app.extend.blocks.indicators.trend.sma import SMA
    from app.extend.blocks.indicators.volatility.bollinger_bands import BollingerBands

    caplog.set_level(logging.DEBUG)

    test_bars = BarData.from_arrays(
        open=np.full(30, 100.0),
        high=np.full(30, 105.0),
        low=np.full(30, 95.0),
        close=np.full(30, 102.0),
        volume=np.full(30, 1000.0),
    )

    # Trend calculation log
    SMA(period=5).calculate(test_bars)
    assert any(
        "FR-SERVICES-INDICATOR-TREND" in record.message for record in caplog.records
    )

    # Momentum calculation log
    caplog.clear()
    RSI(period=5).calculate(test_bars)
    assert any(
        "FR-SERVICES-INDICATOR-MOMENTUM" in record.message for record in caplog.records
    )

    # Volatility calculation log
    caplog.clear()
    BollingerBands(period=5).calculate(test_bars)
    assert any(
        "FR-SERVICES-INDICATOR-VOLATILITY" in record.message
        for record in caplog.records
    )
