"""Monte Carlo Retest: Randomize Starting Bar.

Description:
    Randomizes the backtest start bar index or trims leading bars within
    [0, max_change] to simulate different market entry points.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on backtest starting bar.

Key Capabilities:
    - FR-mc-retest-starting-bar: Randomize starting bar index offset.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_starting_bar import (
        RandomizeStartingBar,
    )
    retest = RandomizeStartingBar(max_change=100)
    retest.modify_settings(rng, settings)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeStartingBar
"""

from __future__ import annotations

import random
from typing import Any, override

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
    SettingsMap,
)

logger = get_logger(__name__)


class RandomizeStartingBar(MonteCarloRetest):
    """Perturbs the backtest starting bar index."""

    def __init__(self, max_change: int = 100) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize starting bar",
        )
        self.max_change: int = max(1, max_change)

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify StartingBar in settings map."""
        val = rng.randint(0, self.max_change)
        settings.set("StartingBar", val)
        logger.info("FR-mc-retest-starting-bar: set StartingBar to %d", val)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Trim leading bars to simulate starting bar offset."""
        p = params or {}
        max_offset = min(len(bars) - 1, int(p.get("max_offset", self.max_change)))
        if max_offset > 0:
            offset = rng.randint(1, max_offset)
            logger.info("FR-mc-retest-starting-bar: offset %d bars", offset)
            return tuple(bars[offset:])
        return tuple(bars)
