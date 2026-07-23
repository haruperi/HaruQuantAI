"""Versioned confirmation and symbol classification for Research."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from app.utils import ValidationError, logger

if TYPE_CHECKING:
    from app.services.research.contracts import EdgeResult

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def classify_symbol(
    mean_reversion: EdgeResult,
    trend_persistence: EdgeResult,
    *,
    policy_version: str,
) -> Mapping[str, JSONValue]:
    """Classify two advisory edges under the single v1 truth table.

    Args:
        mean_reversion: Mean-reversion evidence.
        trend_persistence: Trend-persistence evidence.
        policy_version: Required confirmation policy version.

    Returns:
        Advisory classification with uncertainty preserved.

    Raises:
        ValidationError: If versions or study identities are incompatible.
    """
    logger.info("Classifying Research symbol evidence")
    if policy_version != "v1":
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "CONFIRMATION_POLICY_NOT_V1")
    if mean_reversion.schema_version != trend_persistence.schema_version:
        raise ValidationError("RES_VERSION_INCOMPATIBLE", "EDGE_SCHEMA_MISMATCH")
    confirmed = {
        "mean_reversion": mean_reversion.classification == "confirmed",
        "trend_persistence": trend_persistence.classification == "confirmed",
    }
    if confirmed["mean_reversion"] and confirmed["trend_persistence"]:
        classification = "mixed"
    elif confirmed["mean_reversion"]:
        classification = "mean_reversion"
    elif confirmed["trend_persistence"]:
        classification = "trend_persistence"
    else:
        classification = "inconclusive"
    return {
        "schema_version": "v1",
        "policy_version": policy_version,
        "classification": classification,
        "confirmed": confirmed,
        "advisory_only": True,
    }


__all__ = ("classify_symbol",)
