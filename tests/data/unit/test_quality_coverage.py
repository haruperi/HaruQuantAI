"""Unit tests for quality/contracts.py and quality/series.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.data.contracts import DataQualityReport, QualityIssue
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.quality.contracts import QualityFlag, aggregate_flags
from app.services.data.quality.policy import get_quality_policy
from app.services.data.quality.series import (
    _count_weekend_days,
    _detect_duplicates,
    _detect_gaps,
    _status,
    validate_tick_order,
)

_NOW = datetime.now(UTC)


def _unwrap(response: object) -> object:
    """Unwrap a successful Data standard response to its raw payload."""
    return unwrap_data_response(
        response,  # type: ignore[arg-type]
        operation="data.quality.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_aggregate_flags_success_and_unknown_flag() -> None:
    """Test aggregate_flags with valid issues and unknown issue code."""
    issue_missing = QualityIssue(
        code="MISSING_BARS",
        severity="critical",
        message="Missing bars",
        samples=("2026-01-01T00:00:00Z",),
    )
    issue_spike = QualityIssue(
        code="PRICE_SPIKE",
        severity="warning",
        message="Spike detected",
        samples=("2026-01-01T01:00:00Z",),
    )
    report = DataQualityReport(
        quality_status="passed_with_warnings",
        quality_score=Decimal("0.9"),
        issues=(issue_spike, issue_missing),
        warnings=(),
        record_count=10,
        checked_count=10,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=_NOW,
    )

    flags = _unwrap(aggregate_flags(report))
    assert flags == (QualityFlag.MISSING_BARS, QualityFlag.PRICE_SPIKE)

    # Unknown issue code raises DataError VALIDATION_FAILED
    unknown_issue = QualityIssue(
        code="UNKNOWN_BARS",
        severity="critical",
        message="Unknown issue",
        samples=(),
    )
    report_unknown = DataQualityReport(
        quality_status="failed",
        quality_score=Decimal("0.0"),
        issues=(unknown_issue,),
        warnings=(),
        record_count=10,
        checked_count=10,
        truncated=False,
        sample_limit=100,
        schema_version="v1",
        generated_at=_NOW,
    )
    # Unknown issue code now surfaces as an in-band error response.
    response = aggregate_flags(report_unknown)
    assert response.status == "error"
    assert response.error is not None
    assert response.error.code == "VALIDATION_FAILED"


def test_count_weekend_days() -> None:
    """Test weekend day counter between dates."""
    # Friday to Monday -> Sat, Sun = 2 weekend days
    friday = datetime(2026, 1, 2, tzinfo=UTC)  # Friday
    monday = datetime(2026, 1, 5, tzinfo=UTC)  # Monday
    assert _count_weekend_days(friday, monday) == 2

    # Monday to Wednesday -> 0 weekend days
    wednesday = datetime(2026, 1, 7, tzinfo=UTC)
    assert _count_weekend_days(monday, wednesday) == 0


def test_detect_duplicates_non_ohlcv() -> None:
    """Test _detect_duplicates ignores non-OHLCV records."""
    non_ohlcv = MagicMock()  # Not OHLCVRecord
    assert _detect_duplicates((non_ohlcv,), limit=10) is None


def test_detect_gaps_edge_cases() -> None:
    """Test _detect_gaps with invalid timeframe, short records, D1 timeframe."""
    policy = _unwrap(get_quality_policy())

    # Invalid timeframe returns None
    rec1 = MagicMock()
    rec1.timestamp = _NOW
    rec2 = MagicMock()
    rec2.timestamp = _NOW + timedelta(minutes=5)
    assert (
        _detect_gaps((rec1, rec2), timeframe="INVALID_TF", policy=policy, limit=10)
        is None
    )

    # D1 timeframe with weekend discount
    fri = MagicMock()
    fri.timestamp = datetime(2026, 1, 2, tzinfo=UTC)
    mon = MagicMock()
    mon.timestamp = datetime(2026, 1, 5, tzinfo=UTC)
    # Skipping Sat & Sun on D1 -> 0 missing bars
    assert _detect_gaps((fri, mon), timeframe="D1", policy=policy, limit=10) is None


def test_status_strict_policy_score_failure() -> None:
    """Test _status fails when strict policy score is below minimum."""
    policy = MagicMock()
    policy.profile = "strict"
    # Low score < QUALITY_MIN_SCORE (0.8)
    status = _status(issues=(), score=Decimal("0.5"), policy=policy, warnings=())
    assert status == "failed"


def test_validate_tick_order() -> None:
    """Test validate_tick_order for ordered and unordered records."""
    r1 = MagicMock()
    r1.timestamp = _NOW
    r2 = MagicMock()
    r2.timestamp = _NOW + timedelta(seconds=1)
    r3 = MagicMock()
    r3.timestamp = _NOW - timedelta(seconds=1)

    assert validate_tick_order((r1, r2)) is True
    assert validate_tick_order((r1, r3)) is False
