"""Verify quality analysis boundaries and explicit semantics."""

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from app.workspace.DataManager.Data.contracts import BarRecord, Dataset, TickRecord
from app.workspace.DataManager.Data.quality_analysis import (
    ProblemKind,
    SessionHours,
    analyze_quality,
)

HOURS = SessionHours(0, 23)


def bars(dataset: Dataset, records: Sequence[BarRecord]) -> Dataset:
    return replace(dataset, records=tuple(records))


def test_empty_and_normal_bars(dataset):
    result = analyze_quality(
        bars(dataset, ()), interval_ms=60_000, session_hours=HOURS
    ).unwrap()
    assert result.total_count == 0 and result.problems == () and result.gap_percent == 0
    assert (
        analyze_quality(dataset, interval_ms=60_000, session_hours=HOURS)
        .unwrap()
        .problems
        == ()
    )


@pytest.mark.parametrize("prior", [29, 30, 31])
def test_spike_warmup_and_exact_threshold(dataset, prior):
    records = [BarRecord(i * 60_000, 9.5, 10, 9, 9.5) for i in range(prior)]
    records.append(BarRecord(prior * 60_000, 10, 14, 9, 10))
    result = analyze_quality(
        bars(dataset, records), interval_ms=60_000, session_hours=HOURS
    ).unwrap()
    assert result.spike_count == (0 if prior < 30 else 1)


def test_precedence_and_three_decimal_percentage(dataset):
    records = (
        BarRecord(0, 10, 9, 11, 10),
        BarRecord(60_000, 10, 9, 8, 10),
        BarRecord(180_000, 10, 9, 11, 10),
    )
    result = analyze_quality(
        bars(dataset, records), interval_ms=60_000, session_hours=HOURS
    ).unwrap()
    assert [problem.kind for problem in result.problems] == [
        ProblemKind.LOW,
        ProblemKind.HIGH,
        ProblemKind.GAP,
    ]
    assert result.gap_percent == 33.333 and result.ohlc_percent == 66.666
    assert (result.problems[2].gap_from_ms, result.problems[2].gap_to_ms) == (
        120_000,
        120_000,
    )


def test_zero_ranges_and_bad_bar_update_history(dataset):
    flat = tuple(BarRecord(i * 60_000, 1, 1, 1, 1) for i in range(31))
    assert (
        analyze_quality(bars(dataset, flat), interval_ms=60_000, session_hours=HOURS)
        .unwrap()
        .spike_count
        == 1
    )
    records = [BarRecord(i * 60_000, 9.5, 10, 9, 9.5) for i in range(29)]
    records += [
        BarRecord(29 * 60_000, 20, 10, 9, 20),
        BarRecord(30 * 60_000, 10, 14, 9, 10),
    ]
    result = analyze_quality(
        bars(dataset, records), interval_ms=60_000, session_hours=HOURS
    ).unwrap()
    assert result.problems[-1].kind == ProblemKind.SPIKE


def ms(day: int, hour: int) -> int:
    return int(datetime(2024, 1, day, hour, tzinfo=UTC).timestamp() * 1000)


def test_cross_day_hours_and_sunday_exclusion(dataset):
    hours = SessionHours(9, 17)
    pairs = [
        ((ms(1, 16), ms(2, 9)), 1),
        ((ms(1, 17), ms(2, 10)), 1),
        ((ms(1, 17), ms(2, 9)), 0),
        ((ms(6, 12), ms(7, 12)), 0),
        ((ms(7, 12), ms(8, 9)), 0),
    ]
    for times, count in pairs:
        records = tuple(BarRecord(time, 10, 11, 9, 10) for time in times)
        result = analyze_quality(
            bars(dataset, records), interval_ms=3_600_000, session_hours=hours
        ).unwrap()
        assert result.gap_count == count


def test_invalid_quality_options(dataset):
    ticks = replace(dataset, timeframe="TICK", records=(TickRecord(0, 1, 2),))
    assert (
        analyze_quality(ticks, interval_ms=1, session_hours=HOURS).error_code
        == "UNSUPPORTED_TIMEFRAME"
    )
    for value in [0, -1, True]:
        assert (
            analyze_quality(dataset, interval_ms=value, session_hours=HOURS).error_code
            == "INVALID_INTERVAL"
        )
    assert (
        analyze_quality(
            dataset, interval_ms=1, session_hours=SessionHours(-1, 23)
        ).error_code
        == "INVALID_SESSION"
    )
    assert (
        analyze_quality(
            dataset, interval_ms=1, session_hours=SessionHours(23, 9)
        ).error_code
        == "UNSUPPORTED_OVERNIGHT_SESSION"
    )
    huge = bars(dataset, (BarRecord(0, 1, 1e308, -1e308, 1),))
    assert (
        analyze_quality(huge, interval_ms=1, session_hours=HOURS).error_code
        == "INVALID_RANGE"
    )


def test_session_gap_bounds_do_not_invert(dataset):
    records = tuple(BarRecord(time, 10, 11, 9, 10) for time in (ms(1, 16), ms(2, 9)))
    result = analyze_quality(
        bars(dataset, records), interval_ms=7_200_000, session_hours=SessionHours(9, 17)
    ).unwrap()
    assert result.problems == ()


def test_local_timestamp_overflow_is_explicit(dataset):
    edge = replace(
        dataset,
        timezone="Asia/Kolkata",
        records=(
            BarRecord(253_402_300_799_998, 1, 2, 0, 1),
            BarRecord(253_402_300_799_999, 1, 2, 0, 1),
        ),
    )
    assert (
        analyze_quality(edge, interval_ms=1, session_hours=HOURS).error_code
        == "INVALID_TIMESTAMP"
    )
