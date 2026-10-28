"""Unit tests for discrete price building blocks, containers, and Price facade."""

from __future__ import annotations

import math
from datetime import UTC, datetime

import pytest
from app.include.blocks.price import (
    CLOSE,
    DEFAULT_PIP_SIZE,
    HIGH,
    LOW,
    OPEN,
    BarPrice,
    MTFPrice,
    Price,
    QuotePrice,
    SessionOHLCCalculator,
    SessionPrice,
    ask,
    ask_spec,
    bar_close,
    bar_high,
    bar_low,
    bar_open,
    bar_volume,
    bid,
    bid_spec,
    close_d,
    close_d_spec,
    close_m,
    close_m_spec,
    close_spec,
    close_w,
    close_w_spec,
    heiken_ashi_close,
    heiken_ashi_close_spec,
    heiken_ashi_high,
    heiken_ashi_high_spec,
    heiken_ashi_low,
    heiken_ashi_low_spec,
    heiken_ashi_open,
    heiken_ashi_open_spec,
    high_d,
    high_d_spec,
    high_m,
    high_m_spec,
    high_spec,
    high_w,
    high_w_spec,
    low_d,
    low_d_spec,
    low_m,
    low_m_spec,
    low_price,
    low_spec,
    low_w,
    low_w_spec,
    open_d,
    open_d_spec,
    open_m,
    open_m_spec,
    open_price,
    open_spec,
    open_w,
    open_w_spec,
    session_close,
    session_close_spec,
    session_high,
    session_high_spec,
    session_low,
    session_low_spec,
    session_open,
    session_open_spec,
    spread,
    spread_in_pips,
    spread_in_pips_spec,
    spread_spec,
    volume_spec,
)


def test_bar_price_container() -> None:
    """Verify BarPrice initialization, shifting, series export, and validations."""
    opens = [100.0, 101.0, 102.0]
    highs = [105.0, 106.0, 107.0]
    lows = [95.0, 96.0, 97.0]
    closes = [104.0, 103.0, 105.0]
    vols = [1000.0, 1500.0, 2000.0]

    bp = BarPrice(opens, highs, lows, closes, vols)
    assert len(bp) == 3

    # Shift 0 is latest bar (index 2)
    assert bp.open(0) == 102.0
    assert bp.high(0) == 107.0
    assert bp.low(0) == 97.0
    assert bp.close(0) == 105.0
    assert bp.volume(0) == 2000.0

    # Shift 1 is 1 bar ago (index 1)
    assert bp.open(1) == 101.0
    assert bp.high(1) == 106.0
    assert bp.low(1) == 96.0
    assert bp.close(1) == 103.0
    assert bp.volume(1) == 1500.0

    # Out of bounds
    assert math.isnan(bp.open(3))
    assert math.isnan(bp.close(-1))

    # Read-only views
    assert len(bp.open_values) == 3
    assert len(bp.high_values) == 3
    assert len(bp.low_values) == 3
    assert len(bp.close_values) == 3
    assert len(bp.volume_values) == 3

    # Series exports
    assert bp.open_series().name == "Open"
    assert bp.high_series().name == "High"
    assert bp.low_series().name == "Low"
    assert bp.close_series().name == "Close"
    assert bp.volume_series().name == "Volume"

    # Validation errors
    with pytest.raises(ValueError):
        BarPrice([], [], [], [])
    with pytest.raises(ValueError):
        BarPrice([1.0], [2.0, 3.0], [1.0], [2.0])


def test_quote_price_container() -> None:
    """Verify QuotePrice bid/ask, spread, spread_in_pips, and series exports."""
    bids = [1.1000, 1.1010, 1.1020]
    asks = [1.1002, 1.1013, 1.1024]

    qp = QuotePrice(bids, asks, pip_size=0.0001)
    assert len(qp) == 3
    assert qp.pip_size == DEFAULT_PIP_SIZE

    # Shift 0 is newest
    assert math.isclose(qp.bid(0), 1.1020)
    assert math.isclose(qp.ask(0), 1.1024)
    assert math.isclose(qp.spread(0), 0.0004)
    assert math.isclose(qp.spread_in_pips(0), 4.0)

    # Shift 1
    assert math.isclose(qp.spread(1), 0.0003)
    assert math.isclose(qp.spread_in_pips(1), 3.0)

    # Series
    assert qp.bid_series().name == "Bid"
    assert qp.ask_series().name == "Ask"
    assert qp.spread_series().name == "Spread"
    assert qp.spread_in_pips_series().name == "SpreadInPips"

    # Validation errors
    with pytest.raises(ValueError):
        QuotePrice([], [])
    with pytest.raises(ValueError):
        QuotePrice([1.0], [1.0, 2.0])
    with pytest.raises(ValueError):
        QuotePrice([1.0], [1.0], pip_size=-1)


