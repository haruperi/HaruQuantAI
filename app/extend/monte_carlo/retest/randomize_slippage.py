"""Monte Carlo Retest: Randomize Slippage.

Description:
    Randomizes the execution slippage parameter within configured
    [Min, Max] boundaries.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on slippage settings.

Key Capabilities:
    - FR-mc-retest-slippage: Randomize execution slippage parameter.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_slippage import (
        RandomizeSlippage,
    )
    retest = RandomizeSlippage(min_slippage=0.0, max_slippage=5.0)
    retest.modify_settings(rng, settings)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeSlippage
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


class RandomizeSlippage(MonteCarloRetest):
    """Perturbs the execution slippage parameter."""

    def __init__(self, min_slippage: float = 0.0, max_slippage: float = 5.0) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize slippage",
        )
        self.min_slippage: float = max(0.0, min_slippage)
        self.max_slippage: float = max(self.min_slippage, max_slippage)

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify Slippage in settings map."""
        steps = int(max(1.0, (self.max_slippage - self.min_slippage) / 0.1))
        val = round(self.min_slippage + rng.randint(0, steps) * 0.1, 2)
        settings.set("Slippage", val)
        logger.info("FR-mc-retest-slippage: set Slippage to %f", val)

    def perturb_bars(
        self,
        bars: tuple[MarketBar, ...] | list[MarketBar],
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> tuple[MarketBar, ...]:
        """Apply slippage degradation as widening bar spreads."""
        p = params or {}
        min_slip = float(p.get("min_slippage", self.min_slippage))
        max_slip = float(p.get("max_slippage", self.max_slippage))
        slip = rng.uniform(min_slip, max_slip)
        return tuple(replace(b, spread=max(1, int(b.spread + slip))) for b in bars)
