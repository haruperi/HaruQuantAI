"""Deterministic ranking and Pareto selection."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from app.services.optimization.scoring.contracts import (
    CandidateScore,
    ObjectiveDirection,
)
from app.utils import logger


def _ranking_value(candidate: CandidateScore) -> float:
    """Project a score to a descending utility value.

    Args:
        candidate: Available candidate score.

    Returns:
        Direction-normalized ranking value.

    Raises:
        ValueError: If the candidate is unavailable.
    """
    logger.debug("Projecting Optimization score ranking value")
    if candidate.value is None:
        raise ValueError("available ranking requires a score value")
    return (
        candidate.value
        if candidate.direction is ObjectiveDirection.MAXIMIZE
        else -candidate.value
    )


def rank_candidates(candidates: Sequence[CandidateScore]) -> tuple[CandidateScore, ...]:
    """Rank available candidates with canonical tie breakers.

    Args:
        candidates: Candidate scores for one objective.

    Returns:
        New deterministically ordered candidate tuple.

    Raises:
        ValueError: If objectives differ or available evidence is invalid.
    """
    logger.info("Ranking Optimization candidates deterministically")
    available = tuple(item for item in candidates if item.available)
    if not available:
        return ()
    identities = {(item.objective, item.direction) for item in available}
    if len(identities) != 1:
        raise ValueError("candidate ranking requires one objective and direction")
    return tuple(
        sorted(
            available,
            key=lambda item: (
                -_ranking_value(item),
                -(item.trade_count if item.trade_count is not None else -1),
                item.candidate_hash,
            ),
        )
    )


def select_pareto_candidates(
    candidates: Sequence[Mapping[str, float]], objectives: Sequence[str]
) -> tuple[int, ...]:
    """Select the deterministic non-dominated candidate indices.

    Args:
        candidates: Objective mappings in source order.
        objectives: Non-empty Analytics objective keys.

    Returns:
        Source indices belonging to the Pareto front.

    Raises:
        ValueError: If objectives or values are missing or non-finite.
    """
    logger.info("Selecting Optimization Pareto candidates")
    if not objectives or len(set(objectives)) != len(objectives):
        raise ValueError("Pareto objectives must be non-empty and unique")
    minimize = {"max_drawdown"}
    projected: list[tuple[float, ...]] = []
    for candidate in candidates:
        if any(name not in candidate for name in objectives):
            raise ValueError("Pareto candidate is missing an objective")
        values = tuple(float(candidate[name]) for name in objectives)
        if any(not math.isfinite(value) for value in values):
            raise ValueError("Pareto objective values must be finite")
        projected.append(
            tuple(
                -value if name in minimize else value
                for name, value in zip(objectives, values, strict=True)
            )
        )
    selected: list[int] = []
    for index, values in enumerate(projected):
        dominated = any(
            other_index != index
            and all(left >= right for left, right in zip(other, values, strict=True))
            and any(left > right for left, right in zip(other, values, strict=True))
            for other_index, other in enumerate(projected)
        )
        if not dominated:
            selected.append(index)
    return tuple(selected)


__all__ = ["rank_candidates", "select_pareto_candidates"]