def test_mtf_price_aggregates() -> None:
    """Verify MTFPrice aggregation into daily, weekly, and monthly bars."""
    # Create hourly timestamps for 3 consecutive days across two weeks
    # Day 1: 2024-01-05 (Friday, week 1)
    # Day 2: 2024-01-08 (Monday, week 2)
    # Day 3: 2024-01-09 (Tuesday, week 2)
    t1 = int(datetime(2024, 1, 5, 10, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 14, 0, tzinfo=UTC).timestamp())
    t3 = int(datetime(2024, 1, 8, 10, 0, tzinfo=UTC).timestamp())
    t4 = int(datetime(2024, 1, 9, 10, 0, tzinfo=UTC).timestamp())

    ts = [t1, t2, t3, t4]
    opens = [10.0, 12.0, 20.0, 30.0]
    highs = [15.0, 16.0, 25.0, 35.0]
    lows = [8.0, 11.0, 18.0, 28.0]
    closes = [12.0, 14.0, 22.0, 32.0]

    mtf = MTFPrice(ts, opens, highs, lows, closes)

    # 3 days: Day 1 (index 0), Day 2 (index 1), Day 3 (index 2)
    # Shift 0 is Day 3
    assert mtf.daily_open(0) == 30.0
    assert mtf.daily_high(0) == 35.0
    assert mtf.daily_low(0) == 28.0
    assert mtf.daily_close(0) == 32.0

    # Shift 2 is Day 1 (merged t1 and t2)
    assert mtf.daily_open(2) == 10.0
    assert mtf.daily_high(2) == 16.0
    assert mtf.daily_low(2) == 8.0
    assert mtf.daily_close(2) == 14.0

    # 2 weeks: Week 1 (Day 1), Week 2 (Day 2 + Day 3)
    # Shift 0 is Week 2
    assert mtf.weekly_open(0) == 20.0
    assert mtf.weekly_high(0) == 35.0
    assert mtf.weekly_low(0) == 18.0
    assert mtf.weekly_close(0) == 32.0

    # Shift 1 is Week 1
    assert mtf.weekly_open(1) == 10.0
    assert mtf.weekly_close(1) == 14.0

    # Monthly
    assert mtf.monthly_open(0) == 10.0
    assert mtf.monthly_close(0) == 32.0


def test_session_price_and_calculator() -> None:
    """Verify SessionPrice windowing and SessionOHLCCalculator evaluations."""
    # Bars at 08:00, 09:00, 12:00, 16:00
    t1 = int(datetime(2024, 1, 5, 8, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 9, 0, tzinfo=UTC).timestamp())
    t3 = int(datetime(2024, 1, 5, 12, 0, tzinfo=UTC).timestamp())
    t4 = int(datetime(2024, 1, 5, 16, 0, tzinfo=UTC).timestamp())

    ts = [t1, t2, t3, t4]
    opens = [10.0, 20.0, 30.0, 40.0]
    highs = [12.0, 25.0, 35.0, 42.0]
    lows = [9.0, 18.0, 28.0, 38.0]
    closes = [11.0, 22.0, 32.0, 41.0]

    # Session 08:30 to 15:00: only t2 (09:00) and t3 (12:00) fall inside
    sp = SessionPrice(
        ts,
        opens,
        highs,
        lows,
        closes,
        start_hour=8,
        start_minute=30,
        end_hour=15,
        end_minute=0,
    )

    assert sp.open(0) == 20.0
    assert sp.high(0) == 35.0
    assert sp.low(0) == 18.0
    assert sp.close(0) == 32.0

    # Test SessionOHLCCalculator
    calc_open = SessionOHLCCalculator(output_type=OPEN, chart=sp)
    assert calc_open.get() == 20.0

    calc_high = SessionOHLCCalculator(output_type=HIGH, chart=sp)
    assert calc_high.get() == 35.0

    calc_low = SessionOHLCCalculator(output_type=LOW, chart=sp)
    assert calc_low.get() == 18.0

    calc_close = SessionOHLCCalculator(output_type=CLOSE, chart=sp)
    assert calc_close.get() == 32.0


