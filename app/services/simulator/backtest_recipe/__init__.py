"""Canonical single-asset backtest recipe (FEAT-SIM-19).

Owns the complete server-side pipeline that turns an operator's run
configuration into a canonical Simulation run and its Analytics performance
report, plus the bounded background execution that a multi-minute run requires.
"""

from app.services.simulator.backtest_recipe.dependencies import (
    ExecutionSettings,
    ProviderFacts,
    StrategyBacktestDependencies,
)
from app.services.simulator.backtest_recipe.descriptors import (
    StrategyDescriptor,
    StrategyParameter,
    get_backtest_strategy_descriptor,
    get_backtest_strategy_descriptors,
    resolve_strategy_parameters,
)
from app.services.simulator.backtest_recipe.jobs import (
    BacktestJob,
    BacktestJobRegistry,
    JobStatus,
)
from app.services.simulator.backtest_recipe.pipeline import (
    REPORT_METRIC_KEYS,
    RUN_STAGES,
    BacktestRunConfig,
    run_strategy_backtest,
)

__all__ = (
    "REPORT_METRIC_KEYS",
    "RUN_STAGES",
    "BacktestJob",
    "BacktestJobRegistry",
    "BacktestRunConfig",
    "ExecutionSettings",
    "JobStatus",
    "ProviderFacts",
    "StrategyBacktestDependencies",
    "StrategyDescriptor",
    "StrategyParameter",
    "get_backtest_strategy_descriptor",
    "get_backtest_strategy_descriptors",
    "resolve_strategy_parameters",
    "run_strategy_backtest",
)
