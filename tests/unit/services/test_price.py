"""Unit test suite for Price building blocks (BarPrice, QuotePrice, MTFPrice, SessionPrice, HeikenAshiPrice).

Description:
    Tests verification of single-bar OHLCV, bid/ask quotes, multi-timeframe
    daily/weekly/monthly aggregations, intraday session windows, and Heiken Ashi
    smoothed price feeds matching StrategyQuant X Price building blocks.

Purpose:
    FEAT-SERVICES-PRICE-TESTS: Comprehensive test coverage for Price building blocks.

Key Capabilities:
    - FR-SERVICES-TEST-PRICE: Assert exact calculation and error handling.
      Associated: `test_bar_price()`, `test_quote_price()`, `test_mtf_price()`,
      `test_session_price()`, `test_heiken_ashi_price()`
      Logging: DEBUG on test execution.

Python API Usage:
    ```python
    uv run pytest tests/unit/services/test_price.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_price.py --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pytest
from app.services.indicators.base import IndicatorSeries
from app.services.utils.price import (
    BarPrice,
    HeikenAshiPrice,
    MTFPrice,
    QuotePrice,
    SessionPrice,
)


def test_bar_price() -> None:
    """Verify BarPrice OHLCV queries, series exports, and error bounds."""
    o_arr = np.array([100.0, 102.0, 104.0, 106.0])
    h_arr = np.array([105.0, 107.0, 108.0, 110.0])
    l_arr = np.array([99.0, 101.0, 103.0, 105.0])
    c_arr = np.array([104.0, 106.0, 107.0, 109.0])
    v_arr = np.array([1000.0, 1500.0, 2000.0, 2500.0])

    bp = BarPrice(o_arr, h_arr, l_arr, c_arr, v_arr)
    assert len(bp) == 4

    # Current bar (shift=0)
    assert bp.open(0) == 106.0
    assert bp.high(0) == 110.0
    assert bp.low(0) == 105.0
    assert bp.close(0) == 109.0
    assert bp.volume(0) == 2500.0

    # 1 bar ago (shift=1)
    assert bp.close(1) == 107.0
    assert bp.open(1) == 104.0

    # Out of bounds shift
    assert np.isnan(bp.close(10))
    assert np.isnan(bp.close(-1))

    # Series exports
    assert isinstance(bp.open_series(), IndicatorSeries)
    assert isinstance(bp.high_series(), IndicatorSeries)
    assert isinstance(bp.low_series(), IndicatorSeries)
    assert isinstance(bp.close_series(), IndicatorSeries)
    assert isinstance(bp.volume_series(), IndicatorSeries)
    assert bp.close_series().get(0) == 109.0

    # Without volume defaults to zeros
    bp_no_vol = BarPrice(o_arr, h_arr, l_arr, c_arr)
    assert bp_no_vol.volume(0) == 0.0

    # Validation errors
    with pytest.raises(ValueError, match="cannot be empty"):
        BarPrice([], [], [], [])
    with pytest.raises(ValueError, match="mismatch"):
        BarPrice(o_arr[:2], h_arr, l_arr, c_arr)
    with pytest.raises(ValueError, match="Volume array length"):
        BarPrice(o_arr, h_arr, l_arr, c_arr, v_arr[:2])


def test_quote_price() -> None:
    """Verify QuotePrice Bid, Ask, Spread, and SpreadInPips calculations."""
    bid = np.array([1.1000, 1.1010, 1.1020])
    ask = np.array([1.1002, 1.1013, 1.1025])

    qp = QuotePrice(bid, ask, pip_size=0.0001)
    assert len(qp) == 3
    assert qp.pip_size == 0.0001

    # Shift 0
    assert qp.bid(0) == 1.1020
    assert qp.ask(0) == 1.1025
    assert pytest.approx(qp.spread(0), rel=1e-5) == 0.0005
    assert pytest.approx(qp.spread_in_pips(0), rel=1e-5) == 5.0

    # Shift 1
    assert pytest.approx(qp.spread(1), rel=1e-5) == 0.0003
    assert pytest.approx(qp.spread_in_pips(1), rel=1e-5) == 3.0

    # Out of bounds
    assert np.isnan(qp.bid(5))
    assert np.isnan(qp.spread(5))
    assert np.isnan(qp.spread_in_pips(5))

    # Custom pip size override
    assert pytest.approx(qp.spread_in_pips(0, pip_size=0.001), rel=1e-5) == 0.5
    assert np.isnan(qp.spread_in_pips(0, pip_size=0.0))

    # Series exports
    assert isinstance(qp.bid_series(), IndicatorSeries)
    assert isinstance(qp.ask_series(), IndicatorSeries)
    assert isinstance(qp.spread_series(), IndicatorSeries)
    assert isinstance(qp.spread_in_pips_series(), IndicatorSeries)

    # Validation errors
    with pytest.raises(ValueError, match="cannot be empty"):
        QuotePrice([], [])
    with pytest.raises(ValueError, match="does not match"):
        QuotePrice(bid[:2], ask)
    with pytest.raises(ValueError, match="strictly positive"):
        QuotePrice(bid, ask, pip_size=-0.01)


def test_mtf_price() -> None:
    """Verify MTFPrice Daily, Weekly, and Monthly OHLC aggregations."""
    # 4 bars across 2 days (Jan 1, 2024 and Jan 2, 2024)
    dt1 = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
    dt2 = datetime(2024, 1, 1, 14, 0, tzinfo=UTC)
    dt3 = datetime(2024, 1, 2, 10, 0, tzinfo=UTC)
    dt4 = datetime(2024, 1, 2, 14, 0, tzinfo=UTC)

    ts = [dt1, dt2, dt3, dt4]
    o_arr = [100.0, 102.0, 105.0, 107.0]
    h_arr = [104.0, 106.0, 108.0, 110.0]
    l_arr = [99.0, 101.0, 104.0, 106.0]
    c_arr = [103.0, 105.0, 107.0, 109.0]

    mtf = MTFPrice(ts, o_arr, h_arr, l_arr, c_arr)

    # Current Day (Jan 2): open=105, high=110, low=104, close=109
    assert mtf.daily_open(0) == 105.0
    assert mtf.daily_high(0) == 110.0
    assert mtf.daily_low(0) == 104.0
    assert mtf.daily_close(0) == 109.0

    # Previous Day (Jan 1): open=100, high=106, low=99, close=105
    assert mtf.daily_open(1) == 100.0
    assert mtf.daily_high(1) == 106.0
    assert mtf.daily_low(1) == 99.0
    assert mtf.daily_close(1) == 105.0

    # Weekly & Monthly
    assert mtf.weekly_close(0) == 109.0
    assert mtf.weekly_open(0) == 100.0
    assert mtf.monthly_close(0) == 109.0
    assert mtf.monthly_open(0) == 100.0

    # Out of bounds
    assert np.isnan(mtf.daily_close(5))
    assert np.isnan(mtf.weekly_high(5))
    assert np.isnan(mtf.monthly_low(5))

    # Series exports
    assert isinstance(mtf.daily_close_series(), IndicatorSeries)
    assert isinstance(mtf.weekly_close_series(), IndicatorSeries)
    assert isinstance(mtf.monthly_close_series(), IndicatorSeries)

    # Timestamp variations: integer seconds, ISO strings, numpy array
    ts_sec = np.array([int(d.timestamp()) for d in ts], dtype=np.int64)
    mtf_sec = MTFPrice(ts_sec, o_arr, h_arr, l_arr, c_arr)
    assert mtf_sec.daily_close(0) == 109.0

    ts_ms = ts_sec * 1000
    mtf_ms = MTFPrice(ts_ms, o_arr, h_arr, l_arr, c_arr)
    assert mtf_ms.daily_close(0) == 109.0

    ts_iso = [d.isoformat() for d in ts]
    mtf_iso = MTFPrice(ts_iso, o_arr, h_arr, l_arr, c_arr)
    assert mtf_iso.daily_close(0) == 109.0

    # Validation errors
    with pytest.raises(ValueError, match="cannot be empty"):
        MTFPrice([], [], [], [], [])
    with pytest.raises(ValueError, match="equal length"):
        MTFPrice(ts[:2], o_arr, h_arr, l_arr, c_arr)


def test_session_price() -> None:
    """Verify SessionPrice intraday window filtering and shift queries."""
    # 4 bars in same day: 08:00, 10:00, 14:00, 18:00
    d1 = datetime(2024, 1, 1, 8, 0, tzinfo=UTC)
    d2 = datetime(2024, 1, 1, 10, 0, tzinfo=UTC)
    d3 = datetime(2024, 1, 1, 14, 0, tzinfo=UTC)
    d4 = datetime(2024, 1, 1, 18, 0, tzinfo=UTC)

    ts = [d1, d2, d3, d4]
    o_arr = [90.0, 100.0, 105.0, 120.0]
    h_arr = [95.0, 108.0, 110.0, 125.0]
    l_arr = [88.0, 98.0, 103.0, 118.0]
    c_arr = [92.0, 106.0, 108.0, 122.0]

    # Session 09:00 - 17:00 covers d2 and d3 only
    sp = SessionPrice(
        ts,
        o_arr,
        h_arr,
        l_arr,
        c_arr,
        start_hour=9,
        start_minute=0,
        end_hour=17,
        end_minute=0,
    )

    assert sp.open(0) == 100.0
    assert sp.high(0) == 110.0
    assert sp.low(0) == 98.0
    assert sp.close(0) == 108.0

    # Out of bounds
    assert np.isnan(sp.open(2))

    # Series exports
    assert isinstance(sp.open_series(), IndicatorSeries)
    assert isinstance(sp.high_series(), IndicatorSeries)
    assert isinstance(sp.low_series(), IndicatorSeries)
    assert isinstance(sp.close_series(), IndicatorSeries)

    # Cross midnight session (e.g., 17:00 to 09:00)
    sp_cross = SessionPrice(
        ts,
        o_arr,
        h_arr,
        l_arr,
        c_arr,
        start_hour=17,
        start_minute=0,
        end_hour=9,
        end_minute=0,
    )
    # Covers d1 (08:00) and d4 (18:00)
    assert sp_cross.open(0) == 90.0

    # Validation errors
    with pytest.raises(ValueError, match="cannot be empty"):
        SessionPrice([], [], [], [], [])
    with pytest.raises(ValueError, match="equal length"):
        SessionPrice(ts[:2], o_arr, h_arr, l_arr, c_arr)
    with pytest.raises(ValueError, match="Invalid session start time"):
        SessionPrice(ts, o_arr, h_arr, l_arr, c_arr, start_hour=25)
    with pytest.raises(ValueError, match="Invalid session end time"):
        SessionPrice(ts, o_arr, h_arr, l_arr, c_arr, end_hour=24)


def test_heiken_ashi_price() -> None:
    """Verify HeikenAshiPrice smoothed candle lookups and series accessors."""
    o_arr = np.array([100.0, 102.0, 104.0])
    h_arr = np.array([105.0, 106.0, 108.0])
    l_arr = np.array([98.0, 101.0, 103.0])
    c_arr = np.array([103.0, 105.0, 107.0])

    hap = HeikenAshiPrice(o_arr, h_arr, l_arr, c_arr)
    assert len(hap) == 3

    assert isinstance(hap.open(0), float)
    assert isinstance(hap.high(0), float)
    assert isinstance(hap.low(0), float)
    assert isinstance(hap.close(0), float)

    # Output series
    assert isinstance(hap.open_series(), IndicatorSeries)
    assert isinstance(hap.high_series(), IndicatorSeries)
    assert isinstance(hap.low_series(), IndicatorSeries)
    assert isinstance(hap.close_series(), IndicatorSeries)

    # Validation errors
    with pytest.raises(ValueError, match="cannot be empty"):
        HeikenAshiPrice([], [], [], [])
    with pytest.raises(ValueError, match="matching lengths"):
        HeikenAshiPrice(o_arr[:2], h_arr, l_arr, c_arr)
