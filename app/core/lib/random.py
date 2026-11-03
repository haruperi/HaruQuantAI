# ruff: noqa: S311, PLR2004
"""Mersenne Twister pseudo-random number generator primitives.

Description:
    Provides deterministic pseudo-random number generation primitives matching
    StrategyQuant SQ/MTRandom and MersenneTwisterRng runtime behavior. Wraps
    MT19937 PRNG state with support for bounded integer draws, stepped float ranges,
    Bernoulli trials, Gaussian draws, state isolation, and deterministic cloning.

Purpose:
    FEAT-CORE-LIB-RANDOM: Provide verified deterministic PRNG runtime utilities.

Key Capabilities:
    - FR-core-lib-random-seeding: Initialize and re-seed deterministic MT19937 streams.
    - FR-core-lib-random-cloning: Create isolated clones preserving internal
      generator state.
    - FR-core-lib-random-drawing: Generate uniform, stepped, gaussian, and boolean
      draws.

Python API Usage:
    ```python
    from app.core.lib.random import RandomGenerator

    rng = RandomGenerator(seed=42)
    val = rng.next_double(0.0, 10.0, step=0.5, decimals=2)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/core/lib/test_random.py -q
    ```
"""

from __future__ import annotations

import math
import random
from typing import Protocol, overload, runtime_checkable

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["IRandomGenerator", "MersenneTwisterRng", "RandomGenerator"]


@runtime_checkable
class IRandomGenerator(Protocol):
    """Protocol matching StrategyQuant IRandomGenerator interface."""

    def seed(self, seed: int | None = None) -> None:
        """Re-seed the generator."""
        ...

    def clone(self, seed: int | None = None) -> IRandomGenerator:
        """Create an independent clone of this generator."""
        ...

    def new_instance(self, seed: int | None = None) -> IRandomGenerator:
        """Create a fresh generator instance."""
        ...

    @overload
    def next_double(self) -> float: ...

    @overload
    def next_double(
        self,
        min_val: float,
        max_val: float,
        step: float = 0.0,
        decimals: int = 4,
    ) -> float: ...

    def next_double(
        self,
        min_val: float | None = None,
        max_val: float | None = None,
        step: float = 0.0,
        decimals: int = 4,
    ) -> float:
        """Draw a uniform random float in [0.0, 1.0) or within bounded stepped range."""
        ...

    @overload
    def next_int(self, bound_or_min: int) -> int: ...

    @overload
    def next_int(
        self,
        bound_or_min: int,
        max_val: int,
        step: int = 1,
    ) -> int: ...

    def next_int(
        self,
        bound_or_min: int,
        max_val: int | None = None,
        step: int = 1,
    ) -> int:
        """Draw a random integer from [0, bound) or within [min_val, max_val] range."""
        ...

    def next_long(self) -> int:
        """Draw a random signed 64-bit integer (-2^63 to 2^63 - 1)."""
        ...

    def next_gaussian(self) -> float:
        """Draw a standard normal Gaussian random float (mean 0.0, stddev 1.0)."""
        ...

    def probability(self, prob: float) -> bool:
        """Evaluate a Bernoulli trial with success probability."""
        ...

    def next_bool(self) -> bool:
        """Draw a fair coin-toss boolean (50% True)."""
        ...

    def get_random(self) -> random.Random:
        """Retrieve the underlying standard-library random.Random instance."""
        ...


