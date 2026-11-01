"""Monte Carlo Trade Manipulation: Simulate Parameter Jitter.

Description:
    Applies small random fluctuations to trade profits to simulate sensitivity
    to minor indicator or strategy parameter variations.

Purpose:
    FEAT-RETESTER-MC-MANIPULATION: Profit perturbation via parameter jitter.

Key Capabilities:
    - FR-mc-parameter-jitter: Apply jitter multiplier to trade return profits.

Python API Usage:
    from app.extend.monte_carlo.manipulation.simulate_parameter_jitter import (
        SimulateParameterJitter,
    )
    jitterer = SimulateParameterJitter(std_dev_pct=5.0)
    jittered = jitterer.apply(records, rng=rng)

CLI Usage:
    python -m app.cli retest mc-param-jitter --std-dev 5.0
"""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.core.host.logging import get_logger
from app.extend.monte_carlo.manipulation.randomly_skip_trades import SkipRandom
from app.extend.what_if.base import WhatIfRecord

logger = get_logger(__name__)


class SimulateParameterJitter(BaseModel):
    """Parameter jitter manipulation method."""

    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    std_dev_pct: float = Field(default=5.0, ge=0.0)

    def apply(
        self,
        records: Sequence[WhatIfRecord],
        *,
        rng: SkipRandom,
    ) -> list[WhatIfRecord]:
        """Apply parameter jitter multiplier to trade returns.

        Args:
            records: Sequence of WhatIfRecord objects.
            rng: Injected random index generator.

        Returns:
            List of WhatIfRecord objects with perturbed profit.
        """
        if not records or self.std_dev_pct == 0.0:
            return list(records)

        result: list[WhatIfRecord] = []
        for r in records:
            if r.kind == "trade":
                # Draw from [-1000, 1000] scaled by std_dev_pct
                draw = rng.next_index(2001) - 1000
                multiplier = 1.0 + (draw / 1000.0) * (self.std_dev_pct / 100.0)
                new_profit = round(r.profit * multiplier, 4)
                result.append(r.model_copy(update={"profit": new_profit}))
            else:
                result.append(r)

        logger.info(
            "FR-mc-parameter-jitter: applied %.1f%% jitter to %d records",
            self.std_dev_pct,
            len(records),
        )
        return result
