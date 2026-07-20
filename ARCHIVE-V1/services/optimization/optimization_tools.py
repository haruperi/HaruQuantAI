"""Agent-facing optimization tools.

Purpose:
    Provide deterministic tools for parameter sweeps, walk-forward
    optimization, optimization comparison, stability analysis, overfit checks,
    ranking, persistence packaging, and report packaging.

Classes and functions:
    run_parameter_sweep: Function. Package grid/random parameter search.
    run_walk_forward_optimization: Function. Package walk-forward optimization.
    run_walk_forward_matrix: Function. Package walk-forward matrix analysis.
    compare_optimization_runs: Function. Package optimization run comparison.
    calculate_parameter_stability: Function. Calculate parameter stability.
    detect_overfit_parameters: Function. Detect overfit risk from score gaps.
    rank_parameter_sets: Function. Rank candidates by score.
    save_optimization_result: Function. Package optimization result persistence.
    build_optimization_report: Function. Package optimization report creation.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from ._common import (
    optimization_tool_context,
    optimization_tool_result,
    package_optimization_request,
)


def run_parameter_sweep(**kwargs: Any) -> dict[str, Any]:
    """Package a grid or random parameter search request.

    Purpose:
        Validate and package a parameter sweep request for downstream
        optimization execution.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        strategy_id: Optional strategy identifier.
        parameter_grid: Optional parameter grid or distributions.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_parameter_sweep", kwargs)


def run_walk_forward_optimization(**kwargs: Any) -> dict[str, Any]:
    """Package a walk-forward optimization request.

    Purpose:
        Validate and package rolling train/test optimization details.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        strategy_id: Optional strategy identifier.
        train_period: Optional training window.
        test_period: Optional test window.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_walk_forward_optimization", kwargs)


def run_walk_forward_matrix(**kwargs: Any) -> dict[str, Any]:
    """Package a walk-forward matrix request.

    Purpose:
        Validate and package a matrix of walk-forward train/test combinations.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        strategy_id: Optional strategy identifier.
        matrix: Optional train/test matrix definition.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_walk_forward_matrix", kwargs)


def compare_optimization_runs(**kwargs: Any) -> dict[str, Any]:
    """Package an optimization run comparison request.

    Purpose:
        Validate and package candidate optimization run IDs or result payloads.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None.

    Inputs:
        runs: Optional run result list.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("compare_optimization_runs", kwargs)


def calculate_parameter_stability(**kwargs: Any) -> dict[str, Any]:
    """Calculate standard-deviation stability by parameter.

    Purpose:
        Quantify parameter value dispersion across selected optimization
        candidates.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        parameters: Mapping from parameter name to sampled values.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    parameters = kwargs.get("parameters") or {}
    stability = {}
    for key, values in parameters.items():
        series = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
        stability[key] = float(series.std()) if len(series) else 0.0
    return optimization_tool_result(
        "calculate_parameter_stability",
        data={"stability": stability},
        **optimization_tool_context(kwargs),
    )


def detect_overfit_parameters(**kwargs: Any) -> dict[str, Any]:
    """Detect overfit risk from in-sample and out-of-sample score gap.

    Purpose:
        Flag parameter sets whose in-sample score materially exceeds their
        out-of-sample score.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        in_sample_score: In-sample score.
        out_of_sample_score: Out-of-sample score.
        threshold: Maximum acceptable score gap.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    in_sample = float(kwargs.get("in_sample_score", 0.0) or 0.0)
    out_sample = float(kwargs.get("out_of_sample_score", 0.0) or 0.0)
    threshold = float(kwargs.get("threshold", 0.25) or 0.25)
    gap = in_sample - out_sample
    return optimization_tool_result(
        "detect_overfit_parameters",
        data={"overfit_risk": gap > threshold, "score_gap": gap},
        **optimization_tool_context(kwargs),
    )


def rank_parameter_sets(**kwargs: Any) -> dict[str, Any]:
    """Rank optimization parameter candidates by score.

    Purpose:
        Sort candidate parameter sets deterministically from highest score to
        lowest score.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        candidates: List of dictionaries containing score values.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    candidates = kwargs.get("candidates") or []
    ranked = sorted(
        candidates,
        key=lambda item: float(item.get("score", 0.0)),
        reverse=True,
    )
    return optimization_tool_result(
        "rank_parameter_sets",
        data={"ranked": ranked},
        **optimization_tool_context(kwargs),
    )


def save_optimization_result(**kwargs: Any) -> dict[str, Any]:
    """Package an optimization result persistence request.

    Purpose:
        Prepare optimization result metadata for downstream storage.

    Tool class:
        write_safe

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        optimization_result: Optional result payload.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("save_optimization_result", kwargs)


def build_optimization_report(**kwargs: Any) -> dict[str, Any]:
    """Package an optimization report creation request.

    Purpose:
        Prepare report inputs for downstream reporting.

    Tool class:
        write_safe

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        optimization_result: Optional result payload.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("build_optimization_report", kwargs)


__all__ = [
    "build_optimization_report",
    "calculate_parameter_stability",
    "compare_optimization_runs",
    "detect_overfit_parameters",
    "rank_parameter_sets",
    "run_parameter_sweep",
    "run_walk_forward_matrix",
    "run_walk_forward_optimization",
    "save_optimization_result",
]