def test_discrete_bar_blocks() -> None:
    """Verify bar_open, bar_high, bar_low, bar_close, bar_volume discrete blocks."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [5.0, 15.0], [12.0, 22.0], [100.0, 200.0])

    assert bar_open(bp, 0) == 20.0
    assert open_price(bp, 1) == 10.0
    assert bar_high(bp, 0) == 25.0
    assert bar_low(bp, 0) == 15.0
    assert low_price(bp, 1) == 5.0
    assert bar_close(bp, 0) == 22.0
    assert bar_volume(bp, 0) == 200.0


def test_discrete_quote_blocks() -> None:
    """Verify ask, bid, spread, spread_in_pips blocks."""
    qp = QuotePrice([1.2000, 1.2010], [1.2002, 1.2014], pip_size=0.0001)

    assert math.isclose(ask(qp, 0), 1.2014)
    assert math.isclose(bid(qp, 0), 1.2010)
    assert math.isclose(spread(qp, 0), 0.0004)
    assert math.isclose(spread_in_pips(qp, 0), 4.0)


def test_discrete_mtf_blocks() -> None:
    """Verify open_d, high_d, low_d, close_d, and W/M blocks."""
    t1 = int(datetime(2024, 1, 5, 10, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 8, 10, 0, tzinfo=UTC).timestamp())
    mtf = MTFPrice([t1, t2], [10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    assert open_d(mtf, 0) == 20.0
    assert high_d(mtf, 0) == 25.0
    assert low_d(mtf, 0) == 18.0
    assert close_d(mtf, 0) == 22.0

    assert open_w(mtf, 0) == 20.0
    assert high_w(mtf, 0) == 25.0
    assert low_w(mtf, 0) == 18.0
    assert close_w(mtf, 0) == 22.0

    assert open_m(mtf, 0) == 10.0
    assert high_m(mtf, 0) == 25.0
    assert low_m(mtf, 0) == 8.0
    assert close_m(mtf, 0) == 22.0


def test_discrete_session_blocks() -> None:
    """Verify session_open, session_high, session_low, session_close blocks."""
    t1 = int(datetime(2024, 1, 5, 9, 0, tzinfo=UTC).timestamp())
    t2 = int(datetime(2024, 1, 5, 12, 0, tzinfo=UTC).timestamp())
    sp = SessionPrice([t1, t2], [10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    assert session_open(sp, shift=0) == 10.0
    assert session_high(sp, shift=0) == 25.0
    assert session_low(sp, shift=0) == 8.0
    assert session_close(sp, shift=0) == 22.0


def test_heiken_ashi_blocks() -> None:
    """Verify heiken_ashi_open, heiken_ashi_high, heiken_ashi_low, heiken_ashi_close."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0])

    # Bar 0:
    # ha_close[0] = (10 + 15 + 8 + 12)/4 = 11.25
    # ha_open[0] = (10 + 12)/2 = 11.0
    # ha_high[0] = max(15, 11, 11.25) = 15.0
    # ha_low[0] = min(8, 11, 11.25) = 8.0
    # Bar 1:
    # ha_close[1] = (20 + 25 + 18 + 22)/4 = 21.25
    # ha_open[1] = (11.0 + 11.25)/2 = 11.125
    # ha_high[1] = max(25, 11.125, 21.25) = 25.0
    # ha_low[1] = min(18, 11.125, 21.25) = 11.125

    # Shift 0 is Bar 1
    assert heiken_ashi_close(bp, 0) == 21.25
    assert heiken_ashi_open(bp, 0) == 11.125
    assert heiken_ashi_high(bp, 0) == 25.0
    assert heiken_ashi_low(bp, 0) == 11.125

    # Shift 1 is Bar 0
    assert heiken_ashi_close(bp, 1) == 11.25
    assert heiken_ashi_open(bp, 1) == 11.0
    assert heiken_ashi_high(bp, 1) == 15.0
    assert heiken_ashi_low(bp, 1) == 8.0


def test_price_facade() -> None:
    """Verify Price facade methods routing."""
    bp = BarPrice([10.0, 20.0], [15.0, 25.0], [8.0, 18.0], [12.0, 22.0], [100.0, 200.0])

    assert Price.open(bp, 0) == 20.0
    assert Price.high(bp, 0) == 25.0
    assert Price.low(bp, 0) == 18.0
    assert Price.close(bp, 0) == 22.0
    assert Price.volume(bp, 0) == 200.0


def test_all_29_price_block_specs() -> None:
    """Verify all 29 price block specifications are valid."""
    specs = [
        open_spec,
        high_spec,
        low_spec,
        close_spec,
        volume_spec,
        ask_spec,
        bid_spec,
        spread_spec,
        spread_in_pips_spec,
        open_d_spec,
        high_d_spec,
        low_d_spec,
        close_d_spec,
        open_w_spec,
        high_w_spec,
        low_w_spec,
        close_w_spec,
        open_m_spec,
        high_m_spec,
        low_m_spec,
        close_m_spec,
        session_open_spec,
        session_high_spec,
        session_low_spec,
        session_close_spec,
        heiken_ashi_open_spec,
        heiken_ashi_high_spec,
        heiken_ashi_low_spec,
        heiken_ashi_close_spec,
    ]
    assert len(specs) == 29
    for s in specs:
        assert s.id.startswith("price.")
        assert s.category == "price"
        assert len(s.inputs) >= 1
        assert len(s.outputs) == 1
        assert s.is_causal is True
