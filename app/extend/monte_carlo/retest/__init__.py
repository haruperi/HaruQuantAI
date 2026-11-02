"""Monte Carlo retest perturbation methods package.

Description:
    Exposes all 9 Monte Carlo Retest perturbation classes, base contracts,
    settings mapping, tick event models, and the MCRetestPerturbator catalog.

Purpose:
    FEAT-RETESTER-MC-RETEST: Monte Carlo retest perturbation classes.

Key Capabilities:
    - FR-mc-retest-core: Retest perturbation classes and registry.

Python API Usage:
    from app.extend.monte_carlo.retest import (
        MCRetestPerturbator,
        RandomizeHistoryData,
        RandomizeSpread,
    )

CLI Usage:
    python -m app.cli retest mc-perturb --list
"""

from __future__ import annotations

from app.extend.monte_carlo.retest.base import (
    MonteCarloRetest,
    MonteCarloTestTypes,
    SettingsMap,
    TickEvent,
)
from app.extend.monte_carlo.retest.catalog import (
    RETEST_CLASSES,
    BarRecord,
    MCRetestPerturbator,
)
from app.extend.monte_carlo.retest.randomize_history_data import (
    RandomizeHistoryData,
)
from app.extend.monte_carlo.retest.randomize_history_data_fixed_range import (
    RandomizeHistoryDataFixedRange,
)
from app.extend.monte_carlo.retest.randomize_history_data_ohlc import (
    RandomizeHistoryDataOHLC,
)
from app.extend.monte_carlo.retest.randomize_min_distance import (
    RandomizeMinDistance,
)
from app.extend.monte_carlo.retest.randomize_slippage import RandomizeSlippage
from app.extend.monte_carlo.retest.randomize_spread import RandomizeSpread
from app.extend.monte_carlo.retest.randomize_starting_bar import (
    RandomizeStartingBar,
)
from app.extend.monte_carlo.retest.randomize_strategy_parameters import (
    RandomizeStrategyParameters,
)
from app.extend.monte_carlo.retest.randomize_strategy_parameters_customizable import (
    RandomizeStrategyParametersCustomizable,
)

__all__ = [
    "RETEST_CLASSES",
    "BarRecord",
    "MCRetestPerturbator",
    "MonteCarloRetest",
    "MonteCarloTestTypes",
    "RandomizeHistoryData",
    "RandomizeHistoryDataFixedRange",
    "RandomizeHistoryDataOHLC",
    "RandomizeMinDistance",
    "RandomizeSlippage",
    "RandomizeSpread",
    "RandomizeStartingBar",
    "RandomizeStrategyParameters",
    "RandomizeStrategyParametersCustomizable",
    "SettingsMap",
    "TickEvent",
]
