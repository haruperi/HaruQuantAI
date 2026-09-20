"""Tests for FEAT-DATA-RESAMPLING (app/services/data/resampling.py)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.contracts.data import (
    DATA_RESAMPLING,
    BarRecord,
    ResamplingError,
    SessionDefinition,
    SessionWindow,
    TickRecord,
    TimezoneError,
)
from app.kernel.bootstrapper import Runtime
from app.services.data.resampling import (
    SPEC,
    ResamplingConfig,
    ResamplingFeature,
    ResamplingServiceImpl,
    feature,
)


def _setup_resampling() -> ResamplingServiceImpl:
    return ResamplingServiceImpl(config=ResamplingConfig(default_spread=0.0001))


def test_resample_m1_to_m5_bars() -> None:
    """Verify aggregating M1 bars into M5 bars with volume conservation."""
    svc = _setup_resampling()
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    # 10 1-minute bars spanning two 5-minute buckets: [10:00 - 10:05), [10:05 - 10:10)
    bars: list[BarRecord] = []
    for i in range(10):
        bars.append(
            BarRecord(
                timestamp=base_time + timedelta(minutes=i),
                open=1.0500 + i * 0.0001,
                high=1.0505 + i * 0.0001,
                low=1.0495 + i * 0.0001,
                close=1.0502 + i * 0.0001,
                volume=10.0,
            )
        )

    resampled = svc.resample_bars(bars, target_timeframe="M5")
    assert len(resampled) == 2

    # First M5 bucket: 10:00:00
    b1 = resampled[0]
    assert b1.timestamp == datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    assert b1.open == pytest.approx(1.0500)
    assert b1.close == pytest.approx(1.0502 + 4 * 0.0001)
    assert b1.volume == pytest.approx(50.0)  # 5 bars * 10 vol

    # Second M5 bucket: 10:05:00
    b2 = resampled[1]
    assert b2.timestamp == datetime(2026, 6, 1, 10, 5, 0, tzinfo=UTC)
    assert b2.open == pytest.approx(1.0500 + 5 * 0.0001)
    assert b2.volume == pytest.approx(50.0)

    # Total volume conserved
    assert sum(b.volume for b in resampled) == sum(b.volume for b in bars)


def test_resample_ticks_to_bars() -> None:
    """Verify aggregating raw ticks into 1-minute time bars."""
    svc = _setup_resampling()
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    ticks = [
        TickRecord(
            timestamp=base_time + timedelta(seconds=10),
            bid=1.0500,
            ask=1.0501,
            sequence=1,
            bid_volume=1.0,
            ask_volume=1.0,
        ),
        TickRecord(
            timestamp=base_time + timedelta(seconds=25),
            bid=1.0520,
            ask=1.0521,
            sequence=2,
            bid_volume=2.0,
            ask_volume=2.0,
        ),
        TickRecord(
            timestamp=base_time + timedelta(seconds=40),
            bid=1.0490,
            ask=1.0491,
            sequence=3,
            bid_volume=3.0,
            ask_volume=3.0,
        ),
        TickRecord(
            timestamp=base_time + timedelta(seconds=55),
            bid=1.0510,
            ask=1.0511,
            sequence=4,
            bid_volume=4.0,
            ask_volume=4.0,
        ),
    ]

    bars = svc.resample_ticks_to_bars(ticks, target_timeframe="M1")
    assert len(bars) == 1
    bar = bars[0]
    assert bar.timestamp == base_time
    assert bar.open == pytest.approx(1.0500)
    assert bar.high == pytest.approx(1.0520)
    assert bar.low == pytest.approx(1.0490)
    assert bar.close == pytest.approx(1.0510)
    assert bar.volume == pytest.approx(20.0)


def test_4price_ticks_generation() -> None:
    """Verify 4-price intrabar ticks path for bullish and bearish bars."""
    svc = _setup_resampling()
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)

    # Bullish bar (close > open): Open -> Low -> High -> Close
    bull_bar = BarRecord(
        timestamp=base_time,
        open=1.0500,
        high=1.0550,
        low=1.0480,
        close=1.0530,
        volume=100.0,
    )
    bull_ticks = svc.generate_4price_ticks(bull_bar)
    assert len(bull_ticks) == 4
    assert bull_ticks[0].bid == pytest.approx(1.0500)  # Open
    assert bull_ticks[1].bid == pytest.approx(1.0480)  # Low
    assert bull_ticks[2].bid == pytest.approx(1.0550)  # High
    assert bull_ticks[3].bid == pytest.approx(1.0530)  # Close

    # Bearish bar (close < open): Open -> High -> Low -> Close
    bear_bar = BarRecord(
        timestamp=base_time,
        open=1.0530,
        high=1.0550,
        low=1.0480,
        close=1.0500,
        volume=100.0,
    )
    bear_ticks = svc.generate_4price_ticks(bear_bar)
    assert len(bear_ticks) == 4
    assert bear_ticks[0].bid == pytest.approx(1.0530)  # Open
    assert bear_ticks[1].bid == pytest.approx(1.0550)  # High
    assert bear_ticks[2].bid == pytest.approx(1.0480)  # Low
    assert bear_ticks[3].bid == pytest.approx(1.0500)  # Close


def test_clone_to_timezone() -> None:
    """Verify timezone translation of bar records."""
    svc = _setup_resampling()
    base_time = datetime(2026, 6, 1, 14, 0, 0, tzinfo=UTC)  # 14:00 UTC

    bars = [
        BarRecord(
            timestamp=base_time,
            open=1.0500,
            high=1.0510,
            low=1.0490,
            close=1.0505,
            volume=50.0,
        )
    ]
    cloned = svc.clone_to_timezone(bars, target_timezone="America/New_York")
    assert len(cloned) == 1
    # 14:00 UTC is 10:00 EDT in June (UTC-4)
    assert cloned[0].timestamp.hour == 10
    assert cloned[0].open == pytest.approx(1.0500)
    assert cloned[0].close == pytest.approx(1.0505)


def test_resampling_empty_inputs() -> None:
    """Verify empty input sequences return empty results."""
    svc = _setup_resampling()
    assert svc.resample_bars([], target_timeframe="M5") == []
    assert svc.resample_ticks_to_bars([], target_timeframe="M1") == []


def test_resampling_custom_timeframes() -> None:
    """Verify parsing non-standard timeframes: M2, H2, D2, S30."""
    svc = _setup_resampling()
    base_time = datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC)
    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500,
            high=1.0510,
            low=1.0490,
            close=1.0505,
            volume=10.0,
        )
        for i in range(4)
    ]
    # M2
    res_m2 = svc.resample_bars(bars, target_timeframe="M2")
    assert len(res_m2) == 2
    # H2
    res_h2 = svc.resample_bars(bars, target_timeframe="H2")
    assert len(res_h2) == 1
    # D2
    res_d2 = svc.resample_bars(bars, target_timeframe="D2")
    assert len(res_d2) == 1
    # S30
    res_s30 = svc.resample_bars(bars, target_timeframe="S30")
    assert len(res_s30) == 4


def test_resampling_invalid_timeframe() -> None:
    """Verify invalid timeframe raises ResamplingError."""
    svc = _setup_resampling()
    bars = [
        BarRecord(
            timestamp=datetime(2026, 6, 1, 10, 0, 0, tzinfo=UTC),
            open=1.05,
            high=1.06,
            low=1.04,
            close=1.05,
        )
    ]
    with pytest.raises(ResamplingError, match="Unsupported or invalid timeframe"):
        svc.resample_bars(bars, target_timeframe="INVALID_TF")


def test_resampling_session_offset() -> None:
    """Verify resampling with session window offset."""
    svc = _setup_resampling()
    session = SessionDefinition(
        name="US_Equities",
        windows=[SessionWindow(day_of_week=0, open_time="09:30", close_time="16:00")],
    )
    base_time = datetime(2026, 6, 1, 9, 30, 0, tzinfo=UTC)
    bars = [
        BarRecord(
            timestamp=base_time + timedelta(minutes=i),
            open=1.0500,
            high=1.0510,
            low=1.0490,
            close=1.0505,
            volume=10.0,
        )
        for i in range(10)
    ]
    res = svc.resample_bars(bars, target_timeframe="M5", session=session)
    assert len(res) == 2

    ticks = [
        TickRecord(
            timestamp=base_time + timedelta(seconds=15),
            bid=1.0500,
            ask=1.0501,
        )
    ]
    res_ticks = svc.resample_ticks_to_bars(
        ticks, target_timeframe="M1", session=session
    )
    assert len(res_ticks) == 1


def test_clone_to_timezone_errors_and_naive() -> None:
    """Verify invalid timezone error and naive timestamp handling."""
    svc = _setup_resampling()
    bar = BarRecord(
        timestamp=datetime(2026, 6, 1, 10, 0, 0, tzinfo=None),  # noqa: DTZ001
        open=1.05,
        high=1.06,
        low=1.04,
        close=1.05,
    )
    cloned = svc.clone_to_timezone([bar], target_timezone="UTC")
    assert len(cloned) == 1
    assert cloned[0].timestamp.tzinfo is not None

    with pytest.raises(TimezoneError, match="Unknown target timezone"):
        svc.clone_to_timezone([bar], target_timezone="NonExistent/Timezone")


@pytest.mark.anyio
async def test_resampling_feature_lifecycle() -> None:
    """Verify runtime composition and capability registration."""
    runtime = Runtime([ResamplingFeature])
    async with runtime:
        svc = runtime.require(DATA_RESAMPLING)
        assert isinstance(svc, ResamplingServiceImpl)


def test_resampling_factory() -> None:
    """Verify feature factory and SPEC."""
    feat = feature()
    assert isinstance(feat, ResamplingFeature)
    assert feat.spec == SPEC
