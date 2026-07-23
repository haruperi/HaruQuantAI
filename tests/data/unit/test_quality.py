"""Unit coverage for series-level quality detection, scoring, and remediation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.services.data.contracts import DataError, OHLCVRecord, TickRecord
from app.services.data.quality import (
    get_quality_policy,
    inspect_records_quality,
    summarize_quality_remediation,
)
from app.services.data.quality.policy import QUALITY_PROFILE_THRESHOLDS
from app.services.data.time_sessions.contracts import SessionWindow

_START = datetime(2026, 1, 1, tzinfo=UTC)
_GENERATED = datetime(2026, 1, 2, tzinfo=UTC)
_STANDARD = QUALITY_PROFILE_THRESHOLDS["standard"]
_STRICT = QUALITY_PROFILE_THRESHOLDS["strict"]


def _bar(
    index: int,
    *,
    close: str = "10.0",
    volume: str = "100",
    spread: str | None = None,
    minutes: int | None = None,
) -> OHLCVRecord:
    """Return one canonical bar with explicit series position and values."""
    offset = index if minutes is None else minutes
    timestamp = _START + timedelta(minutes=offset)
    return OHLCVRecord(
        timestamp=timestamp,
        open=Decimal(close),
        high=Decimal(close) + Decimal("0.5"),
        low=Decimal(close) - Decimal("0.5"),
        close=Decimal(close),
        volume=Decimal(volume),
        spread=None if spread is None else Decimal(spread),
        spread_unit=None if spread is None else "USD",
        price_unit="USD",
        volume_unit="lots",
        source="fixture",
        source_symbol="ABC",
        source_revision="rev-1",
        available_at=timestamp + timedelta(seconds=1),
    )


def _inspect(records: tuple[OHLCVRecord, ...], *, policy=_STANDARD):
    """Inspect one bar series under an explicit policy."""
    return inspect_records_quality(
        records,
        "M1",
        policy=policy,
        generated_at=_GENERATED,
    )


def test_clean_series_scores_one() -> None:
    """A series with no detected issue scores exactly one."""
    records = tuple(
        _bar(index, close=str(10 + index), volume=str(100 + index))
        for index in range(8)
    )

    report = _inspect(records)

    assert report.quality_score == Decimal(1)
    assert not any(issue.code == "MISSING_BARS" for issue in report.issues)


def test_gap_detection_reports_missing_bars() -> None:
    """A hole wider than the tolerance is a blocking missing-bar issue."""
    records = (
        _bar(0, close="10"),
        _bar(1, close="11", minutes=1),
        _bar(2, close="12", minutes=20),
    )

    report = _inspect(records)

    codes = {issue.code for issue in report.issues}
    assert "MISSING_BARS" in codes
    assert report.quality_status == "failed"


def test_gap_detection_discounts_weekend_closure() -> None:
    """A Saturday-to-Monday closure is not missing H1 data."""
    friday = datetime(2026, 1, 2, 23, 0, tzinfo=UTC)
    monday = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
    records = (
        _bar(0, close="10").model_copy(
            update={"timestamp": friday, "available_at": friday}
        ),
        _bar(1, close="11").model_copy(
            update={"timestamp": monday, "available_at": monday}
        ),
    )

    report = inspect_records_quality(
        records,
        "H1",
        policy=_STANDARD,
        generated_at=_GENERATED,
    )

    assert "MISSING_BARS" not in {issue.code for issue in report.issues}
    assert "calendar_unverified" in report.warnings


def test_gap_detection_discounts_declared_session_break() -> None:
    """An injected closed interval is not reported as missing data."""
    monday = datetime(2026, 1, 5, 9, 0, tzinfo=UTC)
    noon = monday + timedelta(hours=3)
    records = (
        _bar(0, close="10").model_copy(
            update={"timestamp": monday, "available_at": monday}
        ),
        _bar(1, close="11").model_copy(
            update={"timestamp": noon, "available_at": noon}
        ),
    )
    sessions = (
        SessionWindow(
            label="morning",
            opens_at=monday,
            closes_at=monday + timedelta(hours=1),
        ),
        SessionWindow(
            label="afternoon",
            opens_at=noon,
            closes_at=noon + timedelta(hours=1),
        ),
    )

    report = inspect_records_quality(
        records,
        "H1",
        policy=_STANDARD,
        sessions=sessions,
        generated_at=_GENERATED,
    )

    assert "MISSING_BARS" not in {issue.code for issue in report.issues}
    assert "calendar_unverified" not in report.warnings


def test_duplicate_timestamps_are_blocking() -> None:
    """Repeated timestamps fail the series rather than reducing the score only."""
    records = (
        _bar(0, close="10"),
        _bar(0, close="11"),
        _bar(1, close="12", minutes=1),
    )

    report = _inspect(records)

    codes = {issue.code for issue in report.issues}
    assert "DUPLICATE_BARS" in codes
    assert report.quality_status == "failed"


def test_duplicate_tick_timestamps_are_not_duplicate_bars() -> None:
    """Distinct ticks may share one provider timestamp."""
    ticks = tuple(
        TickRecord(
            timestamp=_START,
            source="fixture",
            source_symbol="ABC",
            available_at=_START,
            bid=Decimal(10) + Decimal(index) / Decimal(100),
            price_unit="USD",
        )
        for index in range(2)
    )

    report = inspect_records_quality(
        ticks,
        None,
        policy=_STANDARD,
        generated_at=_GENERATED,
    )

    assert "DUPLICATE_BARS" not in {issue.code for issue in report.issues}


def test_flatline_run_is_reported() -> None:
    """A run of identical closes is advisory evidence, not a failure."""
    records = tuple(
        _bar(index, close="10.0", volume=str(100 + index)) for index in range(8)
    )

    report = _inspect(records)

    codes = {issue.code for issue in report.issues}
    assert "FLAT_LINE" in codes
    assert report.quality_status == "passed_with_warnings"


def test_zero_volume_run_is_reported() -> None:
    """Consecutive zero-volume records are advisory evidence."""
    records = tuple(
        _bar(index, close=str(10 + index), volume="0") for index in range(8)
    )

    report = _inspect(records)

    assert "ZERO_VOLUME" in {issue.code for issue in report.issues}


def test_spread_breach_is_reported() -> None:
    """Spreads beyond the ceiling are advisory evidence."""
    records = tuple(
        _bar(index, close=str(10 + index), spread="5.0") for index in range(4)
    )

    report = _inspect(records)

    assert "SPREAD_BREACH" in {issue.code for issue in report.issues}


def test_incomparable_spread_unit_is_disclosed_not_compared() -> None:
    """Provider points are not compared with a price-unit ceiling."""
    records = tuple(
        _bar(index, close=str(10 + index), spread="5.0").model_copy(
            update={"spread_unit": "points"}
        )
        for index in range(4)
    )

    report = _inspect(records)

    assert "SPREAD_BREACH" not in {issue.code for issue in report.issues}
    assert "spread_unit_unverified" in report.warnings


def test_score_is_never_constant_across_differing_inputs() -> None:
    """Differing series must not produce identical evidence."""
    clean = tuple(
        _bar(index, close=str(10 + index), volume=str(100 + index))
        for index in range(8)
    )
    degraded = tuple(
        _bar(index, close=str(10 + index), volume="0", spread="9.0")
        for index in range(8)
    )

    clean_report = _inspect(clean)
    degraded_report = _inspect(degraded)

    assert clean_report.quality_score != degraded_report.quality_score
    assert degraded_report.quality_score < clean_report.quality_score


def test_score_reflects_issue_severity() -> None:
    """A blocking critical issue costs more than an advisory warning."""
    warning_only = tuple(
        _bar(index, close="10.0", volume=str(100 + index)) for index in range(8)
    )
    blocking = (
        _bar(0, close="10"),
        _bar(1, close="11", minutes=1),
        _bar(2, close="12", minutes=30),
    )

    assert _inspect(blocking).quality_score < _inspect(warning_only).quality_score


def test_issue_samples_respect_limit() -> None:
    """Samples stay bounded and truncation is disclosed."""
    records = tuple(_bar(index, close="10.0", volume="0") for index in range(40))

    report = _inspect(records)

    for issue in report.issues:
        assert len(issue.samples) <= report.sample_limit


def test_strict_profile_fails_below_minimum_score() -> None:
    """Strict deployments treat a low score as a failure."""
    records = tuple(
        _bar(index, close="10.0", volume="0", spread="9.0") for index in range(8)
    )

    report = _inspect(records, policy=_STRICT)

    assert report.quality_status == "failed"


def test_remediation_is_deterministic() -> None:
    """Every detected code maps to one stable recommended action."""
    records = (
        _bar(0, close="10"),
        _bar(1, close="11", minutes=1),
        _bar(2, close="12", minutes=30),
    )
    report = _inspect(records)

    first = summarize_quality_remediation(report)
    second = summarize_quality_remediation(report)

    assert first == second
    assert "MISSING_BARS" in first


def test_remediation_does_not_mutate_report() -> None:
    """Remediation is evidence only and never performs the repair."""
    records = tuple(_bar(index, close="10.0", volume="0") for index in range(8))
    report = _inspect(records)
    before = report.model_dump_json()

    summarize_quality_remediation(report)

    assert report.model_dump_json() == before


def test_unknown_issue_code_is_rejected() -> None:
    """An unmapped code fails rather than inventing an action."""
    from app.services.data.contracts import (
        DataQualityReport,
        QualityIssue,
    )

    report = DataQualityReport(
        quality_status="passed_with_warnings",
        quality_score=Decimal("0.5"),
        issues=(
            QualityIssue(
                code="UNMAPPED_CODE",
                severity="warning",
                message="synthetic",
                affected_count=1,
            ),
        ),
        record_count=1,
        checked_count=1,
        truncated=False,
        sample_limit=1,
        schema_version="v1",
        generated_at=_GENERATED,
    )

    with pytest.raises(DataError):
        summarize_quality_remediation(report)


def test_active_policy_is_resolved_from_settings() -> None:
    """The configured profile selects one frozen threshold set."""
    policy = get_quality_policy()

    assert policy.profile in QUALITY_PROFILE_THRESHOLDS
