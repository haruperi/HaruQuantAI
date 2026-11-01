"""Monte Carlo Trade Manipulation: MACHR Block Randomization.

Description:
    Partitions trades into contiguous blocks of size N and shuffles the blocks
    to preserve local market correlation structures.

Purpose:
    FEAT-RETESTER-MC-MANIPULATION: Block bootstrap shuffling of trade sequences.

Key Capabilities:
    - FR-mc-block-randomization: Shuffle contiguous blocks of trades.

Python API Usage:
    from app.extend.monte_carlo.manipulation.machr_block_randomization import (
        MACHRBlockRandomization,
    )
    blocker = MACHRBlockRandomization(block_size=10)
    shuffled = blocker.apply(records, rng=rng)

CLI Usage:
    python -m app.cli retest mc-block-shuffle --block-size 10
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.extend.monte_carlo.manipulation.randomly_skip_trades import SkipRandom
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)


class MACHRBlockRandomization(BaseModel):
    """Block randomization manipulation method."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    block_size: int = Field(default=10, ge=1)

    def apply(
        self,
        records: Sequence[WhatIfRecord],
        *,
        rng: SkipRandom,
    ) -> list[WhatIfRecord]:
        """Partition records into blocks and shuffle block order.

        Args:
            records: Sequence of WhatIfRecord objects.
            rng: Injected random index generator.

        Returns:
            List of WhatIfRecord instances with blocks shuffled.
        """
        if not records:
            return []

        blocks: list[list[WhatIfRecord]] = [
            list(records[i : i + self.block_size])
            for i in range(0, len(records), self.block_size)
        ]

        shuffled_blocks: list[list[WhatIfRecord]] = []
        pool = list(blocks)
        for _ in range(len(blocks)):
            idx = rng.next_index(len(pool))
            shuffled_blocks.append(pool.pop(idx))

        result: list[WhatIfRecord] = [r for b in shuffled_blocks for r in b]
        logger.info(
            "FR-mc-block-randomization: shuffled %d blocks of size %d",
            len(blocks),
            self.block_size,
        )
        return result
