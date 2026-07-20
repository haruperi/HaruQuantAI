"""Agent-facing paper trading execution tools.

Purpose:
    Provide deterministic tools for starting/stopping paper strategies,
    submitting/modifying simulated orders, closing simulated positions,
    recording fills, calculating paper slippage, comparing paper trading to
    backtests, and building paper trading reports.

Classes and functions:
    start_paper_strategy: Function. Package a paper strategy start request.
    stop_paper_strategy: Function. Package a paper strategy stop request.
    submit_paper_order: Function. Package a simulated order request.
    modify_paper_order: Function. Package a simulated order modification.
    close_paper_position: Function. Package a simulated position close request.
    record_paper_fill: Function. Package a paper fill recording request.
    calculate_paper_slippage: Function. Package paper slippage calculation.
    compare_paper_vs_backtest: Function. Package paper/backtest comparison.
    build_paper_trading_report: Function. Package paper trading report creation.
"""

from __future__ import annotations

from typing import Any

from ._common import package_execution_request


def start_paper_strategy(**kwargs: Any) -> dict[str, Any]:
    """Enable a strategy in paper trading mode.

    Purpose:
        Package a controlled paper strategy start request.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May change paper strategy state when executed by a downstream service.

    Inputs:
        strategy_id: Strategy identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("start_paper_strategy", kwargs)


def stop_paper_strategy(**kwargs: Any) -> dict[str, Any]:
    """Disable a strategy in paper trading mode.

    Purpose:
        Package a controlled paper strategy stop request.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May change paper strategy state when executed by a downstream service.

    Inputs:
        strategy_id: Strategy identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("stop_paper_strategy", kwargs)


def submit_paper_order(**kwargs: Any) -> dict[str, Any]:
    """Submit a simulated paper order request.

    Purpose:
        Package a paper order request without live broker side effects.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May create a simulated paper order when executed downstream.

    Inputs:
        strategy_id: Strategy identifier.
        symbol: Trading symbol.
        side: Order side.
        volume: Proposed order volume.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("submit_paper_order", kwargs)


def modify_paper_order(**kwargs: Any) -> dict[str, Any]:
    """Modify a simulated paper order request.

    Purpose:
        Package a paper order modification request.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May change a simulated order when executed downstream.

    Inputs:
        order_id: Simulated order identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("modify_paper_order", kwargs)


def close_paper_position(**kwargs: Any) -> dict[str, Any]:
    """Close a simulated paper position.

    Purpose:
        Package a paper position close request.

    Tool class:
        write_controlled

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May close a simulated position when executed downstream.

    Inputs:
        position_id: Simulated position identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("close_paper_position", kwargs)


def record_paper_fill(**kwargs: Any) -> dict[str, Any]:
    """Record a simulated paper fill.

    Purpose:
        Package a paper fill record for audit and paper analytics.

    Tool class:
        write_safe

    Risk level:
        high

    Approval required:
        audit_required

    Side effects:
        May write a paper fill record when executed downstream.

    Inputs:
        order_id: Simulated order identifier.
        fill_price: Fill price.
        fill_volume: Fill volume.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("record_paper_fill", kwargs)


def calculate_paper_slippage(**kwargs: Any) -> dict[str, Any]:
    """Calculate simulated or observed paper slippage.

    Purpose:
        Package paper slippage calculation inputs for paper analytics.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None.

    Inputs:
        expected_price: Expected execution price.
        fill_price: Observed fill price.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("calculate_paper_slippage", kwargs)


def compare_paper_vs_backtest(**kwargs: Any) -> dict[str, Any]:
    """Compare paper trading behavior against backtest expectations.

    Purpose:
        Package paper/backtest comparison inputs for graduation checks.

    Tool class:
        read_only

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None.

    Inputs:
        paper_result_id: Paper trading result identifier.
        backtest_result_id: Backtest result identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("compare_paper_vs_backtest", kwargs)


def build_paper_trading_report(**kwargs: Any) -> dict[str, Any]:
    """Build a paper trading graduation report request.

    Purpose:
        Package paper report creation inputs for downstream reporting.

    Tool class:
        write_safe

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        May create a paper trading report artifact when executed downstream.

    Inputs:
        strategy_id: Strategy identifier.
        paper_result_id: Paper trading result identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("build_paper_trading_report", kwargs)


__all__ = [
    "build_paper_trading_report",
    "calculate_paper_slippage",
    "close_paper_position",
    "compare_paper_vs_backtest",
    "modify_paper_order",
    "record_paper_fill",
    "start_paper_strategy",
    "stop_paper_strategy",
    "submit_paper_order",
]
