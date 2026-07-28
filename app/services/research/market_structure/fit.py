"""Advisory strategy-archetype fit from market-structure evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from app.services.research.contracts import MarketStructureProfile

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)


def build_strategy_fit(
    profile: MarketStructureProfile,
) -> Mapping[str, JSONValue]:
    """Rank advisory strategy archetypes from profile evidence.

    This function never mutates or approves Strategy, Risk, or Trading state.

    Args:
        profile: Canonical market-structure profile.

    Returns:
        Advisory archetype ranking with advisory_only=True.

    Raises:
        ValueError: If the profile is malformed or insufficient.
    """
    logger.info("Building Research advisory strategy fit")
    verdict = profile.verdict
    score = profile.score
    if score < 0.0:
        raise ValueError("RES_INPUT_INVALID", "INVALID_PROFILE_SCORE")
    if verdict == "trending":
        ranking = ("trend_follow", "breakout", "range")
    elif verdict == "ranging":
        ranking = ("mean_revert", "range", "trend_follow")
    else:
        ranking = ("range", "mean_revert", "trend_follow")
    return {
        "schema_version": "v1",
        "verdict": verdict,
        "score": score,
        "archetype_ranking": list(ranking),
        "primary_archetype": ranking[0],
        "advisory_only": True,
    }


__all__ = ("build_strategy_fit",)
