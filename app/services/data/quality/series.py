"""Series-level quality inspection, scoring, and status derivation.

Answers one question: is this *series* trustworthy? Record-level invariants — finite
prices, non-negative volume and spread, ``low <= high``, open/close inside the bar
range, aware UTC timestamps — are enforced fail-closed at contract construction in
``models/records.py`` and are deliberately not repeated here. One rule, one enforcement
point.

Detection is a pure function: ``generated_at`` is supplied by the caller from existing
retrieval evidence, no clock is read, and no I/O is performed. Quality evidence is
always computed from the records examined; a constant or unexamined score is never
emitted.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, QualityIssue
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.quality.scoring import (
    _MAX_SAMPLES,
    _MIN_GAP_RECORDS,
    _fit_samples,
    _issue,
)
from app.utils import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.services.data.contracts.dataset import CanonicalRecord, MarketDataset
    from app.services.data.time_sessions.contracts import SessionWindow

from app.services.data.contracts.dataset import QUALITY_SAMPLE_LIMIT
from app.services.data.quality.anomalies import (
    _detect_runs,
    _detect_spikes,
    _detect_spread_breach,
    detect_unexpected_gaps,
)
from app.services.data.quality.policy import (
    QUALITY_BLOCKING_ISSUES,
    QUALITY_MIN_SCORE,
    QUALITY_SEVERITY_WEIGHTS,
    QualityPolicy,
    get_quality_policy,
)
from app.services.data.time_sessions.timeframes import get_timeframe_spec


def _detect_duplicates(
    records: Sequence[CanonicalRecord], limit: int
) -> QualityIssue | None:
    """Detect repeated timestamps within one bar series."""
    if any(not isinstance(record, OHLCVRecord) for record in records):
        return None
    seen: set[datetime] = set()
    duplicates: list[str] = []
    for record in records:
        if record.timestamp in seen:
            duplicates.append(record.timestamp.isoformat())
        seen.add(record.timestamp)
    if not duplicates:
        return None
    return _issue(
        "DUPLICATE_BARS",
        "critical",
        "Repeated timestamps were observed in the series.",
        len(duplicates),
        duplicates,
        limit,
    )


def _count_weekend_days(start: datetime, end: datetime) -> int:
    """Count the number of Saturday and Sunday days between two datetimes.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        Number of weekend days.
    """
    start_date = start.date()
    end_date = end.date()
    days = (end_date - start_date).days
    weekend_days = 0
    for day_offset in range(1, days):
        current_date = start_date + timedelta(days=day_offset)
        if current_date.weekday() in {5, 6}:
            weekend_days += 1
    return weekend_days


def _detect_gaps(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    policy: QualityPolicy,
    limit: int,
) -> QualityIssue | None:
    """Detect missing bars against the expected timeframe frequency."""
    if timeframe is None or len(records) < _MIN_GAP_RECORDS:
        return None
    try:
        spec = get_timeframe_spec(timeframe)
    except DataError:
        return None
    step = int(spec.duration.total_seconds())
    if step <= 0:
        return None
    missing: list[str] = []
    for previous, current in pairwise(records):
        delta = int((current.timestamp - previous.timestamp).total_seconds())
        if delta <= step:
            continue
        skipped = delta // step - 1
        if timeframe == "D1":
            skipped -= _count_weekend_days(previous.timestamp, current.timestamp)
        if skipped > policy.gap_tolerance:
            missing.append(previous.timestamp.isoformat())
    if not missing:
        return None
    return _issue(
        "MISSING_BARS",
        "critical",
        "Expected bars are absent for the reported timestamps.",
        len(missing),
        missing,
        limit,
    )


def _score(issues: Sequence[QualityIssue], checked: int) -> Decimal:
    """Compute the deterministic quality score from detected issues."""
    if checked <= 0:
        return Decimal(1)
    penalty = Decimal(0)
    for issue in issues:
        weight = QUALITY_SEVERITY_WEIGHTS[issue.severity]
        affected = Decimal(issue.affected_count or 0)
        penalty += weight * affected / Decimal(checked)
    score = Decimal(1) - penalty
    return max(Decimal(0), min(Decimal(1), score))


def _status(
    issues: Sequence[QualityIssue],
    score: Decimal,
    policy: QualityPolicy,
    warnings: Sequence[str],
) -> str:
    """Derive the deterministic quality status."""
    if any(issue.code in QUALITY_BLOCKING_ISSUES for issue in issues):
        return "failed"
    if policy.profile == "strict" and score < QUALITY_MIN_SCORE:
        return "failed"
    if issues or warnings:
        return "passed_with_warnings"
    return "passed"


def inspect_dataset_quality(
    dataset: MarketDataset,
    *,
    policy: QualityPolicy | None = None,
    sessions: Sequence[SessionWindow] | None = None,
    generated_at: datetime | None = None,
) -> DataQualityReport:
    """Produce scored bounded quality evidence for one dataset.

    Args:
        dataset: The normalized dataset to examine.
        policy: Optional explicit thresholds; the configured profile is used when
            omitted.
        sessions: Optional authoritative UTC session windows covering the dataset.
        generated_at: Optional explicit evidence timestamp.

    Returns:
        Bounded quality evidence for the dataset's records.

    Raises:
        DataError: If the policy is malformed or the computed score is invalid.
    """
    return inspect_records_quality(
        dataset.records,
        dataset.timeframe,
        policy=policy,
        sessions=sessions,
        generated_at=(
            generated_at if generated_at is not None else dataset.available_at
        ),
        request_id=dataset.request_id,
    )


def inspect_records_quality(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    *,
    policy: QualityPolicy | None = None,
    sessions: Sequence[SessionWindow] | None = None,
    generated_at: datetime,
    request_id: str | None = None,
) -> DataQualityReport:
    """Produce scored bounded quality evidence for one canonical series.

    The report always reflects the records actually examined. Blocking issues are
    exactly `MISSING_BARS` and `DUPLICATE_BARS`; every other detected issue is
    advisory and reduces the score without failing the series.

    Args:
        records: The canonical records to examine.
        timeframe: Expected bar timeframe, or None for kinds without one.
        policy: Optional explicit thresholds; the configured profile is used when
            omitted.
        sessions: Optional authoritative UTC session windows covering the records.
        generated_at: Explicit evidence timestamp.
        request_id: Optional trace identifier for failure evidence.

    Returns:
        Bounded quality evidence for the supplied records.

    Raises:
        DataError: If the policy is malformed or the computed score is invalid.
    """
    logger.info("Inspecting series quality over %d records", len(records))
    active = policy if policy is not None else get_quality_policy()
    checked = len(records)
    limit = _MAX_SAMPLES

    warnings: list[str] = []
    candidates = [
        _detect_duplicates(records, limit),
        detect_unexpected_gaps(
            records,
            timeframe,
            sessions,
            policy=active,
            limit=limit,
        ),
        _detect_spikes(records, active, limit),
        _detect_runs(
            records,
            "close",
            active.flatline_run,
            "FLAT_LINE",
            "Consecutive identical closes were observed.",
            limit,
            zero_only=False,
        ),
        _detect_runs(
            records,
            "volume",
            active.zero_volume_run,
            "ZERO_VOLUME",
            "Consecutive zero-volume records were observed.",
            limit,
            zero_only=True,
        ),
        _detect_spread_breach(records, active, limit),
    ]
    detected = tuple(issue for issue in candidates if issue is not None)
    issues, truncated = _fit_samples(detected, limit)
    if timeframe is not None and not sessions:
        warnings.append("calendar_unverified")
    if any(
        getattr(record, "spread", None) is not None
        and getattr(record, "spread_unit", None) != getattr(record, "price_unit", None)
        for record in records
    ):
        warnings.append("spread_unit_unverified")

    score = _score(issues, checked)
    if not score.is_finite() or not Decimal(0) <= score <= Decimal(1):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "quality_score"},
            request_id=request_id,
        )
    return DataQualityReport(
        quality_status=_status(issues, score, active, warnings),  # type: ignore[arg-type]
        quality_score=score,
        issues=issues,
        warnings=tuple(warnings),
        record_count=len(records),
        checked_count=checked,
        truncated=truncated,
        sample_limit=limit,
        schema_version="v1",
        generated_at=generated_at,
    )


def detect_timestamp_gaps(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect bars missing against the expected timeframe frequency.

    Session awareness is the caller's concern: when a ``MarketCalendar`` is available,
    ``inspect_dataset_quality`` discounts scheduled closures before reporting. Called
    directly, this reports every gap against raw frequency.

    Args:
        records: Already-normalized records in timestamp order.
        timeframe: Canonical timeframe key. ``None`` disables gap detection, because
            expected frequency is undefined without it.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``MISSING_BARS`` issue, or ``None`` when no gap exceeds tolerance.
    """
    logger.debug("Detecting timestamp gaps")
    return _detect_gaps(records, timeframe, policy or get_quality_policy(), limit)


def validate_tick_order(records: Sequence[CanonicalRecord]) -> bool:
    """Report whether records are in strict non-decreasing timestamp order.

    Returns a boolean rather than raising: ordering is evidence here, and the calling
    workflow owns the fail-closed decision. Retrieval normalization already rejects
    disordered records with ``DATA_QUALITY_FAILED`` before they reach inspection.

    Args:
        records: Records to check.

    Returns:
        ``True`` when timestamps are non-decreasing, ``False`` otherwise.
    """
    logger.debug("Validating tick ordering")
    timestamps = [record.timestamp for record in records]
    return timestamps == sorted(timestamps)


__all__ = [
    "detect_timestamp_gaps",
    "inspect_dataset_quality",
    "inspect_records_quality",
    "validate_tick_order",
]
