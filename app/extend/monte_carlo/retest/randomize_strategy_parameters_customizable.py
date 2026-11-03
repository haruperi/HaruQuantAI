"""Monte Carlo Retest: Randomize Strategy Parameters Customizable.

Description:
    Randomizes strategy parameters with fine-grained customization toggles
    for periods, shifts, constants, exit rules, booleans, and trading options.

Purpose:
    FEAT-RETESTER-MC-RETEST: Retest perturbation on customizable parameters.

Key Capabilities:
    - FR-mc-retest-parameters-custom: Selectively randomize parameter subsets.

Python API Usage:
    from app.extend.monte_carlo.retest import (
        RandomizeStrategyParametersCustomizable,
    )
    retest = RandomizeStrategyParametersCustomizable(
        probability=100, max_change=50, period=True, shift=False
    )
    new_doc = retest.apply_to_strategy(strategy_doc, rng)

CLI Usage:
    python -m app.cli retest mc-perturb --method RandomizeStrategyParametersCustomizable
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


class RandomizeStrategyParametersCustomizable(MonteCarloRetest):
    """Perturbs strategy parameters with individual parameter-type toggles."""

    def __init__(  # noqa: PLR0917
        self,
        probability: int = 100,
        max_change: int = 50,
        symmetric: bool = True,
        period: bool = True,
        shift: bool = False,
        constant: bool = False,
        other_param: bool = False,
        exit_used: bool = False,
        exit_unused: bool = False,
        boolean: bool = False,
        trading_options: bool = False,
    ) -> None:
        super().__init__(
            test_type=MonteCarloTestTypes.ModifySettings,
            name="Randomize strategy parameters Customizable",
        )
        self.probability: int = probability
        self.max_change: int = max_change
        self.symmetric: bool = symmetric
        self.period: bool = period
        self.shift: bool = shift
        self.constant: bool = constant
        self.other_param: bool = other_param
        self.exit_used: bool = exit_used
        self.exit_unused: bool = exit_unused
        self.boolean: bool = boolean
        self.trading_options: bool = trading_options

    @override
    def modify_settings(self, rng: random.Random, settings: SettingsMap) -> None:
        """Modify parameters configuration in settings map."""
        settings.set("RandomizeParamsProbability", self.probability)
        settings.set("RandomizeParamsMaxChange", self.max_change)
        settings.set("RandomizeParamsPeriod", self.period)
        settings.set("RandomizeParamsShift", self.shift)
        settings.set("RandomizeParamsConstant", self.constant)
        logger.info(
            "FR-mc-retest-parameters-custom: configured settings (period=%s)",
            self.period,
        )

    @override
    def apply_to_strategy(
        self,
        strategy: HSLStrategyDocument,
        rng: random.Random,
        params: dict[str, Any] | None = None,
    ) -> HSLStrategyDocument:
        """Perturb numeric parameters according to type filter toggles."""
        p = params or {}
        prob = float(p.get("probability", self.probability / 100.0))
        pct = float(p.get("max_change_pct", self.max_change / 100.0))
        randomize_periods = bool(p.get("period", self.period))

        new_params = dict(strategy.strategy.parameters)
        for k, spec in strategy.strategy.parameters.items():
            if not randomize_periods and "period" in k.lower():
                continue
            if rng.random() <= prob:
                curr = spec.default
                if isinstance(curr, (int, float)) and not isinstance(curr, bool):
                    factor = 1.0 + rng.uniform(-pct, pct)
                    if spec.type == "int":
                        val: int | float = max(1, round(curr * factor))
                    else:
                        val = round(curr * factor, 4)
                    new_params[k] = spec.model_copy(update={"default": val})

        logger.info("FR-mc-retest-parameters-custom: perturbed strategy params")
        payload = strategy.strategy.model_copy(update={"parameters": new_params})
        return strategy.model_copy(update={"strategy": payload})
