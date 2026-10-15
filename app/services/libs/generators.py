# ruff: noqa: S311, PLR2004
"""High-performance pseudo-random number generator primitives.

Description:
    Provides RandomGenerator, a deterministic seeded pseudo-random number
    generator (PRNG) designed for quantitative research, stochastic simulation,
    Monte Carlo analysis, strategy parameter perturbation, and trade order
    randomization. Supports uniform floating-point draws, bounded and stepped
    integer sampling, standard normal Gaussian distributions, Bernoulli
    probability trials, 64-bit integer generation, and isolated instance cloning.

Purpose:
    FEAT-LIBS-GENERATORS: Deterministic pseudo-random number generator primitives.

Key Capabilities:
    - FR-LIBS-GENERATORS-UNIFORM-SAMPLING: Floating-point and integer sampling.
      Associated: `RandomGenerator.next_double()`, `RandomGenerator.next_int()`.
      Logging: Pure in-memory deterministic PRNG with zero side effects.
    - FR-LIBS-GENERATORS-DISCRETE-STEPPING: Stepped parameter sampling and rounding.
      Associated: `RandomGenerator.next_double()`, `RandomGenerator.next_int()`.
      Logging: Pure in-memory deterministic PRNG with zero side effects.
    - FR-LIBS-GENERATORS-GAUSSIAN-DISTRIBUTION: Standard normal Gaussian variates.
      Associated: `RandomGenerator.next_gaussian()`.
      Logging: Pure in-memory deterministic PRNG with zero side effects.
    - FR-LIBS-GENERATORS-STOCHASTIC-GATING: Bernoulli probability trials.
      Associated: `RandomGenerator.probability()`, `RandomGenerator.next_bool()`.
      Logging: Pure in-memory deterministic PRNG with zero side effects.
    - FR-LIBS-GENERATORS-INSTANCE-CLONING: Seeded cloning and branch replication.
      Associated: `RandomGenerator.clone()`, `RandomGenerator.new_instance()`.
      Logging: Pure in-memory deterministic PRNG with zero side effects.

Python API Usage:
    ```python
    from app.services.libs.generators import RandomGenerator

    rng = RandomGenerator(seed=42)
    val = rng.next_double()  # Uniform [0.0, 1.0)
    stepped = rng.next_double(10.0, 50.0, step=5.0, decimals=2)  # Stepped draw
    idx = rng.next_int(10)  # Integer in [0, 10)
    flag = rng.probability(0.25)  # 25% True
    gauss = rng.next_gaussian()  # N(0, 1)
    clone_rng = rng.clone()
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_generators.py --no-cov
    ```
"""

from __future__ import annotations

import random
from typing import overload

__all__ = ["RandomGenerator"]


class RandomGenerator:
    """Deterministic seeded pseudo-random number generator for stochastic simulation."""

    def __init__(self, seed: int | None = None) -> None:
        """Initialize generator with optional seed.

        Args:
            seed: Deterministic integer seed or None for entropy seed.
        """
        self._seed = seed
        self._rng = random.Random(seed)

    def seed(self, seed: int | None = None) -> None:
        """Re-seed the generator.

        Args:
            seed: Deterministic integer seed or None.
        """
        self._seed = seed
        self._rng.seed(seed)

    def clone(self, seed: int | None = None) -> RandomGenerator:
        """Create an independent clone of this generator.

        Args:
            seed: Optional seed for the clone. If omitted, copies current state.

        Returns:
            Independent RandomGenerator instance.
        """
        if seed is not None:
            return RandomGenerator(seed)
        cloned = RandomGenerator(self._seed)
        cloned._rng.setstate(self._rng.getstate())
        return cloned

    def new_instance(self, seed: int | None = None) -> RandomGenerator:
        """Create a fresh generator instance.

        Args:
            seed: Optional seed for the new instance.

        Returns:
            Fresh RandomGenerator instance.
        """
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
            steps = round((max_val - min_val) / step)
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
            prob: Probability in [0.0, 1.0] (or 0..100 percentage).

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
