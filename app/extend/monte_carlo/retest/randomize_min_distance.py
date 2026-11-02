"""Monte Carlo Retest: Randomize Min Distance.

Description:
    Randomizes the minimum price distance setting for order execution
    within configured [Min, Max] boundaries.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on minimum distance settings.

Key Capabilities:
    - FR-mc-retest-min-distance: Randomize minimum order distance parameter.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_min_distance import (
        RandomizeMinDistance,
    )
    retest = RandomizeMinDistance(min_dist=0.0, max_dist=10.0)
    retest.modify_settings(rng, settings)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeMinDistance
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


class RandomizeMinDistance(MonteCarloRetest):
    """Perturbs the MinimumDistance order execution threshold."""

    def __init__(self, min_dist: float = 0.0, max_dist: float = 10.0) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize min distance",
        )
        self.min_dist: float = max(0.0, min_dist)
        self.max_dist: float = max(self.min_dist, max_dist)

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify MinimumDistance in settings map."""
        steps = int(max(1.0, (self.max_dist - self.min_dist) / 0.1))
        val = round(self.min_dist + rng.randint(0, steps) * 0.1, 2)
        settings.set("MinimumDistance", val)
        logger.info("FR-mc-retest-min-distance: set MinimumDistance to %f", val)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply distance perturbation effect to bars."""
        p = params or {}
        min_d = float(p.get("min_dist", self.min_dist))
        max_d = float(p.get("max_dist", self.max_dist))
        dist = rng.uniform(min_d, max_d)
        return tuple(
            replace(b, spread=max(1, int(b.spread + dist * 0.1))) for b in bars
        )
