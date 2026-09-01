"""Series-level quality inspection, scoring, and status derivation.

Answers one question: is this *series* trustworthy? Record-level invariants â€” finite
prices, non-negative volume and spread, ``low <= high``, open/close inside the bar
range, aware UTC timestamps â€” are enforced fail-closed at contract construction in
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

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.contracts.dataset import DataQualityReport, QualityIssue
from app.services.data.contracts.records import OHLCVRecord
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.services.data.integrity.scoring import (
    _MAX_SAMPLES,
    _MIN_GAP_RECORDS,
    _fit_samples,
    _issue,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.services.data.contracts.dataset import CanonicalRecord, MarketDataset
    from app.services.data.time_sessions.contracts import SessionWindow

from app.services.data.contracts.dataset import QUALITY_SAMPLE_LIMIT
from app.services.data.integrity.anomalies import (
    _detect_gap_issues,
    _detect_runs,
    _detect_spikes,
    _detect_spread_breach,
)
from app.services.data.integrity.policy import (
    QUALITY_BLOCKING_ISSUES,
    QUALITY_MIN_SCORE,
    QUALITY_SEVERITY_WEIGHTS,
    QualityPolicy,
    _get_quality_policy_raw,
)
from app.services.data.time_sessions.timeframes import (
    _get_timeframe_spec_raw as get_timeframe_spec,
)

logger = get_logger(__name__)


def _detect_duplicates(
    records: Sequence[CanonicalRecord], limit: int
) -> QualityIssue | None:
    """Detect repeated timestamps within one bar series.

    Args:
        records: The ``records`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Detect missing bars against the expected timeframe frequency.

    Args:
        records: The ``records`` argument.
        timeframe: The ``timeframe`` argument.
        policy: The ``policy`` argument.
        limit: The ``limit`` argument.

    Returns:
        The result produced by the operation.
    """
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
    """Compute the deterministic quality score from detected issues.

    Args:
        issues: The ``issues`` argument.
        checked: The ``checked`` argument.

    Returns:
        The result produced by the operation.
    """
    if checked <= 0:
        return Decimal(0)
    penalty = Decimal(0)
    for issue in issues:
        weight = QUALITY_SEVERITY_WEIGHTS[issue.severity]
        affected = Decimal(issue.affected_count or 0)
        penalty += weight * affected / Decimal(checked)
    score = Decimal(100) * (Decimal(1) - penalty)
    bounded = max(Decimal(0), min(Decimal(100), score))
    return bounded.quantize(Decimal("0.01"))


def _status(score: Decimal, checked: int) -> str:
    """Derive the deterministic percentage grade.

    Args:
        score: The ``score`` argument.
        checked: The ``checked`` argument.

    Returns:
        The result produced by the operation.
    """
    if checked == 0:
        return "not_checked"
    if score == Decimal(100):
        return "perfect"
    boundaries = (
        (Decimal(95), "excellent"),
        (QUALITY_MIN_SCORE, "good"),
        (Decimal(80), "degraded"),
        (Decimal(60), "poor"),
    )
    for minimum, status in boundaries:
        if score >= minimum:
            return status
    return "critical"


def _decision(
    issues: Sequence[QualityIssue],
    status: str,
    warnings: Sequence[str],
) -> str:
    """Derive the fail-closed operational quality decision.

    Args:
        issues: The ``issues`` argument.
        status: The ``status`` argument.
        warnings: The ``warnings`` argument.

    Returns:
        The result produced by the operation.
    """
    if status == "not_checked":
        return "not_evaluated"
    if any(issue.code in QUALITY_BLOCKING_ISSUES for issue in issues):
        return "rejected"
    if status in {"poor", "critical"}:
        return "rejected"
    if status == "degraded":
        return "review_required"
    if issues or warnings:
        return "accepted_with_warnings"
    return "accepted"


def inspect_dataset_quality(
    dataset: MarketDataset,
    *,
    policy: QualityPolicy | None = None,
    sessions: Sequence[SessionWindow] | None = None,
    calendar_closures: Sequence[object] = (),
    generated_at: datetime | None = None,
) -> StandardResponse[DataQualityReport]:
    """Produce scored bounded quality evidence for one dataset.

    Args:
        dataset: The normalized dataset to examine.
        policy: Optional explicit thresholds; the configured profile is used when
            omitted.
        sessions: Optional authoritative UTC session windows covering the dataset.
        calendar_closures: Relevant persisted research-only holiday evidence.
        generated_at: Optional explicit evidence timestamp.

    Returns:
        Standard response carrying bounded quality evidence for the dataset's records.

    Raises:
        (in-band) ``VALIDATION_FAILED`` if the policy is malformed or the score invalid.
    """
    return run_data_operation(
        operation="data.quality.inspect_dataset_quality",
        request_id=dataset.request_id,
        start_time=data_start_time(),
        raw=lambda: _inspect_records_quality_raw(
            dataset.records,
            dataset.timeframe,
            policy=policy,
            sessions=sessions,
            calendar_closures=calendar_closures,
            generated_at=(
                generated_at if generated_at is not None else dataset.available_at
            ),
            request_id=dataset.request_id,
        ),
    )


def _inspect_records_quality_raw(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    *,
    policy: QualityPolicy | None = None,
    sessions: Sequence[SessionWindow] | None = None,
    calendar_closures: Sequence[object] = (),
    generated_at: datetime,
    request_id: str | None = None,
) -> DataQualityReport:
    """Produce scored bounded quality evidence without response wrapping.

    Args:
        records: The ``records`` argument.
        timeframe: The ``timeframe`` argument.
        policy: The ``policy`` argument.
        sessions: The ``sessions`` argument.
        calendar_closures: Relevant persisted research-only holiday evidence.
        generated_at: The ``generated_at`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the policy is malformed or the computed score is invalid.
    """
    logger.info("Inspecting series quality over %d records", len(records))
    active = policy if policy is not None else _get_quality_policy_raw()
    checked = len(records)
    limit = _MAX_SAMPLES

    warnings: list[str] = []
    gap_issues = _detect_gap_issues(
        records,
        timeframe,
        sessions,
        calendar_closures,  # type: ignore[arg-type]
        policy=active,
        limit=limit,
    )
    candidates = [
        _detect_duplicates(records, limit),
        *gap_issues,
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
    if gap_issues and any(
        issue.code == "CALENDAR_SUPPORTED_CLOSURE" for issue in gap_issues
    ):
        warnings.append(
            "holiday_closure_supported_by_economic_calendar_not_broker_schedule"
        )
    if any(
        getattr(record, "spread", None) is not None
        and getattr(record, "spread_unit", None) != getattr(record, "price_unit", None)
        for record in records
    ):
        warnings.append("spread_unit_unverified")

    score = _score(issues, checked)
    if not score.is_finite() or not Decimal(0) <= score <= Decimal(100):
        raise DataError(
            "VALIDATION_FAILED",
            safe_details={"field": "quality_score"},
            request_id=request_id,
        )
    status = _status(score, checked)
    return DataQualityReport(
        quality_status=status,  # type: ignore[arg-type]
        quality_decision=_decision(issues, status, warnings),  # type: ignore[arg-type]
        quality_score=score,
        issues=issues,
        warnings=tuple(warnings),
        record_count=len(records),
        checked_count=checked,
        truncated=truncated,
        sample_limit=limit,
        schema_version="v2",
        generated_at=generated_at,
    )


def inspect_records_quality(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    *,
    policy: QualityPolicy | None = None,
    sessions: Sequence[SessionWindow] | None = None,
    generated_at: datetime,
    request_id: str | None = None,
) -> StandardResponse[DataQualityReport]:
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
        Standard response carrying bounded quality evidence for the supplied records.

    Raises:
        (in-band) ``VALIDATION_FAILED`` if the policy is malformed or the score invalid.
    """
    return run_data_operation(
        operation="data.quality.inspect_records_quality",
        request_id=request_id,
        start_time=data_start_time(),
        raw=lambda: _inspect_records_quality_raw(
            records,
            timeframe,
            policy=policy,
            sessions=sessions,
            generated_at=generated_at,
            request_id=request_id,
        ),
    )


def detect_timestamp_gaps(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> StandardResponse[QualityIssue | None]:
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
        Standard response carrying one ``MISSING_BARS`` issue, or ``None`` when no gap
        exceeds tolerance.
    """
    return run_data_operation(
        operation="data.quality.detect_timestamp_gaps",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _detect_gaps(
            records, timeframe, policy or _get_quality_policy_raw(), limit
        ),
    )


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
