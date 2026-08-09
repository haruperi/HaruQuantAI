"""Public Optimization walk-forward validation feature API."""

from app.services.optimization.validation.contracts import (
    SplitMode,
    TimeSeriesSplit,
    WalkForwardFoldResult,
    WalkForwardRequest,
    WalkForwardResult,
)
from app.services.optimization.validation.envelope_gate import (
    evaluate_candidate_envelope,
    filter_candidates_by_envelope,
    get_envelope_gate_contract_version,
)
from app.services.optimization.validation.scenario_holdout import (
    ScenarioHoldoutPort,
    detect_scenario_leakage,
    evaluate_scenario_holdout,
    get_scenario_holdout_contract_version,
)
from app.services.optimization.validation.splits import build_time_series_splits
from app.services.optimization.validation.walk_forward import (
    run_walk_forward_validation,
)

__all__ = [
    "ScenarioHoldoutPort",
    "SplitMode",
    "TimeSeriesSplit",
    "WalkForwardFoldResult",
    "WalkForwardRequest",
    "WalkForwardResult",
    "build_time_series_splits",
    "detect_scenario_leakage",
    "evaluate_candidate_envelope",
    "evaluate_scenario_holdout",
    "filter_candidates_by_envelope",
    "get_envelope_gate_contract_version",
    "get_scenario_holdout_contract_version",
    "run_walk_forward_validation",
]
