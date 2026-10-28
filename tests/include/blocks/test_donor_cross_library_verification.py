"""Cross-library verification against donor behavior: warmup, rounding, shifts, and boundaries."""

from __future__ import annotations

import numpy as np
import pytest
from app.include.blocks.indicators.momentum.cci import CCI
from app.include.blocks.indicators.momentum.macd import MACD
from app.include.blocks.indicators.momentum.rsi import RSI
from app.include.blocks.indicators.momentum.stochastic import Stochastic
from app.include.blocks.indicators.trend.ema import EMA
from app.include.blocks.indicators.volatility.atr import ATR
from app.include.blocks.indicators.volatility.bollinger_bands import BollingerBands
from app.include.blocks.indicators.volume.volume_profile import VolumeProfile
from app.include.blocks.registry import BlockRegistry
from app.include.blocks.series import BarData


@pytest.fixture(scope="module")
def catalog():
    reg = BlockRegistry()
    reg.discover("app/include/blocks/indicators")
    reg.discover("app/include/blocks/comparisons")
    return reg.snapshot()


def make_bars(count: int, seed: int = 42) -> BarData:
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0, 0.5, count))
    high = close + np.abs(rng.normal(0, 0.3, count))
    low = close - np.abs(rng.normal(0, 0.3, count))
    open_ = low + (high - low) * rng.uniform(0.1, 0.9, count)
    volume = rng.uniform(10.0, 1000.0, count)
    timestamps = np.arange(count, dtype=np.int64) * 60000 + 1704153600000
    return BarData.from_arrays(
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        timestamps=timestamps,
    )


# ---------------------------------------------------------------------------
# 1. Warmup Periods Across Indicator Families
# ---------------------------------------------------------------------------


def test_rsi_warmup_produces_nans_before_period():
    bars = make_bars(30)
    rsi = RSI(period=14)
    res = rsi.calculate(bars)
    vals = res["value"].values
    # First 13 bars should be NaN warmup in standard Wilder RSI
    assert np.isnan(vals[:13]).all()
    # From bar 14 onwards, finite values
    assert np.isfinite(vals[14:]).all()


def test_macd_warmup_requires_slow_plus_smooth():
    bars = make_bars(50)
    macd = MACD(fast=12, slow=26, smooth=9)
    res = macd.calculate(bars)
    main = res["main"].values
    signal = res["signal"].values
    # MACD main finite after slow period
    assert np.isfinite(main[26:]).all()
    # Signal line finite after slow + smooth
    assert np.isfinite(signal[34:]).all()


def test_bollinger_bands_warmup_requires_period():
    bars = make_bars(30)
    bb = BollingerBands(period=20)
    res = bb.calculate(bars)
    # First 19 bars are warmup
    assert np.isnan(res["middle"].values[:19]).all()
    assert np.isfinite(res["middle"].values[19:]).all()


def test_stochastic_warmup_requires_k_plus_slowing_plus_d():
    bars = make_bars(30)
    stoch = Stochastic(k_period=14, slowing=3, d_period=3)
    res = stoch.calculate(bars)
    d = res["d"].values
    # Requires k_period (14) + slowing (3) + d_period (3) - 2 = 18 bars
    assert np.isfinite(d[18:]).all()


# ---------------------------------------------------------------------------
# 2. Shift Causality and Boundary Bounding
# ---------------------------------------------------------------------------


def test_shift_causality_matches_subsets(catalog):
    recipe = catalog.require("signal.rsi.rsi_rising").target
    full_bars = make_bars(50)

    # Shift 0 on prefix(40) must equal Shift 10 on prefix(50)
    prefix_40 = make_bars(40)
    res_prefix_shift0 = recipe(prefix_40, shift=0)
    res_full_shift10 = recipe(full_bars, shift=10)
    assert res_prefix_shift0 == res_full_shift10

    # Shift out of bounds (larger than dataset) returns False or handles cleanly
    res_oob = recipe(full_bars, shift=60)
    assert res_oob is False


