# ruff: noqa: S311, PLR2004
"""Mersenne Twister pseudo-random number generator primitives.

Description:
    Implements recovered MersenneTwisterRng draws with MersenneTwisterFast seed
    state and a separate MTRandom stream. Uses CPython's MT state transition,
    with Java bit extraction, signed arithmetic, and bounded rejection sampling.
    Entropy seeds, reseeding, no-argument state cloning and unstepped ranges are
    retained Python conveniences. Seeded clone/new_instance follow donor
    construction; no-argument clone copies both stream states. get_random exposes
    a separate MTRandom stream through the existing Python random.Random API.

Purpose:
    FEAT-CORE-LIB-RANDOM: Provide verified deterministic PRNG runtime utilities.

Key Capabilities:
    - FR-core-lib-random-seeding: Initialize and re-seed deterministic MT19937 streams.
    - FR-core-lib-random-cloning: Create isolated clones preserving internal
      generator state.
    - FR-core-lib-random-drawing: Generate uniform, stepped, gaussian, and boolean
      draws. DEBUG records draw operations; donor-vector tests verify results
      and the logging test verifies seeding, cloning and drawing events.

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
import secrets
from typing import Protocol, overload, override, runtime_checkable

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["IRandomGenerator", "MersenneTwisterRng", "RandomGenerator"]


class _DonorStream(random.Random):
    """Reuse CPython's MT transition with donor seed state and bit extraction.

    CPython accepts the complete 624-word MT state through its public state API.
    This avoids duplicating the twist algorithm while preserving donor seeding.
    The secondary stream uses MTRandom's two-word long-seed initialization.
    """

    gauss_next: float | None

    def __init__(self, seed: int, *, secondary: bool = False) -> None:
        self._secondary = secondary
        super().__init__(seed)

    @override
    def seed(
        self,
        a: object = None,
        version: int = 2,
    ) -> None:
        """Initialize MT state using the recovered donor integer algorithms."""
        if a is not None and not isinstance(a, int):
            raise TypeError("Donor streams require an integer seed")
        value = secrets.randbits(64) if a is None else a
        words = [0] * 624
        words[0] = (19650218 if self._secondary else value) & 0xFFFFFFFF
        for i in range(1, 624):
            previous = words[i - 1]
            words[i] = (1812433253 * (previous ^ (previous >> 30)) + i) & 0xFFFFFFFF
        if self._secondary:
            keys = [value & 0xFFFFFFFF, (value >> 32) & 0xFFFFFFFF]
            i, j = 1, 0
            for _ in range(624):
                previous = words[i - 1]
                words[i] = (
                    (words[i] ^ ((previous ^ (previous >> 30)) * 1664525)) + keys[j] + j
                ) & 0xFFFFFFFF
                i, j = i + 1, (j + 1) % 2
                if i == 624:
                    words[0], i = words[623], 1
            for _ in range(623):
                previous = words[i - 1]
                words[i] = (
                    (words[i] ^ ((previous ^ (previous >> 30)) * 1566083941)) - i
                ) & 0xFFFFFFFF
                i += 1
                if i == 624:
                    words[0], i = words[623], 1
            words[0] = 0x80000000
        self.setstate((3, (*words, 624), None))
        logger.debug("FR-core-lib-random-seeding: donor stream seeded")

    @override
    def random(self) -> float:
        """Draw the donor's 26-high/27-low bit double, consuming two words."""
        logger.debug("FR-core-lib-random-drawing: donor double draw")
        return ((self.getrandbits(26) << 27) + self.getrandbits(27)) / 2**53

    @override
    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Use the donor polar transform and retain its second result."""
        result = self.gauss_next
        self.gauss_next = None
        if result is None:
            radius = 0.0
            while radius == 0.0 or radius >= 1.0:
                first, second = 2.0 * self.random() - 1.0, 2.0 * self.random() - 1.0
                radius = first * first + second * second
            factor = math.sqrt(-2.0 * math.log(radius) / radius)
            result, self.gauss_next = first * factor, second * factor
        logger.debug("FR-core-lib-random-drawing: donor Gaussian draw")
        return mu + sigma * result


def _signed(value: int, bits: int) -> int:
    """Apply Java signed integer wrapping at a mapped arithmetic boundary."""
    sign = 1 << (bits - 1)
    return (value + sign) % (1 << bits) - sign


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
        """Retrieve the independent MTRandom stream using Python's random API."""
        ...


