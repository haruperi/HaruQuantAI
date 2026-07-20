"""Simulation and backtest engine primitives."""

from app.services.strategy.registry import (
    StrategyRegistryError,
    get_strategy_class,
    list_strategy_names,
    register_builtin_strategies,
    register_strategy,
    registered_strategies,
)
from app.services.utils.standard import standardize_domain_exports

# config.py tools
from .config import (
    AccountConfig,
    DataConfig,
    ExecutionConfig,
    PositionSizeConfig,
    ReportingConfig,
    SimulationConfig,
    SimulationConfigError,
    SimulationPositionSizingError,
    SimulationSymbolInfo,
    StatefulRiskControlsConfig,
    StrategyConfig,
    _position_sizer_config,
)

# data_preparation.py tools
from .data_preparation import (
    PreparedSimulationData,
    SimulationDataPreparationError,
    SimulationDataPreparer,
    _generate_ticks_for_backtest,
    _normalize_position_sizing_method,
    _resolve_engine_type,
    _resolve_modelling,
    _resolve_tick_generator_config,
    resolve_position_size,
)

# engine.py tools
from .engine import Engine

# event_driven.py tools
from .event_driven import run_event_driven_simulation

# results.py tools
from .results import SimulationRunResult, build_symbol_summary

# runner.py tools
from .runner import SimulationRunner

# vectorized.py tools
from .vectorized import (
    prepare_vectorized_data,
    reconstruct_equity_curve,
    reconstruct_trades,
    run_vectorized_simulation,
)

__version__ = "1.0.0"

__all__ = [
    "AccountConfig",
    "DataConfig",
    "Engine",
    "ExecutionConfig",
    "PositionSizeConfig",
    "PreparedSimulationData",
    "ReportingConfig",
    "SimulationConfig",
    "SimulationConfigError",
    "SimulationDataPreparationError",
    "SimulationDataPreparer",
    "SimulationPositionSizingError",
    "SimulationRunResult",
    "SimulationRunner",
    "SimulationSymbolInfo",
    "StatefulRiskControlsConfig",
    "StrategyConfig",
    "_generate_ticks_for_backtest",
    "_normalize_position_sizing_method",
    "_position_sizer_config",
    "_resolve_engine_type",
    "_resolve_modelling",
    "_resolve_tick_generator_config",
    "build_symbol_summary",
    "get_strategy_class",
    "list_strategy_names",
    "prepare_vectorized_data",
    "reconstruct_equity_curve",
    "reconstruct_trades",
    "register_builtin_strategies",
    "register_strategy",
    "registered_strategies",
    "resolve_position_size",
    "run_event_driven_simulation",
    "run_vectorized_simulation",
]


standardize_domain_exports(globals(), __all__, tool_category="simulation")
