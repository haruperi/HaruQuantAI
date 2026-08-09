"""Public Optimization execution feature API."""

from app.services.optimization.execution.adapter import (
    SimulationAnalyticsBacktestAdapter,
    execute_candidate,
)
from app.services.optimization.execution.calibration import (
    FillModelCalibrationPort,
    ScenarioDifficultyCalibrationPort,
    get_calibration_contract_version,
    resolve_fill_model_calibration,
    resolve_scenario_difficulty_calibration,
)
from app.services.optimization.execution.contracts import (
    BacktestExecutionAdapter,
    BacktestExecutionContext,
    BacktestExecutionRequest,
    EngineOptimizationResult,
)

__all__ = [
    "BacktestExecutionAdapter",
    "BacktestExecutionContext",
    "BacktestExecutionRequest",
    "EngineOptimizationResult",
    "FillModelCalibrationPort",
    "ScenarioDifficultyCalibrationPort",
    "SimulationAnalyticsBacktestAdapter",
    "execute_candidate",
    "get_calibration_contract_version",
    "resolve_fill_model_calibration",
    "resolve_scenario_difficulty_calibration",
]
