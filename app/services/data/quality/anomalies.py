"""Statistical anomaly detection over an already-normalized series.

Detects what no single record can reveal: price spikes beyond the profile sigma bound,
flat-line runs, zero-volume runs, and spread-threshold breaches. Every detector is a
pure function returning evidence; none mutates, repairs, drops, or interpolates a
record, and none decides a workflow outcome.

Promoted from private helpers in ``validation/quality.py`` by ``CAP-DATA-026``. The
flat-line and zero-volume detectors share one pass internally, because they scan the
same runs.
"""

from __future__ import annotations

from decimal import Decimal
from itertools import pairwise
from typing import TYPE_CHECKING

from app.services.data.contracts.dataset import QualityIssue
from app.services.data.quality.scoring import (
    _MIN_SPIKE_RECORDS,
    _issue,
)
from app.utils import logger

if TYPE_CHECKING:
    from collections.abc import Sequence

    from app.services.data.contracts.dataset import CanonicalRecord
    from app.services.data.time_sessions.contracts import SessionWindow

from app.services.data.contracts.dataset import QUALITY_SAMPLE_LIMIT
from app.services.data.quality.policy import QualityPolicy, get_quality_policy
from app.services.data.time_sessions.gaps import GapType, classify_gap
from app.services.data.time_sessions.timeframes import get_timeframe_spec


def _closes(records: Sequence[CanonicalRecord]) -> list[Decimal] | None:
    """Return close prices when the series carries them."""
    closes: list[Decimal] = []
    for record in records:
        close = getattr(record, "close", None)
        if close is None:
            return None
        closes.append(Decimal(close))
    return closes


def _detect_spikes(
    records: Sequence[CanonicalRecord], policy: QualityPolicy, limit: int
) -> QualityIssue | None:
    """Detect returns beyond the profile sigma bound."""
    closes = _closes(records)
    if closes is None or len(closes) < _MIN_SPIKE_RECORDS:
        return None
    changes = [
        abs(later - earlier) / earlier if earlier != 0 else Decimal(0)
        for earlier, later in pairwise(closes)
    ]
    if not changes:
        return None
    mean = sum(changes) / Decimal(len(changes))
    variance = sum((value - mean) ** 2 for value in changes) / Decimal(len(changes))
    sigma = variance.sqrt()
    if sigma == 0:
        return None
    bound = mean + policy.spike_sigma * sigma
    spikes = [
        records[index + 1].timestamp.isoformat()
        for index, value in enumerate(changes)
        if value > bound
    ]
    if not spikes:
        return None
    return _issue(
        "PRICE_SPIKE",
        "warning",
        "Price changes exceeded the configured sigma bound.",
        len(spikes),
        spikes,
        limit,
    )


def _detect_runs(
    records: Sequence[CanonicalRecord],
    attribute: str,
    run_length: int,
    code: str,
    message: str,
    limit: int,
    *,
    zero_only: bool,
) -> QualityIssue | None:
    """Detect consecutive identical or zero values of one attribute."""
    if run_length <= 0 or not records:
        return None
    starts: list[str] = []
    run = 1
    for previous, current in pairwise(records):
        earlier = getattr(previous, attribute, None)
        later = getattr(current, attribute, None)
        if earlier is None or later is None:
            run = 1
            continue
        matched = (
            (Decimal(earlier) == 0 and Decimal(later) == 0)
            if zero_only
            else Decimal(earlier) == Decimal(later)
        )
        if matched:
            run += 1
            if run == run_length:
                starts.append(current.timestamp.isoformat())
        else:
            run = 1
    if not starts:
        return None
    return _issue(code, "warning", message, len(starts), starts, limit)


def _detect_spread_breach(
    records: Sequence[CanonicalRecord], policy: QualityPolicy, limit: int
) -> QualityIssue | None:
    """Detect comparable price-unit spreads beyond the configured ceiling."""
    breaches: list[str] = []
    for record in records:
        spread = getattr(record, "spread", None)
        spread_unit = getattr(record, "spread_unit", None)
        price_unit = getattr(record, "price_unit", None)
        if (
            spread is not None
            and spread_unit is not None
            and spread_unit == price_unit
            and Decimal(spread) > policy.spread_ceiling
        ):
            breaches.append(record.timestamp.isoformat())
    if not breaches:
        return None
    return _issue(
        "SPREAD_BREACH",
        "warning",
        "Observed spreads exceeded the configured ceiling.",
        len(breaches),
        breaches,
        limit,
    )


# Gap classifications that a declared calendar already explains.
_EXPECTED_GAPS = frozenset({GapType.EXPECTED_WEEKEND, GapType.EXPECTED_SESSION_BREAK})
# A gap needs two observations to exist at all.
_MIN_GAP_PAIR = 2


