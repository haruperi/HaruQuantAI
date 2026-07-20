"""Agent-facing optimization robustness tools.

Purpose:
    Provide deterministic tools for cost stress tests, Monte Carlo robustness
    packages, cross-market/timeframe checks, out-of-sample checks, robustness
    score calculation, and robustness report packaging.

Classes and functions:
    run_spread_stress_test: Function. Package wider-spread stress test.
    run_slippage_stress_test: Function. Package slippage stress test.
    run_commission_stress_test: Function. Package commission stress test.
    run_randomize_trade_order_mc: Function. Package shuffled-trade Monte Carlo.
    run_resample_trades_mc: Function. Package resampled-trade Monte Carlo.
    run_skip_trades_mc: Function. Package skipped-trade Monte Carlo.
    run_randomize_parameters_mc: Function. Package randomized-parameter Monte Carlo.
    run_randomize_history_mc: Function. Package randomized-history Monte Carlo.
    run_combined_monte_carlo: Function. Package combined Monte Carlo stress.
    run_cross_market_test: Function. Package cross-market robustness test.
    run_cross_timeframe_test: Function. Package cross-timeframe robustness test.
    run_second_oos_test: Function. Package second out-of-sample test.
    run_third_oos_test: Function. Package third out-of-sample test.
    calculate_robustness_score: Function. Calculate pass-rate robustness score.
    build_robustness_report: Function. Package robustness report creation.
"""

from __future__ import annotations

from typing import Any

from ._common import (
    optimization_tool_context,
    optimization_tool_result,
    package_optimization_request,
)


def run_spread_stress_test(**kwargs: Any) -> dict[str, Any]:
    """Package a wider-spread stress test request.

    Purpose:
        Prepare spread stress inputs for downstream robustness execution.

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
        spread_multiplier: Optional spread multiplier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_spread_stress_test", kwargs)


def run_slippage_stress_test(**kwargs: Any) -> dict[str, Any]:
    """Package a slippage stress test request.

    Purpose:
        Prepare slippage stress inputs for downstream robustness execution.

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
        slippage_multiplier: Optional slippage multiplier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_slippage_stress_test", kwargs)


def run_commission_stress_test(**kwargs: Any) -> dict[str, Any]:
    """Package a commission stress test request.

    Purpose:
        Prepare commission stress inputs for downstream robustness execution.

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
        commission_multiplier: Optional commission multiplier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_commission_stress_test", kwargs)


def run_randomize_trade_order_mc(**kwargs: Any) -> dict[str, Any]:
    """Package a shuffled-trade-order Monte Carlo request.

    Purpose:
        Prepare trade order randomization inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        trades: Optional trade list.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_randomize_trade_order_mc", kwargs)


def run_resample_trades_mc(**kwargs: Any) -> dict[str, Any]:
    """Package a resampled-trade Monte Carlo request.

    Purpose:
        Prepare bootstrap trade resampling inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        trades: Optional trade list.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_resample_trades_mc", kwargs)


def run_skip_trades_mc(**kwargs: Any) -> dict[str, Any]:
    """Package a skipped-trade Monte Carlo request.

    Purpose:
        Prepare random skipped-trade inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        trades: Optional trade list.
        skip_probability: Optional probability for skipping trades.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_skip_trades_mc", kwargs)


def run_randomize_parameters_mc(**kwargs: Any) -> dict[str, Any]:
    """Package a randomized-parameter Monte Carlo request.

    Purpose:
        Prepare parameter perturbation inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        parameters: Optional baseline parameters.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_randomize_parameters_mc", kwargs)


def run_randomize_history_mc(**kwargs: Any) -> dict[str, Any]:
    """Package a randomized-history Monte Carlo request.

    Purpose:
        Prepare historical path randomization inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        returns: Optional returns list.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_randomize_history_mc", kwargs)


def run_combined_monte_carlo(**kwargs: Any) -> dict[str, Any]:
    """Package a combined Monte Carlo stress request.

    Purpose:
        Prepare combined randomization inputs for robustness analysis.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        scenarios: Optional scenario list.
        iterations: Optional iteration count.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_combined_monte_carlo", kwargs)


def run_cross_market_test(**kwargs: Any) -> dict[str, Any]:
    """Package a cross-market robustness test request.

    Purpose:
        Prepare related-symbol robustness inputs.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        symbols: Optional related symbol list.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_cross_market_test", kwargs)


def run_cross_timeframe_test(**kwargs: Any) -> dict[str, Any]:
    """Package a cross-timeframe robustness test request.

    Purpose:
        Prepare nearby-timeframe robustness inputs.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        timeframes: Optional timeframe list.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_cross_timeframe_test", kwargs)


def run_second_oos_test(**kwargs: Any) -> dict[str, Any]:
    """Package a second out-of-sample test request.

    Purpose:
        Prepare a pre-development out-of-sample validation request.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        dataset_id: Optional dataset identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_second_oos_test", kwargs)


def run_third_oos_test(**kwargs: Any) -> dict[str, Any]:
    """Package a third out-of-sample test request.

    Purpose:
        Prepare a post-development out-of-sample validation request.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        dataset_id: Optional dataset identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("run_third_oos_test", kwargs)


def calculate_robustness_score(**kwargs: Any) -> dict[str, Any]:
    """Calculate a robustness score from pass/fail checks.

    Purpose:
        Produce a deterministic percentage score from robustness check results.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        checks: List of check dictionaries with passed booleans.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, simulate only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    checks = kwargs.get("checks") or []
    passed = len([check for check in checks if bool(check.get("passed", False))])
    score = passed / len(checks) * 100.0 if checks else 0.0
    return optimization_tool_result(
        "calculate_robustness_score",
        data={"robustness_score": score, "passed": passed, "total": len(checks)},
        **optimization_tool_context(kwargs),
    )


def build_robustness_report(**kwargs: Any) -> dict[str, Any]:
    """Package a robustness report creation request.

    Purpose:
        Prepare robustness result data for downstream report creation.

    Tool class:
        write_safe

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        robustness_result: Optional robustness result payload.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_optimization_request("build_robustness_report", kwargs)


__all__ = [
    "build_robustness_report",
    "calculate_robustness_score",
    "run_combined_monte_carlo",
    "run_commission_stress_test",
    "run_cross_market_test",
    "run_cross_timeframe_test",
    "run_randomize_history_mc",
    "run_randomize_parameters_mc",
    "run_randomize_trade_order_mc",
    "run_resample_trades_mc",
    "run_second_oos_test",
    "run_skip_trades_mc",
    "run_slippage_stress_test",
    "run_spread_stress_test",
    "run_third_oos_test",
]
