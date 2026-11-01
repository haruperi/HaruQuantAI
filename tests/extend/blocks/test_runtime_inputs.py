"""Qualification of runtime inputs: session profiles, tick sizes, decision prices, and DST."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pytest
from app.extend.blocks.indicators.volume.volume_profile import VolumeProfile
from app.extend.blocks.registry import BlockRegistry
from app.extend.blocks.runtime_inputs import (
    bind_profile_signals,
    bind_runtime_inputs,
    execute_bound_signal,
    resolve_decision_price,
    schedule_calendar_session,
)
from app.extend.blocks.series import BarData
from app.extend.calculators.profile_sessions import session_bounds


@pytest.fixture(scope="module")
def catalog():
    reg = BlockRegistry()
    reg.discover("app/extend/blocks/indicators")
    return reg.snapshot()


def sample_intraday_bars(
    timestamps_ms: list[int],
    base_price: float = 100.0,
    price_step: float = 0.5,
) -> BarData:
    n = len(timestamps_ms)
    prices = base_price + np.arange(n) * price_step
    return BarData.from_arrays(
        open=prices - 0.2,
        high=prices + 0.5,
        low=prices - 0.5,
        close=prices,
        volume=np.full(n, 100.0),
        timestamps=np.asarray(timestamps_ms, dtype=np.int64),
    )


# ---------------------------------------------------------------------------
# 1. Decision Price Resolution
# ---------------------------------------------------------------------------


def test_resolve_decision_price_bar_close():
    bars = BarData.from_arrays(
        close=np.array([10.0, 11.0, 12.0]),
        open=np.array([9.0, 10.0, 11.0]),
        high=np.array([10.5, 11.5, 12.5]),
        low=np.array([8.5, 9.5, 10.5]),
        volume=np.array([100.0, 100.0, 100.0]),
    )
    result = resolve_decision_price(bars, decides_on_bar_close=True)
    np.testing.assert_array_equal(result, [10.0, 11.0, 12.0])


def test_resolve_decision_price_intrabar_quote():
    bars = BarData.from_arrays(
        close=np.array([10.0, 11.0, 12.0]),
        open=np.array([9.0, 10.0, 11.0]),
        high=np.array([10.5, 11.5, 12.5]),
        low=np.array([8.5, 9.5, 10.5]),
        volume=np.array([100.0, 100.0, 100.0]),
    )
    # Scalar quote broadcast
    scalar_res = resolve_decision_price(bars, decides_on_bar_close=False, bid=12.25)
    np.testing.assert_array_equal(scalar_res, [12.25, 12.25, 12.25])

    # Series quote
    series_res = resolve_decision_price(
        bars, decides_on_bar_close=False, bid=[10.1, 11.1, 12.1]
    )
    np.testing.assert_array_equal(series_res, [10.1, 11.1, 12.1])

    # Missing quote raises ValueError
    with pytest.raises(ValueError, match="Intra-bar decision price"):
        resolve_decision_price(bars, decides_on_bar_close=False)

    # Invalid quote price
    with pytest.raises(ValueError, match="positive"):
        resolve_decision_price(bars, decides_on_bar_close=False, bid=-1.0)


# ---------------------------------------------------------------------------
# 2. Profile Signal Binding and Execution
# ---------------------------------------------------------------------------


def test_bind_profile_signals_and_execute_catalog_signals(catalog):
    # Construct 48 intraday hourly bars (2 full days)
    t0 = 1704153600000  # 2024-01-02 00:00:00 UTC (Tuesday)
    timestamps = [t0 + i * 3600000 for i in range(48)]
    bars = sample_intraday_bars(timestamps, base_price=100.0)

    vp = VolumeProfile(
        session_type=1,
        bin_size_mode=1,  # Range binning
        profile_rows=10,
        timestamp_unit="milliseconds",
    )
    bound_bars = bind_profile_signals(bars, volume_profile=vp, threshold=5.0)

    # Check that all external feeds are bound in auxiliary
    expected_feeds = (
        "vp_poc",
        "vp_vah",
        "vp_val",
        "vp_bull_poc",
        "vp_bear_poc",
        "vp_delta",
        "vp_session_vah",
        "vp_session_val",
        "vp_session_open_prices",
        "vp_session_poc_pct_down",
        "vp_session_poc_pct_up",
        "vp_session_threshold",
    )
    for feed in expected_feeds:
        assert feed in bound_bars.auxiliary, f"Missing feed {feed}"
        assert len(bound_bars.auxiliary[feed]) == len(bars.prices)

    # Test catalog signal: VP Price Above POC (composition)
    vp_above = catalog.require("signal.volume_profile.vp_price_above_poc")
    res1 = execute_bound_signal(vp_above, bound_bars, shift=1)
    assert isinstance(res1, (bool, np.bool_))

    # Test catalog signal: VP Bull Above Bear (composition)
    vp_bull = catalog.require("signal.volume_profile.vp_bull_above_bear")
    res2 = execute_bound_signal(vp_bull, bound_bars, shift=1)
    assert isinstance(res2, (bool, np.bool_))

    # Test catalog signal: VP Bottom Heavy POC (specialized signal)
    vp_bottom = catalog.require("signal.volume_profile.vp_bottom_heavy_poc")
    res3 = execute_bound_signal(vp_bottom, bound_bars)
    assert isinstance(res3, (bool, np.bool_))


def test_bind_runtime_inputs_end_to_end_with_psar(catalog):
    t0 = 1704153600000
    timestamps = [t0 + i * 3600000 for i in range(48)]
    bars = sample_intraday_bars(timestamps, base_price=100.0, price_step=0.2)

    # Bind with tick size, decision price, and session profile
    bound_bars = bind_runtime_inputs(
        bars,
        decides_on_bar_close=True,
        tick_size=0.25,
        timezone="UTC",
        volume_profile={
            "session_type": 1,
            "bin_size_mode": 1,
            "profile_rows": 10,
            "timestamp_unit": "milliseconds",
        },
    )
    assert "decision_price" in bound_bars.auxiliary
    assert "vp_poc" in bound_bars.auxiliary

    # Test PSARBarHigher
    psar_higher = catalog.require("signal.parabolic_sar.psar_bar_higher")
    res = execute_bound_signal(psar_higher, bound_bars, step=0.02, maximum=0.2, shift=0)
    assert isinstance(res, (bool, np.bool_))

    # Test PSARBarLower
    psar_lower = catalog.require("signal.parabolic_sar.psar_bar_lower")
    res_low = execute_bound_signal(
        psar_lower, bound_bars, step=0.02, maximum=0.2, shift=0
    )
    assert isinstance(res_low, (bool, np.bool_))
    # Price cannot be both strictly higher and strictly lower than PSAR
    assert not (res and res_low)


# ---------------------------------------------------------------------------
# 3. Qualification of Non-UTC Calendars and DST Transitions
# ---------------------------------------------------------------------------


def test_dst_spring_forward_us_eastern():
    """US Eastern springs forward on Sunday 2024-03-10: 02:00 -> 03:00.

    Before: UTC-5 (EST). After: UTC-4 (EDT).
    """
    zone = ZoneInfo("America/New_York")

    # Friday before DST: 2024-03-08 15:00 UTC (10:00 EST)
    t_fri = int(datetime(2024, 3, 8, 15, 0, tzinfo=UTC).timestamp() * 1000)
    start_fri, end_fri = session_bounds(t_fri, 1, zone)
    # Session start should be midnight EST (05:00 UTC on March 8)
    dt_start_fri = datetime.fromtimestamp(start_fri / 1000, UTC).astimezone(zone)
    assert (
        dt_start_fri.year == 2024 and dt_start_fri.month == 3 and dt_start_fri.day == 8
    )
    assert dt_start_fri.hour == 0 and dt_start_fri.minute == 0

    # Monday after DST: 2024-03-11 15:00 UTC (11:00 EDT)
    t_mon = int(datetime(2024, 3, 11, 15, 0, tzinfo=UTC).timestamp() * 1000)
    start_mon, end_mon = session_bounds(t_mon, 1, zone)
    # Session start should be midnight EDT (04:00 UTC on March 11)
    dt_start_mon = datetime.fromtimestamp(start_mon / 1000, UTC).astimezone(zone)
    assert (
        dt_start_mon.year == 2024 and dt_start_mon.month == 3 and dt_start_mon.day == 11
    )
    assert dt_start_mon.hour == 0 and dt_start_mon.minute == 0


def test_dst_fall_back_us_eastern():
    """US Eastern falls back on Sunday 2024-11-03: 02:00 -> 01:00.

    Before: UTC-4 (EDT). After: UTC-5 (EST).
    """
    zone = ZoneInfo("America/New_York")

    # Friday before fall back: 2024-11-01 15:00 UTC (11:00 EDT)
    t_fri = int(datetime(2024, 11, 1, 15, 0, tzinfo=UTC).timestamp() * 1000)
    start_fri, _ = session_bounds(t_fri, 1, zone)
    dt_start_fri = datetime.fromtimestamp(start_fri / 1000, UTC).astimezone(zone)
    assert dt_start_fri.hour == 0 and dt_start_fri.minute == 0

    # Monday after fall back: 2024-11-04 15:00 UTC (10:00 EST)
    t_mon = int(datetime(2024, 11, 4, 15, 0, tzinfo=UTC).timestamp() * 1000)
    start_mon, _ = session_bounds(t_mon, 1, zone)
    dt_start_mon = datetime.fromtimestamp(start_mon / 1000, UTC).astimezone(zone)
    assert dt_start_mon.hour == 0 and dt_start_mon.minute == 0


def test_dst_uk_europe_london():
    """UK springs forward 2024-03-31 and falls back 2024-10-27."""
    zone = ZoneInfo("Europe/London")

    # Before spring forward: 2024-03-25 (GMT, UTC+0)
    t1 = int(datetime(2024, 3, 25, 12, 0, tzinfo=UTC).timestamp() * 1000)
    start1, _ = session_bounds(t1, 1, zone)
    dt1 = datetime.fromtimestamp(start1 / 1000, UTC).astimezone(zone)
    assert dt1.hour == 0 and dt1.utcoffset().total_seconds() == 0

    # After spring forward: 2024-04-02 (BST, UTC+1)
    t2 = int(datetime(2024, 4, 2, 12, 0, tzinfo=UTC).timestamp() * 1000)
    start2, _ = session_bounds(t2, 1, zone)
    dt2 = datetime.fromtimestamp(start2 / 1000, UTC).astimezone(zone)
    assert dt2.hour == 0 and dt2.utcoffset().total_seconds() == 3600


def test_tokyo_calendar_fixed_offset():
    """Tokyo JST is always UTC+9 without DST."""
    zone = ZoneInfo("Asia/Tokyo")
    t1 = int(datetime(2024, 1, 15, 12, 0, tzinfo=UTC).timestamp() * 1000)
    t2 = int(datetime(2024, 7, 15, 12, 0, tzinfo=UTC).timestamp() * 1000)
    _, _ = session_bounds(t1, 1, zone)
    _, _ = session_bounds(t2, 1, zone)
    start1, end1 = schedule_calendar_session(t1, session_type=1, timezone="Asia/Tokyo")
    start2, end2 = schedule_calendar_session(t2, session_type=1, timezone="Asia/Tokyo")
    assert start1.utcoffset().total_seconds() == 9 * 3600
    assert start2.utcoffset().total_seconds() == 9 * 3600


def test_volume_profile_fixed_ticks_with_instrument_tick_size():
    """Qualify fixed-tick profile calculation with explicit instrument tick size."""
    # 48 hourly bars across 2 calendar days
    t0 = 1704153600000
    timestamps = [t0 + i * 3600000 for i in range(48)]
    # S&P 500 E-mini futures tick size = 0.25
    bars = sample_intraday_bars(timestamps, base_price=4750.0, price_step=0.25)
    vp = VolumeProfile(
        session_type=1,
        bin_size_mode=2,  # Fixed ticks
        tick_size=0.25,
        ticks_per_bin=2,
        profile_rows=20,
        timestamp_unit="milliseconds",
    )
    result = vp.calculate(bars)
    assert "poc" in result
    assert result["poc"].values[-1] > 0
    assert "total_volume" in result
    assert result["total_volume"].values[-1] == 24 * 100.0