def detect_price_jumps(
    records: Sequence[CanonicalRecord],
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect closes that moved beyond the profile's sigma bound.

    Args:
        records: Already-normalized records in timestamp order.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``PRICE_SPIKE`` issue, or ``None`` when no close breaches the bound.
    """
    logger.debug("Detecting price jumps")
    return _detect_spikes(records, policy or get_quality_policy(), limit)


def detect_flatline_periods(
    records: Sequence[CanonicalRecord],
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect runs of unchanged closing price longer than the profile allows.

    Args:
        records: Already-normalized records in timestamp order.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``FLAT_LINE`` issue, or ``None`` when no run exceeds the threshold.
    """
    logger.debug("Detecting flat-line periods")
    active = policy or get_quality_policy()
    return _detect_runs(
        records,
        "close",
        active.flatline_run,
        "FLAT_LINE",
        "Consecutive identical closes were observed.",
        limit,
        zero_only=False,
    )


def detect_zero_volume_bars(
    records: Sequence[CanonicalRecord],
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect runs of zero-volume records longer than the profile allows.

    Shares ``_detect_runs`` with flat-line detection: both scan for a run of an
    unchanging attribute, and separating them into two passes would double the scan
    without changing the result.

    Args:
        records: Already-normalized records in timestamp order.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``ZERO_VOLUME`` issue, or ``None`` when no run exceeds the threshold.
    """
    logger.debug("Detecting zero-volume runs")
    active = policy or get_quality_policy()
    return _detect_runs(
        records,
        "volume",
        active.zero_volume_run,
        "ZERO_VOLUME",
        "Consecutive zero-volume records were observed.",
        limit,
        zero_only=True,
    )


def detect_extreme_spread_widening(
    records: Sequence[CanonicalRecord],
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect spreads beyond the profile ceiling.

    Args:
        records: Already-normalized records in timestamp order.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``SPREAD_BREACH`` issue, or ``None`` when every spread is within bounds.
    """
    logger.debug("Detecting extreme spread widening")
    return _detect_spread_breach(records, policy or get_quality_policy(), limit)


def detect_unexpected_gaps(
    records: Sequence[CanonicalRecord],
    timeframe: str | None,
    sessions: Sequence[SessionWindow] | None = None,
    *,
    policy: QualityPolicy | None = None,
    limit: int = QUALITY_SAMPLE_LIMIT,
) -> QualityIssue | None:
    """Detect missing bars that a declared session break does not explain.

    ``detect_timestamp_gaps`` reports every gap against raw timeframe frequency, which
    means a weekend looks identical to an outage. This narrows that to the gaps that
    need explaining, by classifying each against the supplied session windows and
    discarding the ones that fall in a declared non-trading window.

    When no session evidence is supplied, an interval containing only Saturday and
    Sunday is still a known weekend closure. Every other gap classifies as
    ``UNVERIFIED`` and is reported. That is deliberate: an unexplained weekday gap is
    not the same as a benign one.

    Args:
        records: Already-normalized records in timestamp order.
        timeframe: Canonical timeframe key. ``None`` disables detection entirely,
            because expected frequency is undefined without it.
        sessions: Declared session windows covering the period. ``None`` still
            discounts weekend-only intervals but reports other gaps as unverified.
        policy: Threshold profile to apply. Defaults to the active configured profile.
        limit: Maximum number of bounded samples to attach to the issue.

    Returns:
        One ``MISSING_BARS`` issue covering only the unexplained gaps, or ``None`` when
        every gap is accounted for by a session break or weekend.
    """
    logger.debug("Detecting unexpected gaps against declared sessions")
    active = policy or get_quality_policy()
    if timeframe is None or len(records) < _MIN_GAP_PAIR:
        return None
    spec = get_timeframe_spec(timeframe)

    unexplained: list[str] = []
    for earlier, later in pairwise(records):
        expected_next = earlier.timestamp + spec.duration
        if later.timestamp <= expected_next:
            continue
        skipped = int((later.timestamp - earlier.timestamp) // spec.duration) - 1
        if skipped <= active.gap_tolerance:
            continue
        if classify_gap(expected_next, later.timestamp, sessions) in _EXPECTED_GAPS:
            continue
        unexplained.append(
            f"{expected_next.isoformat()}..{later.timestamp.isoformat()}"
        )

    if not unexplained:
        return None
    return _issue(
        "MISSING_BARS",
        "critical",
        "Missing bars were observed outside any declared session break.",
        len(unexplained),
        tuple(unexplained),
        limit,
    )


__all__ = [
    "detect_extreme_spread_widening",
    "detect_flatline_periods",
    "detect_price_jumps",
    "detect_unexpected_gaps",
    "detect_zero_volume_bars",
]