class RandomGenerator:
    """Deterministic seeded pseudo-random number generator for stochastic simulation.

    Implements MT19937 PRNG behavior matching donor MersenneTwisterRng / MTRandom.
    """

    __slots__ = ("_rng", "_seed")

    def __init__(self, seed: int | None = None) -> None:
        """Initialize generator with optional seed.

        Args:
            seed: Deterministic integer seed or None for entropy seed.
        """
        self._seed = seed
        self._rng = random.Random(seed)
        logger.debug(
            "FR-core-lib-random-seeding: initialized RandomGenerator with seed=%s",
            seed,
        )

    def seed(self, seed: int | None = None) -> None:
        """Re-seed the generator.

        Args:
            seed: Deterministic integer seed or None.
        """
        self._seed = seed
        self._rng.seed(seed)
        logger.debug(
            "FR-core-lib-random-seeding: re-seeded RandomGenerator with seed=%s",
            seed,
        )

    def clone(self, seed: int | None = None) -> RandomGenerator:
        """Create an independent clone of this generator.

        Args:
            seed: Optional seed for the clone. If omitted, copies current state.

        Returns:
            Independent RandomGenerator instance.
        """
        if seed is not None:
            logger.debug(
                "FR-core-lib-random-cloning: cloned with new seed=%s",
                seed,
            )
            return RandomGenerator(seed)
        cloned = RandomGenerator(self._seed)
        cloned._rng.setstate(self._rng.getstate())
        logger.debug(
            "FR-core-lib-random-cloning: cloned with preserved state from seed=%s",
            self._seed,
        )
        return cloned

    def new_instance(self, seed: int | None = None) -> RandomGenerator:
        """Create a fresh generator instance.

        Args:
            seed: Optional seed for the new instance.

        Returns:
            Fresh RandomGenerator instance.
        """
        logger.debug(
            "FR-core-lib-random-cloning: creating new instance with seed=%s",
            seed,
        )
        return RandomGenerator(seed)

    @overload
    def next_double(self) -> float: ...

    @overload
    def next_double(
        self,
        min_val: float,
        max_val: float,
        step: float = 0.0,
        decimals: int = 4,
    ) -> float: ...

    def next_double(
        self,
        min_val: float | None = None,
        max_val: float | None = None,
        step: float = 0.0,
        decimals: int = 4,
    ) -> float:
        """Draw a uniform random float in [0.0, 1.0) or within bounded stepped range.

        Args:
            min_val: Minimum bound, or None for [0.0, 1.0).
            max_val: Maximum bound, or None for [0.0, 1.0).
            step: Discretization step size. If > 0.0, quantizes draw to steps.
            decimals: Rounding precision for stepped/bounded draws.

        Returns:
            Drawn floating-point value.
        """
        if min_val is None or max_val is None:
            return self._rng.random()

        if min_val >= max_val:
            return round(float(min_val), decimals)

        if step > 0.0:
            steps = math.ceil((max_val - min_val) / step)
            val = min_val + self._rng.randint(0, steps) * step
            return round(val, decimals)

        val = self._rng.uniform(min_val, max_val)
        return round(val, decimals)

    @overload
    def next_int(self, bound_or_min: int) -> int: ...

    @overload
    def next_int(
        self,
        bound_or_min: int,
        max_val: int,
        step: int = 1,
    ) -> int: ...

    def next_int(
        self,
        bound_or_min: int,
        max_val: int | None = None,
        step: int = 1,
    ) -> int:
        """Draw a random integer from [0, bound) or within [min_val, max_val] range.

        Args:
            bound_or_min: Upper bound (exclusive) when max_val is None,
                else lower bound.
            max_val: Upper bound (inclusive) when provided.
            step: Step size between values when max_val is provided.

        Returns:
            Drawn integer value.
        """
        if max_val is None:
            if bound_or_min <= 0:
                return 0
            return self._rng.randrange(0, bound_or_min)

        min_val = bound_or_min
        if min_val >= max_val:
            return min_val

        if step <= 1:
            return self._rng.randint(min_val, max_val)

        steps = (max_val - min_val) // step
        return min_val + self._rng.randint(0, steps) * step

    def next_long(self) -> int:
        """Draw a random signed 64-bit integer (-2^63 to 2^63 - 1).

        Returns:
            Signed 64-bit integer.
        """
        return self._rng.randint(-9_223_372_036_854_775_808, 9_223_372_036_854_775_807)

    def next_gaussian(self) -> float:
        """Draw a standard normal Gaussian random float (mean 0.0, stddev 1.0).

        Returns:
            Gaussian distributed float.
        """
        return self._rng.gauss(0.0, 1.0)

    def probability(self, prob: float) -> bool:
        """Evaluate a Bernoulli trial with success probability.

        Args:
            prob: Probability in [0.0, 1.0].

        Returns:
            True if trial succeeds, False otherwise.
        """
        if prob <= 0.0:
            return False
        if prob >= 1.0:
            return True
        return self._rng.random() < prob

    def next_bool(self) -> bool:
        """Draw a fair coin-toss boolean (50% True).

        Returns:
            Boolean value.
        """
        return self._rng.random() < 0.5

    def get_random(self) -> random.Random:
        """Retrieve the underlying standard-library random.Random instance.

        Returns:
            Internal Random instance.
        """
        return self._rng


MersenneTwisterRng = RandomGenerator
