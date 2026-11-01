"""Portfolio Composer automatic-search integer allocation candidates.

Description:
    Generates integer portfolio allocation candidate vectors summing to 100
    using an injected BoundedRandom provider.
Purpose:
    FEAT-PORTFOLIO-COMPOSER: Configure composition and evaluation.
Key Capabilities:
    - FR-composer-allocations: Generate integer allocation candidate vectors.
Python API Usage:
    from app.workspace.portfolio_composer.allocations import (
        ComposerAllocations,
        BoundedRandom,
    )
    vectors = ComposerAllocations.generate(member_count=3, simulations=10, rng=rng)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_composer/test_allocations.py
"""

from __future__ import annotations

from typing import Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

_LARGE_MEMBER_THRESHOLD: int = 80
_TOTAL_ALLOCATION_UNITS: int = 100


class BoundedRandom(Protocol):
    """Protocol for bounded pseudo-random integer draws."""

    def next_index(self, upper_exclusive: int) -> int:
        """Return an integer in the half-open interval [0, upper_exclusive).

        Args:
            upper_exclusive: Upper exclusive bound (positive integer).

        Returns:
            Integer draw in [0, upper_exclusive).
        """
        ...


class ComposerAllocations:
    """Integer candidate weight allocation vector generator."""

    @staticmethod
    def generate(
        *,
        member_count: int,
        simulations: int,
        rng: BoundedRandom,
    ) -> tuple[tuple[int, ...], ...]:
        """Generate candidate weight integer vectors summing to 100.

        Args:
            member_count: Number of portfolio members (must be integer >= 1).
            simulations: Number of candidate vectors (must be integer >= 0).
            rng: Injected BoundedRandom draw source.

        Returns:
            Tuple of simulation vectors, each a tuple of member integers summing to 100.

        Raises:
            ValueError: If counts are invalid or rng returns out-of-bounds index.
        """
        if (
            type(member_count) is not int
            or type(simulations) is not int
            or member_count < 1
            or simulations < 0
        ):
            raise ValueError(
                "member_count must be positive and simulations non-negative integers"
            )

        logger.info(
            "FR-composer-allocations: generating %d allocation vectors for %d members",
            simulations,
            member_count,
        )

        if simulations == 0:
            return ()

        # Fast path for 1 member: 100% allocation without consuming random draws
        if member_count == 1:
            return ((_TOTAL_ALLOCATION_UNITS,),) * simulations

        minimum = 1 if member_count < _LARGE_MEMBER_THRESHOLD else 0
        results: list[tuple[int, ...]] = []

        for _ in range(simulations):
            alloc = [minimum] * member_count
            remaining = _TOTAL_ALLOCATION_UNITS - minimum * member_count

            for i in range(member_count - 1):
                bound = max(0, remaining) + 1
                draw = rng.next_index(bound)
                if type(draw) is not int or draw < 0 or draw >= bound:
                    raise ValueError("random index outside requested bounds")

                alloc[i] += draw
                remaining -= draw

            alloc[member_count - 1] += remaining
            results.append(tuple(alloc))

        return tuple(results)
