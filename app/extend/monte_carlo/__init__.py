"""Monte Carlo manipulation and retest extension package.

Description:
    Exposes trade manipulation methods and simulation retest perturbations
    matching StrategyQuant donor snippets.

Purpose:
    FEAT-RETESTER-MC-COHORT: Monte Carlo manipulation and retest cohort.

Key Capabilities:
    - FR-mc-manipulation: Trade manipulation methods.
    - FR-mc-retest: Retest perturbation methods.

Python API Usage:
    from app.extend.monte_carlo import (
        MACHRBlockRandomization,
        RandomizeTradesOrder,
        RandomlyDegradeExecution,
        RandomlySkipTrades,
        SimulateParameterJitter,
        MCRetestPerturbator,
        RandomizeHistoryData,
        RandomizeSpread,
    )

CLI Usage:
    python -m app.cli retest mc-perturb --list
"""

from __future__ import annotations

from app.extend.monte_carlo.manipulation import (
    MACHRBlockRandomization,
    RandomizeTradesOrder,
    RandomlyDegradeExecution,
    RandomlySkipTrades,
    SimulateParameterJitter,
    SkipRandom,
)
from app.extend.monte_carlo.retest import (
    RETEST_CLASSES,
    BarRecord,
    MCRetestPerturbator,
    MonteCarloRetest,
    MonteCarloTestTypes,
    RandomizeHistoryData,
    RandomizeHistoryDataFixedRange,
    RandomizeHistoryDataOHLC,
    RandomizeMinDistance,
    RandomizeSlippage,
    RandomizeSpread,
    RandomizeStartingBar,
    RandomizeStrategyParameters,
    RandomizeStrategyParametersCustomizable,
    SettingsMap,
    TickEvent,
)

__all__ = [
    "RETEST_CLASSES",
    "BarRecord",
    "MACHRBlockRandomization",
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
    "RandomizeTradesOrder",
    "RandomlyDegradeExecution",
    "RandomlySkipTrades",
    "SettingsMap",
    "SimulateParameterJitter",
    "SkipRandom",
    "TickEvent",
]
