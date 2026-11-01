"""Monte Carlo Trade Manipulation: Randomly Degrade Execution.

Description:
    Degrades trade profitability to simulate slippage spikes and worse execution fills.

Purpose:
    FEAT-RETESTER-MC-MANIPULATION: Degrade profit by random percentage.

Key Capabilities:
    - FR-mc-degrade-execution: Uniform percentage reduction of trade net profit.

Python API Usage:
    from app.extend.monte_carlo.manipulation.randomly_degrade_execution import (
        RandomlyDegradeExecution,
    )
    degrader = RandomlyDegradeExecution(probability=20, max_pct_degradation=10.0)
    degraded = degrader.apply(records, rng=rng)

CLI Usage:
    python -m app.cli retest mc-degrade --probability 20 --max-pct 10.0
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.extend.monte_carlo.manipulation.randomly_skip_trades import SkipRandom
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)


class RandomlyDegradeExecution(BaseModel):
    """Randomly degrade execution method."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    probability: int = Field(default=20, ge=1, le=100)
    max_pct_degradation: float = Field(default=10.0, ge=0.0, le=100.0)

    def apply(
        self,
        records: Sequence[WhatIfRecord],
        *,
        rng: SkipRandom,
    ) -> list[WhatIfRecord]:
        """Apply random degradation to trades.

        Args:
            records: Sequence of WhatIfRecord objects.
            rng: Injected random index generator.

        Returns:
            List of WhatIfRecord objects with degraded profits.
        """
        if not records:
            return []

        result: list[WhatIfRecord] = []
        degraded_count = 0

        for r in records:
            if r.kind == "trade" and rng.next_index(100) < self.probability:
                draw = rng.next_index(1000)
                fraction = (draw / 1000.0) * (self.max_pct_degradation / 100.0)
                # Reduce profit if winning, increase loss if losing
                if r.profit >= 0:
                    new_profit = r.profit * (1.0 - fraction)
                else:
                    new_profit = r.profit * (1.0 + fraction)
                degraded_count += 1
                result.append(r.model_copy(update={"profit": round(new_profit, 4)}))
            else:
                result.append(r)

        logger.info(
            "FR-mc-degrade-execution: degraded %d of %d trades (max_pct=%.1f%%)",
            degraded_count,
            len(records),
            self.max_pct_degradation,
        )
        return result
