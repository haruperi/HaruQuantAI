"""Monte Carlo Retest: Randomize Spread.

Description:
    Randomizes the backtest spread parameter and/or bar spreads within
    configured [Min, Max] boundaries.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on spread settings and bars.

Key Capabilities:
    - FR-mc-retest-spread: Randomize simulation spread within bounds.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_spread import RandomizeSpread
    retest = RandomizeSpread(min_spread=1.0, max_spread=5.0)
    retest.modify_settings(rng, settings)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeSpread
"""

from __future__ import annotations

import random
from dataclasses import replace
from typing import Any, override

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
    SettingsMap,
)

logger = get_logger(__name__)


class RandomizeSpread(MonteCarloRetest):
    """Perturbs the backtest Spread parameter and bar spread values."""

    def __init__(self, min_spread: float = 1.0, max_spread: float = 5.0) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize spread",
        )
        self.min_spread: float = max(0.0, min_spread)
        self.max_spread: float = max(self.min_spread, max_spread)

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify Spread in settings map."""
        steps = int(max(1.0, (self.max_spread - self.min_spread) / 0.1))
        val = round(self.min_spread + rng.randint(0, steps) * 0.1, 2)
        settings.set("Spread", val)
        logger.info("FR-mc-retest-spread: set Spread to %f", val)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply random spread to bars."""
        p = params or {}
        min_sp = int(p.get("min_spread", int(self.min_spread)))
        max_sp = int(p.get("max_spread", int(self.max_spread)))
        return tuple(replace(b, spread=rng.randint(min_sp, max_sp)) for b in bars)
