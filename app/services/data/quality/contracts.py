"""Typed vocabulary for the quality issues the detectors actually emit.

``CAP-DATA-026`` originally proposed a ten-value flag enum â€” ``MISSING``, ``STALE``,
``PARTIAL``, ``NON_MONOTONIC``, ``INVERTED_BID_ASK``, and so on. None of those values
is produced by any detector. Shipping them would have given consumers a vocabulary of
codes that never appear, and left two lists to keep in sync.

This module formalises the six codes the implementation emits, so the enum is a
faithful view of the evidence rather than an aspiration. Adding a value here without
adding the detector that emits it is a defect, and ``tests/data/unit/test_flags.py``
fails if the enum and the remediation mapping disagree.

Record-level conditions absent from this enum â€” non-finite prices, inverted bid/ask,
negative volume â€” are not missing by oversight. They cannot reach a series at all,
because ``models/records.py`` rejects them fail-closed at construction.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
    run_data_operation,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.data.contracts.dataset import DataQualityReport

__all__ = [
    "QualityFlag",
    "aggregate_flags",
]


class QualityFlag(StrEnum):
    """One detected series-level quality condition.

    Values are the exact issue codes emitted by the detectors, so a flag can be
    compared against a raw ``QualityIssue.code`` without translation.

    Trading Cockpit Phase 0 reconciliation (`TC-IMP-DATA-06`) targeted a
    seven-concept data-integrity taxonomy: stale, gap, duplicate, crossed,
    out-of-order, clock-drift, and primary/backup disagreement. Rechecked
    (rule 9) against the current repository: `MISSING_BARS` (gap) and
    `DUPLICATE_BARS` (duplicate) already existed. A crossed quote (`ask <
    bid`) can never reach a series in the first place — `TickRecord`
    rejects it fail-closed at construction (`contracts/records.py:218`) per
    this module's own stated principle that record-level conditions are
    enforced before construction, not re-detected here — so no
    `CROSSED_QUOTE` series flag exists or is needed. `OUT_OF_ORDER`,
    `CLOCK_DRIFT`, `STALE_QUOTE`, and `SOURCE_DISAGREEMENT` are new,
    each backed by a real detector in `anomalies.py`.

    Attributes:
        MISSING_BARS: Expected bars absent against the timeframe frequency.
        DUPLICATE_BARS: Two records share a timestamp.
        PRICE_SPIKE: A close moved beyond the profile sigma bound.
        FLAT_LINE: Price unchanged across a run longer than the profile allows.
        ZERO_VOLUME: Volume zero across a run longer than the profile allows.
        SPREAD_BREACH: Spread exceeded the profile ceiling.
        OUT_OF_ORDER: A record's timestamp preceded the immediately prior record.
        CLOCK_DRIFT: A record's receive time drifted from its own event time.
        STALE_QUOTE: The newest record's receive time exceeded the maximum age.
        SOURCE_DISAGREEMENT: Primary and backup sources disagreed beyond tolerance.
    """

    MISSING_BARS = "MISSING_BARS"
    DUPLICATE_BARS = "DUPLICATE_BARS"
    PRICE_SPIKE = "PRICE_SPIKE"
    FLAT_LINE = "FLAT_LINE"
    ZERO_VOLUME = "ZERO_VOLUME"
    SPREAD_BREACH = "SPREAD_BREACH"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CLOCK_DRIFT = "CLOCK_DRIFT"
    STALE_QUOTE = "STALE_QUOTE"
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"


def _aggregate_flags_raw(report: DataQualityReport) -> tuple[QualityFlag, ...]:
    """Compile distinct quality flags present in one report without wrapping.

    Raises:
        DataError: With code ``VALIDATION_FAILED`` if the report carries an issue code
            that no detector emits.
    """
    logger.debug("Aggregating quality flags from a report")
    present: set[QualityFlag] = set()
    for issue in report.issues:
        try:
            present.add(QualityFlag(issue.code))
        except ValueError as error:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"issue_code": issue.code, "reason": "unknown_flag"},
            ) from error
    return tuple(flag for flag in QualityFlag if flag in present)


def aggregate_flags(
    report: DataQualityReport,
) -> StandardResponse[tuple[QualityFlag, ...]]:
    """Compile the distinct quality flags present in one report.

    Flags are returned in the enum's declaration order rather than the order issues
    happen to appear, so the result is deterministic for a given set of conditions and
    two reports with the same problems compare equal.

    Args:
        report: Quality evidence produced by series inspection.

    Returns:
        Standard response carrying distinct flags present in the report, in declaration
        order. Empty when the series is clean.

    Raises:
        (in-band) ``VALIDATION_FAILED`` if the report carries an issue code that no
            detector emits. That means evidence and vocabulary have diverged, which is
            a defect rather than an unknown-but-tolerable condition.
    """
    return run_data_operation(
        operation="data.quality.aggregate_flags",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=lambda: _aggregate_flags_raw(report),
    )