class RandomGenerator:
    """Deterministic seeded pseudo-random number generator for stochastic simulation.

    Implements MT19937 PRNG behavior matching donor MersenneTwisterRng / MTRandom.
    """

    __slots__ = ("_random_obj", "_rng", "_seed")

    def __init__(self, seed: int | None = None) -> None:
        """Initialize generator with optional seed.

        Args:
            seed: Deterministic integer seed or None for entropy seed.
        """
        self._seed = seed
        actual_seed = secrets.randbits(64) if seed is None else seed
        self._rng = _DonorStream(actual_seed)
        self._random_obj = _DonorStream(actual_seed, secondary=True)
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
        actual_seed = secrets.randbits(64) if seed is None else seed
        self._rng.seed(actual_seed)
        self._random_obj.seed(actual_seed)
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
        cloned._random_obj.setstate(self._random_obj.getstate())
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

        if step > 0.0:
            steps = math.ceil((max_val - min_val) / step)
            val = min_val + self.next_int(steps + 1) * step
            if decimals <= 0 or val == 0.0:
                return val
            scale = 10.0**decimals
            return math.floor((val + 1.0e-10) * scale + 0.5) / scale

        # Existing Python convenience: unstepped ranges and degenerate bounds.
        if min_val >= max_val:
            return round(float(min_val), decimals)

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
                else lower bound. Nonpositive single bounds raise ValueError.
            max_val: Upper bound (inclusive) when provided.
            step: Nonzero step size when max_val is provided, using Java division.

        Returns:
            Drawn integer value.
        """
        if max_val is None:
            if not 0 < bound_or_min <= 2**31 - 1:
                raise ValueError("Bound must be a positive Java signed integer")
            logger.debug("FR-core-lib-random-drawing: donor bounded integer draw")
            if bound_or_min & -bound_or_min == bound_or_min:
                return (bound_or_min * self._rng.getrandbits(31)) >> 31
            while True:
                bits = self._rng.getrandbits(31)
                result = bits % bound_or_min
                if bits - result + bound_or_min - 1 < 2**31:
                    return result

        min_val = bound_or_min
        difference = _signed(max_val - min_val, 32)
        if step == 0:
            raise ZeroDivisionError("Integer range step must be nonzero")
        # Java division truncates toward zero, unlike Python floor division.
        steps = abs(difference) // abs(step)
        if (difference < 0) != (step < 0):
            steps = -steps
        return _signed(min_val + self.next_int(_signed(steps + 1, 32)) * step, 32)

    def next_long(self) -> int:
        """Draw a random signed 64-bit integer (-2^63 to 2^63 - 1).

        Returns:
            Signed 64-bit integer.
        """
        logger.debug("FR-core-lib-random-drawing: donor signed long draw")
        high = _signed(self._rng.getrandbits(32), 32)
        low = _signed(self._rng.getrandbits(32), 32)
        return _signed((high << 32) + low, 64)

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
        return prob == 1.0 or self._rng.random() < prob

    def next_bool(self) -> bool:
        """Draw a fair coin-toss boolean (50% True).

        Returns:
            Boolean value.
        """
        return self.next_int(2) == 0

    def get_random(self) -> random.Random:
        """Retrieve the independent donor MTRandom stream through Python's API.

        Returns:
            Internal Random instance.
        """
        return self._random_obj


MersenneTwisterRng = RandomGenerator
