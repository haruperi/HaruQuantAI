"""Guards for gap classification and session-aware gap detection.

Both are new in Phase 6, so there is nothing to compare against — these tests pin
intended behaviour rather than prove a move was faithful.

The property that matters most: an unexplained gap and a gap nobody has explained are
different things. Suppressing gaps because no calendar was supplied would hide real
outages behind missing configuration, so absent session evidence reports rather than
silences.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.time_sessions.contracts import SessionWindow
from app.services.data.time_sessions.gaps import GapType, classify_gap

# 2024-01-05 is a Friday; 2024-01-06 and 07 are the weekend.
FRIDAY = datetime(2024, 1, 5, 20, 0, tzinfo=UTC)
MONDAY = datetime(2024, 1, 8, 8, 0, tzinfo=UTC)
SATURDAY = datetime(2024, 1, 6, 12, 0, tzinfo=UTC)
SUNDAY = datetime(2024, 1, 7, 12, 0, tzinfo=UTC)

REQUEST_ID = "req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _session(open_at: datetime, close_at: datetime) -> SessionWindow:
    """Build one declared session window.

    Args:
        open_at: Session open, aware UTC.
        close_at: Session close, aware UTC.

    Returns:
        One validated ``SessionWindow``.
    """
    return SessionWindow(label="regular", opens_at=open_at, closes_at=close_at)


def test_a_gap_wholly_inside_the_weekend_is_expected() -> None:
    """Assert a weekend gap classifies as expected without session evidence.

    Raises:
        AssertionError: If a weekend gap is reported as anomalous.
    """
    assert classify_gap(SATURDAY, SUNDAY) is GapType.EXPECTED_WEEKEND


def test_weekend_gap_may_end_exactly_when_monday_starts() -> None:
    """Assert the half-open weekend excludes its Monday endpoint."""
    monday_midnight = datetime(2024, 1, 8, tzinfo=UTC)

    assert classify_gap(SATURDAY, monday_midnight) is GapType.EXPECTED_WEEKEND


def test_weekend_gap_extending_into_monday_is_not_expected_without_sessions() -> None:
    """Assert Monday missing time is not hidden as a weekend closure."""
    monday_one = datetime(2024, 1, 8, 1, 0, tzinfo=UTC)

    assert classify_gap(SATURDAY, monday_one) is GapType.UNVERIFIED


def test_a_gap_without_session_evidence_is_unverified_not_expected() -> None:
    """Assert missing session evidence yields ``UNVERIFIED`` rather than ``EXPECTED``.

    This is the distinction the module exists to preserve: a gap nobody has explained
    must not be presented as a gap known to be benign.

    Raises:
        AssertionError: If an unexplained weekday gap is treated as expected.
    """
    monday_noon = datetime(2024, 1, 8, 12, 0, tzinfo=UTC)
    monday_two = datetime(2024, 1, 8, 14, 0, tzinfo=UTC)
    assert classify_gap(monday_noon, monday_two) is GapType.UNVERIFIED


def test_a_gap_inside_an_open_session_is_unexpected() -> None:
    """Assert a gap during declared trading hours is anomalous.

    Raises:
        AssertionError: If a gap inside an open session is excused.
    """
    sessions = (_session(MONDAY, MONDAY + timedelta(hours=8)),)
    inside = MONDAY + timedelta(hours=2)
    assert classify_gap(inside, inside + timedelta(minutes=30), sessions) is (
        GapType.UNEXPECTED
    )


def test_a_gap_outside_every_session_is_an_expected_break() -> None:
    """Assert a gap between sessions is explained by the calendar.

    Raises:
        AssertionError: If a declared break is reported as anomalous.
    """
    sessions = (_session(MONDAY, MONDAY + timedelta(hours=4)),)
    after_close = MONDAY + timedelta(hours=5)
    assert classify_gap(after_close, after_close + timedelta(hours=1), sessions) is (
        GapType.EXPECTED_SESSION_BREAK
    )


def test_a_non_advancing_gap_is_rejected() -> None:
    """Assert an end at or before the start is invalid input.

    Raises:
        AssertionError: If a degenerate interval is silently accepted.
    """
    with pytest.raises(ValueError, match="gap_end must follow gap_start"):
        classify_gap(MONDAY, MONDAY)


def _bar(moment: datetime) -> OHLCVRecord:
    """Build one canonical bar at an exact timestamp.

    Args:
        moment: Aware UTC timestamp.

    Returns:
        One validated ``OHLCVRecord``.
    """
    return OHLCVRecord(
        timestamp=moment,
        open=Decimal("1.1000"),
        high=Decimal("1.1010"),
        low=Decimal("1.0990"),
        close=Decimal("1.1005"),
        volume=Decimal(100),
        price_unit="USD",
        volume_unit="shares",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=moment,
    )


def test_detect_unexpected_gaps_ignores_a_declared_session_break() -> None:
    """Assert a gap explained by the calendar is not reported.

    Raises:
        AssertionError: If a declared break is reported as missing bars.
    """
    from app.services.data.quality.anomalies import detect_unexpected_gaps

    base = datetime(2024, 1, 8, 9, 0, tzinfo=UTC)
    records = (
        _bar(base),
        _bar(base + timedelta(minutes=1)),
        # Two-hour hole that the declared session break covers.
        _bar(base + timedelta(hours=2)),
        _bar(base + timedelta(hours=2, minutes=1)),
    )
    sessions = (
        _session(base, base + timedelta(minutes=2)),
        _session(base + timedelta(hours=2), base + timedelta(hours=3)),
    )
    assert detect_unexpected_gaps(records, "M1", sessions) is None


def test_detect_unexpected_gaps_reports_a_gap_during_open_hours() -> None:
    """Assert a gap inside a declared session is reported.

    Raises:
        AssertionError: If an anomalous gap is missed.
    """
    from app.services.data.quality.anomalies import detect_unexpected_gaps

    base = datetime(2024, 1, 8, 9, 0, tzinfo=UTC)
    records = (
        _bar(base),
        _bar(base + timedelta(minutes=1)),
        _bar(base + timedelta(minutes=30)),
    )
    sessions = (_session(base, base + timedelta(hours=8)),)
    issue = detect_unexpected_gaps(records, "M1", sessions)
    assert issue is not None
    assert issue.code == "MISSING_BARS"


def test_detect_unexpected_gaps_needs_a_timeframe() -> None:
    """Assert detection is disabled when expected frequency is undefined.

    Raises:
        AssertionError: If gaps are reported without a timeframe.
    """
    from app.services.data.quality.anomalies import detect_unexpected_gaps

    base = datetime(2024, 1, 8, 9, 0, tzinfo=UTC)
    records = (_bar(base), _bar(base + timedelta(minutes=30)))
    assert detect_unexpected_gaps(records, None) is None
