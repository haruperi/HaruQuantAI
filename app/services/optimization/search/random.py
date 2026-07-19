"""Seeded random sampling over a bounded discrete parameter space."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import TYPE_CHECKING

from app.services.optimization.search.grid import iter_grid_candidates
from app.utils import logger

if TYPE_CHECKING:
    from app.services.optimization.parameters import ParameterSpace, ParameterValue


def sample_random_candidates(
    space: ParameterSpace,
    *,
    candidate_count: int,
    seed: int,
    max_expansion: int,
    max_constraints: int,
) -> tuple[dict[str, ParameterValue], ...]:
    """Sample unique candidates without replacement using an explicit seed.

    Args:
        space: Bounded parameter space.
        candidate_count: Required sample size.
        seed: Deterministic random seed.
        max_expansion: Maximum raw space expansion.
        max_constraints: Maximum constraint count.

    Returns:
        Deterministically sampled unique candidates.

    Raises:
        ValueError: If the valid space cannot satisfy the requested count.
    """
    logger.info("Sampling seeded Optimization random candidates")
    if candidate_count <= 0:
        raise ValueError("candidate_count must be positive")
    candidates: Sequence[dict[str, ParameterValue]] = tuple(
        iter_grid_candidates(
            space,
            max_candidates=max_expansion,
            max_expansion=max_expansion,
            max_constraints=max_constraints,
        )
    )
    if len(candidates) < candidate_count:
        raise ValueError("valid parameter space cannot satisfy candidate_count")
    generator = random.Random(seed)
    indices = generator.sample(range(len(candidates)), candidate_count)
    return tuple(dict(candidates[index]) for index in indices)


__all__ = ["sample_random_candidates"]