# ---------------------------------------------------------------------------
# 3. Rounding Parity
# ---------------------------------------------------------------------------


def test_composition_applies_six_digit_rounding_to_outputs(catalog):
    """Donor getRounded() rounds to 6 digits; micro-differences below 1e-6 do not trigger crosses."""
    from app.include.blocks.series import IndicatorSeries

    recipe = catalog.require("signal.rsi.rsi_cross_up").target
    # 29.9999999 and 30.0000001 both round to 30.000000 at 6 digits
    outputs = {
        "i0": {
            "value": IndicatorSeries([29.9999999, 30.0000001]),
        }
    }
    source = make_bars(2)
    # If rounded to 6 digits, 30.000000 == 30.000000, so it is a touch, not a strict cross
    assert not recipe.evaluate_outputs(outputs, source, level=30.0)

    # A real cross across 6 digits
    outputs_cross = {
        "i0": {
            "value": IndicatorSeries([29.5, 30.5]),
        }
    }
    assert recipe.evaluate_outputs(outputs_cross, source, level=30.0)


# ---------------------------------------------------------------------------
# 4. Boundary and Exceptional Inputs
# ---------------------------------------------------------------------------


def test_flat_price_series_zero_division_resilience():
    """Flat price series (high == low == open == close) must not raise ZeroDivisionError."""
    n = 30
    flat = np.full(n, 100.0)
    bars = BarData.from_arrays(
        open=flat,
        high=flat,
        low=flat,
        close=flat,
        volume=np.full(n, 100.0),
        timestamps=np.arange(n, dtype=np.int64) * 60000 + 1704153600000,
    )

    # ATR should be 0.0
    atr = ATR(period=14).calculate(bars)
    assert np.allclose(atr["value"].values[14:], 0.0)

    # Bollinger Bands width should be 0.0, upper == lower == middle == 100.0
    bb = BollingerBands(period=20).calculate(bars)
    assert np.allclose(bb["middle"].values[19:], 100.0)
    assert np.allclose(bb["upper"].values[19:], 100.0)
    assert np.allclose(bb["lower"].values[19:], 100.0)

    # RSI on flat series should return neutral 50.0 without ZeroDivisionError
    rsi = RSI(period=14).calculate(bars)
    assert np.allclose(rsi["value"].values[14:], 50.0)

    # Stochastic on flat series should be neutral 50.0 without ZeroDivisionError
    stoch = Stochastic(k_period=14, slowing=3, d_period=3).calculate(bars)
    assert np.allclose(stoch["k"].values[18:], 50.0)

    # CCI on flat series should be 0.0
    cci = CCI(period=14).calculate(bars)
    assert np.allclose(cci["value"].values[14:], 0.0)


def test_single_bar_input():
    """Single bar input should not raise unhandled index errors."""
    bars = BarData.from_arrays(
        open=[100.0],
        high=[101.0],
        low=[99.0],
        close=[100.5],
        volume=[50.0],
        timestamps=[1704153600000],
    )
    # EMA on single bar
    res = EMA(period=20).calculate(bars)
    assert len(res["value"].values) == 1

    # VolumeProfile on single bar
    vp = VolumeProfile(
        session_type=5, bin_size_mode=1, profile_rows=10, timestamp_unit="milliseconds"
    )
    vp_res = vp.calculate(bars)
    assert len(vp_res["poc"].values) == 1


def test_zero_volume_handling():
    """Zero volume bars must not cause ZeroDivisionError in volume profiles."""
    n = 20
    prices = 100.0 + np.arange(n) * 0.1
    bars = BarData.from_arrays(
        open=prices,
        high=prices + 0.2,
        low=prices - 0.2,
        close=prices,
        volume=np.zeros(n),
        timestamps=np.arange(n, dtype=np.int64) * 60000 + 1704153600000,
    )
    vp = VolumeProfile(
        session_type=5, bin_size_mode=1, profile_rows=10, timestamp_unit="milliseconds"
    )
    vp_res = vp.calculate(bars)
    assert vp_res["total_volume"].values[-1] == 0.0
