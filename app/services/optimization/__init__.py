"""Approved public port for the complete Optimization domain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.services.optimization.evidence.assemble import build_optimization_evidence
from app.services.optimization.evidence.handoff import build_report_package
from app.services.optimization.execution.adapter import execute_candidate
from app.services.optimization.migrations import (
    get_optimization_migrations,
    run_optimization_migrations,
)
from app.services.optimization.parameters import (
    evaluate_constraints,
    get_executable_parameters,
    validate_parameter_space,
)
from app.services.optimization.parameters.hashing import (
    candidate_hash,
    parameter_space_hash,
)
from app.services.optimization.persistence import create_optimization_state_store
from app.services.optimization.public_api import (
    build_optimization_handoff,
    calculate_parameter_stability,
    calculate_robustness_score,
    compare_optimization_runs,
    detect_overfit_parameters,
    get_official_optimization_tools,
    rank_parameter_sets,
    run_parameter_sweep,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
)
from app.services.optimization.public_api.factories import (
    create_optimization_value,
    dump_optimization_value,
    get_optimization_value_field,
    is_optimization_value,
)
from app.services.optimization.public_api.validation import (
    validate_request_id,
)
from app.services.optimization.robustness.assessment import assess_strategy_robustness
from app.services.optimization.robustness.barrier import (
    estimate_drawdown_mode_sensitivity,
    estimate_first_passage,
    estimate_joint_first_passage,
)
from app.services.optimization.robustness.monte_carlo import (
    calculate_confidence_intervals,
    calculate_probability_of_ruin,
    run_monte_carlo,
    run_parametric_simulation,
)
from app.services.optimization.robustness.stress import apply_execution_cost_stress
from app.services.optimization.scoring.metrics import (
    calculate_candidate_score,
    calculate_deflated_sharpe,
    count_nominal_trials,
)
from app.services.optimization.scoring.overfit import assess_overfit_evidence
from app.services.optimization.scoring.ranking import (
    rank_candidates,
    select_pareto_candidates,
)
from app.services.optimization.search.grid import iter_grid_candidates
from app.services.optimization.search.random import sample_random_candidates
from app.services.optimization.search.sweep import (
    run_bounded_search,
    select_top_candidates,
)
from app.services.optimization.state.artifacts import build_optimization_artifact_path
from app.services.optimization.state.persistence import persist_optimization_result
from app.services.optimization.state.read import load_optimization_result
from app.services.optimization.state.stores import (
    load_search_checkpoint,
    save_search_checkpoint,
)
from app.services.optimization.validation.splits import build_time_series_splits
from app.services.optimization.validation.walk_forward import (
    run_walk_forward_validation,
)

if TYPE_CHECKING:
    from app.services.optimization.execution.contracts import BacktestExecutionAdapter


def build_simulation_analytics_backtest_adapter(
    *,
    auth_context: object,
    simulation_dependencies: object,
    analytics_config: object,
    engine_type: str,
    engine_version: str,
) -> BacktestExecutionAdapter:
    """Build the concrete adapter from public Optimization boundary inputs.

    Args:
        auth_context: Authenticated invocation context.
        simulation_dependencies: Simulation service dependency.
        analytics_config: Analytics service configuration.
        engine_type: Backtest execution engine type.
        engine_version: Engine implementation version.

    Returns:
        Configured backtest adapter used by optimization workflows.
    """
    from app.services.optimization.execution.adapter import (
        SimulationAnalyticsBacktestAdapter,
    )

    return SimulationAnalyticsBacktestAdapter(
        auth_context=auth_context,
        simulation_dependencies=simulation_dependencies,
        analytics_config=analytics_config,
        engine_type=engine_type,
        engine_version=engine_version,
    )


def get_optimization_trace_id(request_id: str | None = None) -> str | None:
    """Validate and return an optional request identifier.

    Args:
        request_id: Candidate request identifier.

    Returns:
        Canonical request identifier or ``None``.
    """
    return validate_request_id(request_id)


__all__ = (
    "apply_execution_cost_stress",
    "assess_overfit_evidence",
    "assess_strategy_robustness",
    "build_optimization_artifact_path",
    "build_optimization_evidence",
    "build_optimization_handoff",
    "build_report_package",
    "build_simulation_analytics_backtest_adapter",
    "build_time_series_splits",
    "calculate_candidate_score",
    "calculate_confidence_intervals",
    "calculate_deflated_sharpe",
    "calculate_parameter_stability",
    "calculate_probability_of_ruin",
    "calculate_robustness_score",
    "candidate_hash",
    "compare_optimization_runs",
    "count_nominal_trials",
    "create_optimization_state_store",
    "create_optimization_value",
    "detect_overfit_parameters",
    "dump_optimization_value",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
    "evaluate_constraints",
    "execute_candidate",
    "get_executable_parameters",
    "get_official_optimization_tools",
    "get_optimization_migrations",
    "get_optimization_trace_id",
    "get_optimization_value_field",
    "is_optimization_value",
    "iter_grid_candidates",
    "load_optimization_result",
    "load_search_checkpoint",
    "parameter_space_hash",
    "persist_optimization_result",
    "rank_candidates",
    "rank_parameter_sets",
    "run_bounded_search",
    "run_monte_carlo",
    "run_optimization_migrations",
    "run_parameter_sweep",
    "run_parametric_simulation",
    "run_robustness_analysis",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
    "run_walk_forward_validation",
    "sample_random_candidates",
    "save_search_checkpoint",
    "select_pareto_candidates",
    "select_top_candidates",
    "validate_parameter_space",
    "validate_request_id",
)
