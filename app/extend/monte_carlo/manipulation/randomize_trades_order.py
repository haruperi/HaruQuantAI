"""Monte Carlo Trade Manipulation: Randomize Trades Order.

Description:
    Shuffles trade order either by exact permutation (Fisher-Yates without replacement)
    or bootstrapping (resampling with replacement).

Purpose:
    FEAT-RETESTER-MC-MANIPULATION: Trade sequence order randomization.

Key Capabilities:
    - FR-mc-randomize-trades-order: Exact shuffle or bootstrap of trade records.

Python API Usage:
    from app.extend.monte_carlo.manipulation.randomize_trades_order import (
        RandomizeTradesOrder,
    )
    shuffler = RandomizeTradesOrder(method="exact")
    shuffled = shuffler.apply(records, rng=rng)

CLI Usage:
    python -m app.cli retest mc-randomize-order --method exact
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.host.logging import get_logger
from app.extend.monte_carlo.manipulation.randomly_skip_trades import SkipRandom
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)


class RandomizeTradesOrder(BaseModel):
    """Randomize trades order manipulation method."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    method: Literal["exact", "resampling"] = "exact"

    def apply(
        self,
        records: Sequence[WhatIfRecord],
        *,
        rng: SkipRandom,
    ) -> list[WhatIfRecord]:
        """Apply trade order randomization.

        Args:
            records: Immutable sequence of analysis records.
            rng: Injected random index generator.

        Returns:
            Shuffled or resampled list of WhatIfRecord instances.
        """
        if not records:
            logger.debug("FR-mc-randomize-trades-order: empty records")
            return []

        n = len(records)
        if self.method == "exact":
            pool = list(records)
            result: list[WhatIfRecord] = []
            for _ in range(n):
                idx = rng.next_index(len(pool))
                result.append(pool.pop(idx))
            logger.info(
                "FR-mc-randomize-trades-order: exact Fisher-Yates shuffle on %d trades",
                n,
            )
            return result

        # method == "resampling"
        result = [records[rng.next_index(n)] for _ in range(n)]
        logger.info(
            "FR-mc-randomize-trades-order: bootstrap resampling of %d trades", n
        )
        return result
