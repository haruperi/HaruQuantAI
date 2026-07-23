"""Quality profiles, thresholds, and deterministic remediation mapping.

The threshold sets are frozen module-level constants rather than configuration.
``QUALITY_PROFILE`` selects one of three named profiles; individual thresholds are
deliberately not separately tunable, so a deployment cannot quietly weaken detection
one bound at a time.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Final, NamedTuple

from app.services.data._settings import get_data_settings
from app.services.data.contracts import DataError
from app.utils import logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.data.contracts.dataset import DataQualityReport


class QualityPolicy(NamedTuple):
    """One frozen threshold set selected by `QUALITY_PROFILE`."""

    profile: str
    spike_sigma: Decimal
    flatline_run: int
    zero_volume_run: int
    spread_ceiling: Decimal
    gap_tolerance: int


QUALITY_PROFILE_THRESHOLDS: Final[Mapping[str, QualityPolicy]] = {
    "strict": QualityPolicy("strict", Decimal(6), 3, 3, Decimal("0.005"), 0),
    "standard": QualityPolicy("standard", Decimal(8), 5, 5, Decimal("0.01"), 1),
    "lenient": QualityPolicy("lenient", Decimal(12), 10, 10, Decimal("0.05"), 3),
}

QUALITY_BLOCKING_ISSUES: Final[frozenset[str]] = frozenset(
    {"MISSING_BARS", "DUPLICATE_BARS"}
)

QUALITY_MIN_SCORE: Final[Decimal] = Decimal("0.90")

QUALITY_SEVERITY_WEIGHTS: Final[Mapping[str, Decimal]] = {
    "info": Decimal(0),
    "warning": Decimal("0.25"),
    "error": Decimal("0.5"),
    "critical": Decimal(1),
}

QUALITY_REMEDIATION: Final[Mapping[str, str]] = {
    "MISSING_BARS": "Backfill the reported range from an approved source.",
    "DUPLICATE_BARS": "Re-ingest the range and deduplicate on the exact timestamp.",
    "PRICE_SPIKE": "Verify the reported bars against a second approved source.",
    "FLAT_LINE": "Confirm the venue was open and the feed was live for the run.",
    "ZERO_VOLUME": "Confirm the venue was open and the feed reported real volume.",
    "SPREAD_BREACH": "Review venue conditions before using the range for costing.",
}

_MAX_SAMPLES: Final = 10
_MIN_SPIKE_RECORDS: Final = 3
_MIN_GAP_RECORDS: Final = 2


def get_quality_policy() -> QualityPolicy:
    """Return the active immutable quality thresholds.

    Returns:
        The frozen policy named by `QUALITY_PROFILE`.

    Raises:
        DataError: If the configured profile is not recognized.
    """
    logger.debug("Resolving the active DATA quality profile")
    profile = getattr(get_data_settings(), "quality_profile", "standard")
    policy = QUALITY_PROFILE_THRESHOLDS.get(str(profile))
    if policy is None:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "QUALITY_PROFILE"})
    return policy


def summarize_quality_remediation(report: DataQualityReport) -> Mapping[str, str]:
    """Map each detected issue code to its recommended remediation action.

    The dataset is neither mutated nor remediated; this returns evidence only.

    Args:
        report: The quality evidence to summarize.

    Returns:
        An ordered mapping of issue code to recommended action.

    Raises:
        DataError: If the report carries an unknown issue code.
    """
    logger.debug("Summarizing quality remediation evidence")
    summary: dict[str, str] = {}
    for issue in report.issues:
        action = QUALITY_REMEDIATION.get(issue.code)
        if action is None:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "issue_code"},
            )
        summary[issue.code] = action
    return summary


__all__ = [
    "QUALITY_BLOCKING_ISSUES",
    "QUALITY_MIN_SCORE",
    "QUALITY_PROFILE_THRESHOLDS",
    "QUALITY_REMEDIATION",
    "QUALITY_SEVERITY_WEIGHTS",
    "QualityPolicy",
    "get_quality_policy",
    "summarize_quality_remediation",
]
