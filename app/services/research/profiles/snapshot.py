"""Canonical versioned profile snapshot and summaries for Research."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.services.research.contracts import ResearchProfileSnapshot
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from app.services.research.contracts import ResearchScorecard

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_MAX_DASHBOARD_REASONS = 5


def build_research_profile_snapshot(
    *,
    stages: Mapping[str, JSONValue],
    scorecard: ResearchScorecard,
    dataset_hash: str,
    configuration_hash: str,
) -> ResearchProfileSnapshot:
    """Normalize approved stage outputs into one versioned snapshot.

    Args:
        stages: Approved stage evidence, each carrying ``schema_version``.
        scorecard: Canonical advisory scorecard.
        dataset_hash: Lowercase SHA-256 of the dataset identity.
        configuration_hash: Lowercase SHA-256 of the configuration.

    Returns:
        Validated ``ResearchProfileSnapshot``.

    Raises:
        ValueError: If any stage is unversioned or hashes are invalid.
    """
    logger.info("Building Research profile snapshot")
    if not stages:
        raise ValueError("RES_INPUT_INVALID", "EMPTY_SNAPSHOT_STAGES")
    for value in stages.values():
        if not isinstance(value, Mapping) or "schema_version" not in value:
            raise ValueError("RES_INPUT_INVALID", "UNVERSIONED_SNAPSHOT_STAGE")
    return ResearchProfileSnapshot(
        "v1",
        dict(stages),
        scorecard,
        dataset_hash,
        configuration_hash,
        datetime.now(UTC),
        scorecard.warnings,
        True,
    )


def build_profile_summary(
    snapshot: ResearchProfileSnapshot,
) -> Mapping[str, JSONValue]:
    """Return a concise observation/uncertainty/readiness summary.

    Args:
        snapshot: Canonical profile snapshot.

    Returns:
        Versioned summary preserving warning count and readiness.

    Raises:
        ValueError: If the snapshot is invalid.
    """
    logger.debug("Building Research profile summary")
    return {
        "schema_version": "v1",
        "readiness": snapshot.scorecard.readiness,
        "final_score": snapshot.scorecard.final_score,
        "warning_count": len(snapshot.warnings),
        "stage_count": len(snapshot.stages),
        "advisory_only": True,
    }


def build_dashboard_summary(
    snapshot: ResearchProfileSnapshot,
) -> Mapping[str, JSONValue]:
    """Return a bounded UI-ready block without presentation-side calculation.

    Args:
        snapshot: Canonical profile snapshot.

    Returns:
        Bounded dashboard block with verdict, score, and top reasons.

    Raises:
        ValueError: If the snapshot is invalid or oversized.
    """
    logger.debug("Building Research dashboard summary")
    reasons: list[JSONValue] = [
        str(reason) for reason in snapshot.scorecard.reasons[:_MAX_DASHBOARD_REASONS]
    ]
    stage_names: list[JSONValue] = [str(name) for name in snapshot.stages]
    return {
        "schema_version": "v1",
        "readiness": snapshot.scorecard.readiness,
        "final_score": snapshot.scorecard.final_score,
        "top_reasons": reasons,
        "stage_names": stage_names,
        "advisory_only": True,
    }


__all__ = (
    "build_dashboard_summary",
    "build_profile_summary",
    "build_research_profile_snapshot",
)
