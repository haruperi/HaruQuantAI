"""Approved public port for the complete Optimization domain."""

from __future__ import annotations

import typing

# Explicit imports keep type checking exact; runtime stays lazy.
if typing.TYPE_CHECKING:
    from app.services.optimization.evidence.assemble import build_optimization_evidence
    from app.services.optimization.evidence.handoff import build_report_package
    from app.services.optimization.evidence.promotion import (
        evaluate_promotion_gate,
        get_promotion_contract_version,
    )
    from app.services.optimization.execution.adapter import execute_candidate
    from app.services.optimization.execution.calibration import (
        get_calibration_contract_version,
        resolve_fill_model_calibration,
        resolve_scenario_difficulty_calibration,
    )
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
    from app.services.optimization.parameters.study import (
        build_optimization_study,
        get_optimization_study_contract_version,
        get_optimization_study_schema_id,
        parse_optimization_study,
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
    from app.services.optimization.robustness.assessment import (
        assess_strategy_robustness,
    )
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
    from app.services.optimization.robustness.risk_sensitivity import (
        evaluate_risk_sensitivity,
        get_risk_sensitivity_contract_version,
        summarize_drawdown_threshold_sensitivity,
    )
    from app.services.optimization.robustness.stress import apply_execution_cost_stress
    from app.services.optimization.robustness.stress_calibration import (
        get_stress_calibration_contract_version,
        resolve_stress_profile_calibration,
    )
    from app.services.optimization.scoring.metrics import (
        calculate_candidate_score,
        calculate_deflated_sharpe,
        count_nominal_trials,
    )
    from app.services.optimization.scoring.multi_objective import (
        build_multi_objective_mapping,
        evaluate_multi_objective_candidate,
        get_multi_objective_contract_version,
        get_multi_objective_schema_id,
        parse_multi_objective_mapping,
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
    from app.services.optimization.state.artifacts import (
        build_optimization_artifact_path,
    )
    from app.services.optimization.state.persistence import persist_optimization_result
    from app.services.optimization.state.read import load_optimization_result
    from app.services.optimization.state.stores import (
        load_search_checkpoint,
        save_search_checkpoint,
    )
    from app.services.optimization.validation.envelope_gate import (
        evaluate_candidate_envelope,
        filter_candidates_by_envelope,
        get_envelope_gate_contract_version,
    )
    from app.services.optimization.validation.scenario_holdout import (
        detect_scenario_leakage,
        evaluate_scenario_holdout,
        get_scenario_holdout_contract_version,
    )
    from app.services.optimization.validation.splits import build_time_series_splits
    from app.services.optimization.validation.walk_forward import (
        run_walk_forward_validation,
    )

# Public export name to the module and attribute that owns it. Resolved on
# first access so importing this boundary never loads every feature.
_EXPORTS: dict[str, tuple[str, str]] = {
    "apply_execution_cost_stress": (
        "app.services.optimization.robustness.stress",
        "apply_execution_cost_stress",
    ),
    "assess_overfit_evidence": (
        "app.services.optimization.scoring.overfit",
        "assess_overfit_evidence",
    ),
    "assess_strategy_robustness": (
        "app.services.optimization.robustness.assessment",
        "assess_strategy_robustness",
    ),
    "build_multi_objective_mapping": (
        "app.services.optimization.scoring.multi_objective",
        "build_multi_objective_mapping",
    ),
    "build_optimization_artifact_path": (
        "app.services.optimization.state.artifacts",
        "build_optimization_artifact_path",
    ),
    "build_optimization_evidence": (
        "app.services.optimization.evidence.assemble",
        "build_optimization_evidence",
    ),
    "build_optimization_handoff": (
        "app.services.optimization.public_api",
        "build_optimization_handoff",
    ),
    "build_optimization_study": (
        "app.services.optimization.parameters.study",
        "build_optimization_study",
    ),
    "build_report_package": (
        "app.services.optimization.evidence.handoff",
        "build_report_package",
    ),
    "build_time_series_splits": (
        "app.services.optimization.validation.splits",
        "build_time_series_splits",
    ),
    "calculate_candidate_score": (
        "app.services.optimization.scoring.metrics",
        "calculate_candidate_score",
    ),
    "calculate_confidence_intervals": (
        "app.services.optimization.robustness.monte_carlo",
        "calculate_confidence_intervals",
    ),
    "calculate_deflated_sharpe": (
        "app.services.optimization.scoring.metrics",
        "calculate_deflated_sharpe",
    ),
    "calculate_parameter_stability": (
        "app.services.optimization.public_api",
        "calculate_parameter_stability",
    ),
    "calculate_probability_of_ruin": (
        "app.services.optimization.robustness.monte_carlo",
        "calculate_probability_of_ruin",
    ),
    "calculate_robustness_score": (
        "app.services.optimization.public_api",
        "calculate_robustness_score",
    ),
    "candidate_hash": (
        "app.services.optimization.parameters.hashing",
        "candidate_hash",
    ),
    "compare_optimization_runs": (
        "app.services.optimization.public_api",
        "compare_optimization_runs",
    ),
    "count_nominal_trials": (
        "app.services.optimization.scoring.metrics",
        "count_nominal_trials",
    ),
    "create_optimization_state_store": (
        "app.services.optimization.persistence",
        "create_optimization_state_store",
    ),
    "create_optimization_value": (
        "app.services.optimization.public_api.factories",
        "create_optimization_value",
    ),
    "detect_overfit_parameters": (
        "app.services.optimization.public_api",
        "detect_overfit_parameters",
    ),
    "detect_scenario_leakage": (
        "app.services.optimization.validation.scenario_holdout",
        "detect_scenario_leakage",
    ),
    "dump_optimization_value": (
        "app.services.optimization.public_api.factories",
        "dump_optimization_value",
    ),
    "estimate_drawdown_mode_sensitivity": (
        "app.services.optimization.robustness.barrier",
        "estimate_drawdown_mode_sensitivity",
    ),
    "estimate_first_passage": (
        "app.services.optimization.robustness.barrier",
        "estimate_first_passage",
    ),
    "estimate_joint_first_passage": (
        "app.services.optimization.robustness.barrier",
        "estimate_joint_first_passage",
    ),
    "evaluate_candidate_envelope": (
        "app.services.optimization.validation.envelope_gate",
        "evaluate_candidate_envelope",
    ),
    "evaluate_constraints": (
        "app.services.optimization.parameters",
        "evaluate_constraints",
    ),
    "evaluate_multi_objective_candidate": (
        "app.services.optimization.scoring.multi_objective",
        "evaluate_multi_objective_candidate",
    ),
    "evaluate_promotion_gate": (
        "app.services.optimization.evidence.promotion",
        "evaluate_promotion_gate",
    ),
    "evaluate_risk_sensitivity": (
        "app.services.optimization.robustness.risk_sensitivity",
        "evaluate_risk_sensitivity",
    ),
    "evaluate_scenario_holdout": (
        "app.services.optimization.validation.scenario_holdout",
        "evaluate_scenario_holdout",
    ),
    "execute_candidate": (
        "app.services.optimization.execution.adapter",
        "execute_candidate",
    ),
    "filter_candidates_by_envelope": (
        "app.services.optimization.validation.envelope_gate",
        "filter_candidates_by_envelope",
    ),
    "get_calibration_contract_version": (
        "app.services.optimization.execution.calibration",
        "get_calibration_contract_version",
    ),
    "get_envelope_gate_contract_version": (
        "app.services.optimization.validation.envelope_gate",
        "get_envelope_gate_contract_version",
    ),
    "get_executable_parameters": (
        "app.services.optimization.parameters",
        "get_executable_parameters",
    ),
    "get_multi_objective_contract_version": (
        "app.services.optimization.scoring.multi_objective",
        "get_multi_objective_contract_version",
    ),
    "get_multi_objective_schema_id": (
        "app.services.optimization.scoring.multi_objective",
        "get_multi_objective_schema_id",
    ),
    "get_official_optimization_tools": (
        "app.services.optimization.public_api",
        "get_official_optimization_tools",
    ),
    "get_optimization_migrations": (
        "app.services.optimization.migrations",
        "get_optimization_migrations",
    ),
    "get_optimization_study_contract_version": (
        "app.services.optimization.parameters.study",
        "get_optimization_study_contract_version",
    ),
    "get_optimization_study_schema_id": (
        "app.services.optimization.parameters.study",
        "get_optimization_study_schema_id",
    ),
    "get_optimization_value_field": (
        "app.services.optimization.public_api.factories",
        "get_optimization_value_field",
    ),
    "get_promotion_contract_version": (
        "app.services.optimization.evidence.promotion",
        "get_promotion_contract_version",
    ),
    "get_risk_sensitivity_contract_version": (
        "app.services.optimization.robustness.risk_sensitivity",
        "get_risk_sensitivity_contract_version",
    ),
    "get_scenario_holdout_contract_version": (
        "app.services.optimization.validation.scenario_holdout",
        "get_scenario_holdout_contract_version",
    ),
    "get_stress_calibration_contract_version": (
        "app.services.optimization.robustness.stress_calibration",
        "get_stress_calibration_contract_version",
    ),
    "is_optimization_value": (
        "app.services.optimization.public_api.factories",
        "is_optimization_value",
    ),
    "iter_grid_candidates": (
        "app.services.optimization.search.grid",
        "iter_grid_candidates",
    ),
    "load_optimization_result": (
        "app.services.optimization.state.read",
        "load_optimization_result",
    ),
    "load_search_checkpoint": (
        "app.services.optimization.state.stores",
        "load_search_checkpoint",
    ),
    "parameter_space_hash": (
        "app.services.optimization.parameters.hashing",
        "parameter_space_hash",
    ),
    "parse_multi_objective_mapping": (
        "app.services.optimization.scoring.multi_objective",
        "parse_multi_objective_mapping",
    ),
    "parse_optimization_study": (
        "app.services.optimization.parameters.study",
        "parse_optimization_study",
    ),
    "persist_optimization_result": (
        "app.services.optimization.state.persistence",
        "persist_optimization_result",
    ),
    "rank_candidates": ("app.services.optimization.scoring.ranking", "rank_candidates"),
    "rank_parameter_sets": (
        "app.services.optimization.public_api",
        "rank_parameter_sets",
    ),
    "resolve_fill_model_calibration": (
        "app.services.optimization.execution.calibration",
        "resolve_fill_model_calibration",
    ),
    "resolve_scenario_difficulty_calibration": (
        "app.services.optimization.execution.calibration",
        "resolve_scenario_difficulty_calibration",
    ),
    "resolve_stress_profile_calibration": (
        "app.services.optimization.robustness.stress_calibration",
        "resolve_stress_profile_calibration",
    ),
    "run_bounded_search": (
        "app.services.optimization.search.sweep",
        "run_bounded_search",
    ),
    "run_monte_carlo": (
        "app.services.optimization.robustness.monte_carlo",
        "run_monte_carlo",
    ),
    "run_optimization_migrations": (
        "app.services.optimization.migrations",
        "run_optimization_migrations",
    ),
    "run_parameter_sweep": (
        "app.services.optimization.public_api",
        "run_parameter_sweep",
    ),
    "run_parametric_simulation": (
        "app.services.optimization.robustness.monte_carlo",
        "run_parametric_simulation",
    ),
    "run_robustness_analysis": (
        "app.services.optimization.public_api",
        "run_robustness_analysis",
    ),
    "run_walk_forward_matrix": (
        "app.services.optimization.public_api",
        "run_walk_forward_matrix",
    ),
    "run_walk_forward_optimization": (
        "app.services.optimization.public_api",
        "run_walk_forward_optimization",
    ),
    "run_walk_forward_validation": (
        "app.services.optimization.validation.walk_forward",
        "run_walk_forward_validation",
    ),
    "sample_random_candidates": (
        "app.services.optimization.search.random",
        "sample_random_candidates",
    ),
    "save_search_checkpoint": (
        "app.services.optimization.state.stores",
        "save_search_checkpoint",
    ),
    "select_pareto_candidates": (
        "app.services.optimization.scoring.ranking",
        "select_pareto_candidates",
    ),
    "select_top_candidates": (
        "app.services.optimization.search.sweep",
        "select_top_candidates",
    ),
    "summarize_drawdown_threshold_sensitivity": (
        "app.services.optimization.robustness.risk_sensitivity",
        "summarize_drawdown_threshold_sensitivity",
    ),
    "validate_parameter_space": (
        "app.services.optimization.parameters",
        "validate_parameter_space",
    ),
    "validate_request_id": (
        "app.services.optimization.public_api.validation",
        "validate_request_id",
    ),
}


def __getattr__(name: str) -> object:
    """Resolve one public export on first access.

    Args:
        name: Public export name.

    Returns:
        The resolved public function.

    Raises:
        AttributeError: If the name is not part of the public boundary.
    """
    target = _EXPORTS.get(name)
    if target is None:
        message = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(message)
    from importlib import import_module

    return getattr(import_module(target[0]), target[1])


def __dir__() -> list[str]:
    """List the public export surface.

    Returns:
        Sorted public export names.
    """
    return sorted(_EXPORTS)


if typing.TYPE_CHECKING:
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
    from app.services.optimization.public_api.validation import validate_request_id

    return validate_request_id(request_id)


__all__ = (
    "apply_execution_cost_stress",
    "assess_overfit_evidence",
    "assess_strategy_robustness",
    "build_multi_objective_mapping",
    "build_optimization_artifact_path",
    "build_optimization_evidence",
    "build_optimization_handoff",
    "build_optimization_study",
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
    "detect_scenario_leakage",
    "dump_optimization_value",
    "estimate_drawdown_mode_sensitivity",
    "estimate_first_passage",
    "estimate_joint_first_passage",
    "evaluate_candidate_envelope",
    "evaluate_constraints",
    "evaluate_multi_objective_candidate",
    "evaluate_promotion_gate",
    "evaluate_risk_sensitivity",
    "evaluate_scenario_holdout",
    "execute_candidate",
    "filter_candidates_by_envelope",
    "get_calibration_contract_version",
    "get_envelope_gate_contract_version",
    "get_executable_parameters",
    "get_multi_objective_contract_version",
    "get_multi_objective_schema_id",
    "get_official_optimization_tools",
    "get_optimization_migrations",
    "get_optimization_study_contract_version",
    "get_optimization_study_schema_id",
    "get_optimization_trace_id",
    "get_optimization_value_field",
    "get_promotion_contract_version",
    "get_risk_sensitivity_contract_version",
    "get_scenario_holdout_contract_version",
    "get_stress_calibration_contract_version",
    "is_optimization_value",
    "iter_grid_candidates",
    "load_optimization_result",
    "load_search_checkpoint",
    "parameter_space_hash",
    "parse_multi_objective_mapping",
    "parse_optimization_study",
    "persist_optimization_result",
    "rank_candidates",
    "rank_parameter_sets",
    "resolve_fill_model_calibration",
    "resolve_scenario_difficulty_calibration",
    "resolve_stress_profile_calibration",
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
    "summarize_drawdown_threshold_sensitivity",
    "validate_parameter_space",
    "validate_request_id",
)
