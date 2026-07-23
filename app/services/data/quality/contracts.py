"""Typed vocabulary for the quality issues the detectors actually emit.

``CAP-DATA-026`` originally proposed a ten-value flag enum — ``MISSING``, ``STALE``,
``PARTIAL``, ``NON_MONOTONIC``, ``INVERTED_BID_ASK``, and so on. None of those values
is produced by any detector. Shipping them would have given consumers a vocabulary of
codes that never appear, and left two lists to keep in sync.

This module formalises the six codes the implementation emits, so the enum is a
faithful view of the evidence rather than an aspiration. Adding a value here without
adding the detector that emits it is a defect, and ``tests/data/unit/test_flags.py``
fails if the enum and the remediation mapping disagree.

Record-level conditions absent from this enum — non-finite prices, inverted bid/ask,
negative volume — are not missing by oversight. They cannot reach a series at all,
because ``models/records.py`` rejects them fail-closed at construction.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from app.services.data.contracts import DataError
from app.utils import logger

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

    Attributes:
        MISSING_BARS: Expected bars absent against the timeframe frequency.
        DUPLICATE_BARS: Two records share a timestamp.
        PRICE_SPIKE: A close moved beyond the profile sigma bound.
        FLAT_LINE: Price unchanged across a run longer than the profile allows.
        ZERO_VOLUME: Volume zero across a run longer than the profile allows.
        SPREAD_BREACH: Spread exceeded the profile ceiling.
    """

    MISSING_BARS = "MISSING_BARS"
    DUPLICATE_BARS = "DUPLICATE_BARS"
    PRICE_SPIKE = "PRICE_SPIKE"
    FLAT_LINE = "FLAT_LINE"
    ZERO_VOLUME = "ZERO_VOLUME"
    SPREAD_BREACH = "SPREAD_BREACH"


def aggregate_flags(report: DataQualityReport) -> tuple[QualityFlag, ...]:
    """Compile the distinct quality flags present in one report.

    Flags are returned in the enum's declaration order rather than the order issues
    happen to appear, so the result is deterministic for a given set of conditions and
    two reports with the same problems compare equal.

    Args:
        report: Quality evidence produced by series inspection.

    Returns:
        Distinct flags present in the report, in declaration order. Empty when the
        series is clean.

    Raises:
        DataError: With code ``VALIDATION_FAILED`` if the report carries an issue code
            that no detector emits. That means evidence and vocabulary have diverged,
            which is a defect rather than an unknown-but-tolerable condition.
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
