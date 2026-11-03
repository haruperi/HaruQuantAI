"""Monte Carlo Retest: Randomize Strategy Parameters.

Description:
    Randomizes strategy parameters (indicator periods, thresholds, constants)
    within configured probability and maximum percentage change boundaries.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on strategy parameter sets.

Key Capabilities:
    - FR-mc-retest-parameters: Randomize strategy parameters with change boundaries.

Python API Usage:
    from app.extend.monte_carlo.retest.randomize_strategy_parameters import (
        RandomizeStrategyParameters,
    )
    retest = RandomizeStrategyParameters(probability=10, max_change=20)
    new_doc = retest.apply_to_strategy(strategy_doc, rng)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeStrategyParameters
"""

from __future__ import annotations

import random
from typing import Any, override

from app.core.host.logging import get_logger
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
    SettingsMap,
)

logger = get_logger(__name__)


class RandomizeStrategyParameters(MonteCarloRetest):
    """Perturbs numeric strategy parameters within bounded percentage jitter."""

    def __init__(
        self,
        probability: int = 10,
        max_change: int = 20,
        symmetric: bool = True,
    ) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize strategy parameters",
        )
        self.probability: int = probability
        self.max_change: int = max_change
        self.symmetric: bool = symmetric

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify parameters in settings map."""
        settings.set("RandomizeParamsProbability", self.probability)
        settings.set("RandomizeParamsMaxChange", self.max_change)
        settings.set("RandomizeParamsSymmetric", self.symmetric)
        logger.info(
            "FR-mc-retest-parameters: settings prob=%d, max_change=%d",
            self.probability,
            self.max_change,
        )

    @override
    def apply_to_strategy(
        self,
        strategy: HSLStrategyDocument,
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> HSLStrategyDocument:
        """Perturb numeric parameters within HSLStrategyDocument."""
        p = params or {}
        prob = float(p.get("probability", self.probability / 100.0))
        pct = float(p.get("max_change_pct", self.max_change / 100.0))

        new_params = dict(strategy.strategy.parameters)
        for k, spec in strategy.strategy.parameters.items():
            if rng.random() <= prob:
                curr = spec.default
                if isinstance(curr, (int, float)) and not isinstance(curr, bool):
                    factor = 1.0 + rng.uniform(-pct, pct)
                    if spec.type == "int":
                        val: int | float = max(1, round(curr * factor))
                    else:
                        val = round(curr * factor, 4)
                    new_params[k] = spec.model_copy(update={"default": val})

        logger.info("FR-mc-retest-parameters: perturbed parameters")
        payload = strategy.strategy.model_copy(update={"parameters": new_params})
        return strategy.model_copy(update={"strategy": payload})
