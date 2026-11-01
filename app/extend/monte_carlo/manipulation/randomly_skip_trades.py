"""Monte Carlo Trade Manipulation: Randomly Skip Trades.

Description:
    Implements the observed remove-without-replacement trade skip manipulation
    method. Rounds removal count deterministically using Java-compatible positive
    Math.round rounding, then removes trades by randomly drawn index.

Purpose:
    FEAT-RETESTER-MC-MANIPULATION: Monte Carlo trade manipulation skip method.

Key Capabilities:
    - FR-mc-randomly-skip-trades: Randomly skip a percentage of trades without
      replacement, preserving input sequence immutability.

Python API Usage:
    from app.extend.monte_carlo.manipulation.randomly_skip_trades import (
        RandomlySkipTrades,
        SkipRandom,
    )
    skipper = RandomlySkipTrades(probability=10)
    filtered = skipper.apply(records, rng=rng)

CLI Usage:
    python -m app.cli retest mc-skip --probability 10
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)


@runtime_checkable
class SkipRandom(Protocol):
    """Protocol for RNG providing uniform exclusive upper bounded integers."""

    def next_index(self, upper_exclusive: int) -> int:
        """Return a random index in [0, upper_exclusive - 1]."""
        ...


class RandomlySkipTrades(BaseModel):
    """Randomly skip trades simulation method."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
    )

    probability: int = Field(default=10, ge=1, le=100)

    def apply(
        self,
        records: Sequence[WhatIfRecord],
        *,
        rng: SkipRandom,
    ) -> list[WhatIfRecord]:
        """Apply skip trades manipulation without mutating input records.

        Args:
            records: Immutable sequence of analysis records.
            rng: Injected random index generator.

        Returns:
            List of retained WhatIfRecord instances.

        Raises:
            ValueError: If rng returns a non-integer, boolean, or out-of-range index.
        """
        if not records:
            logger.debug("FR-mc-randomly-skip-trades: empty records sequence received")
            return []

        result: list[WhatIfRecord] = list(records)
        removal_count = math.floor(len(records) * self.probability / 100.0 + 0.5)

        logger.info(
            "FR-mc-randomly-skip-trades: removing %d of %d records (probability=%d%%)",
            removal_count,
            len(records),
            self.probability,
        )

        for _ in range(removal_count):
            if not result:
                break
            bound = len(result)
            idx = rng.next_index(bound)
            if type(idx) is not int or type(idx) is bool or idx < 0 or idx >= bound:
                raise ValueError("random index outside requested bounds")
            del result[idx]

        return result
