"""Agent-facing live execution tools.

Purpose:
    Provide fail-closed tools for live order submission, modification,
    cancellation, position reduction/closure, strategy pause/resume, broker
    state synchronization, reconciliation, and live execution reporting.

Classes and functions:
    submit_live_order: Function. Package a live order request.
    modify_live_order: Function. Package a live order modification.
    close_live_position: Function. Package a live position close request.
    cancel_live_order: Function. Package a live order cancellation.
    reduce_live_exposure: Function. Package live exposure reduction.
    pause_live_strategy: Function. Package live strategy pause.
    resume_live_strategy: Function. Package live strategy resume.
    sync_live_positions: Function. Package live position synchronization.
    reconcile_broker_state: Function. Package broker reconciliation.
    build_live_execution_report: Function. Package live execution reporting.
"""

from __future__ import annotations

from typing import Any

from ._common import package_execution_request


def submit_live_order(**kwargs: Any) -> dict[str, Any]:
    """Submit a live order request after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        order request for the broker execution layer.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May place a live broker order only when executed downstream after all
        gates pass.

    Inputs:
        approval_id: Required approval identifier.
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
    return package_execution_request("submit_live_order", kwargs, critical=True)


def modify_live_order(**kwargs: Any) -> dict[str, Any]:
    """Modify a live broker order after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        order modification request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May modify live broker state when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        order_id: Broker order identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("modify_live_order", kwargs, critical=True)


def close_live_position(**kwargs: Any) -> dict[str, Any]:
    """Close a live broker position after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        position close request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May close live broker exposure when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        position_id: Broker position identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("close_live_position", kwargs, critical=True)


def cancel_live_order(**kwargs: Any) -> dict[str, Any]:
    """Cancel a live pending order after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        order cancellation request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May cancel live broker orders when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        order_id: Broker order identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("cancel_live_order", kwargs, critical=True)


def reduce_live_exposure(**kwargs: Any) -> dict[str, Any]:
    """Reduce live broker exposure after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        exposure reduction request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May reduce live capital exposure when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        symbol: Optional trading symbol.
        reduction_amount: Optional exposure reduction target.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("reduce_live_exposure", kwargs, critical=True)


def pause_live_strategy(**kwargs: Any) -> dict[str, Any]:
    """Pause a live strategy after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        strategy pause request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May pause live strategy execution when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        strategy_id: Strategy identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("pause_live_strategy", kwargs, critical=True)


def resume_live_strategy(**kwargs: Any) -> dict[str, Any]:
    """Resume a live strategy after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a live
        strategy resume request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May resume live strategy execution when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        strategy_id: Strategy identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("resume_live_strategy", kwargs, critical=True)


def sync_live_positions(**kwargs: Any) -> dict[str, Any]:
    """Synchronize live positions from broker state.

    Purpose:
        Fail closed unless approval context is present, then package live
        position synchronization.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May update internal live position state when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        account_id: Optional broker account identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("sync_live_positions", kwargs, critical=True)


def reconcile_broker_state(**kwargs: Any) -> dict[str, Any]:
    """Reconcile internal execution state against broker state.

    Purpose:
        Fail closed unless approval context is present, then package broker
        reconciliation.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May write reconciliation records or trigger downstream remediation.

    Inputs:
        approval_id: Required approval identifier.
        account_id: Optional broker account identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("reconcile_broker_state", kwargs, critical=True)


def build_live_execution_report(**kwargs: Any) -> dict[str, Any]:
    """Build a live execution result report request.

    Purpose:
        Fail closed unless approval context is present, then package live
        execution report generation.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May create a live execution report artifact downstream.

    Inputs:
        approval_id: Required approval identifier.
        strategy_id: Optional strategy identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "build_live_execution_report", kwargs, critical=True
    )


__all__ = [
    "build_live_execution_report",
    "cancel_live_order",
    "close_live_position",
    "modify_live_order",
    "pause_live_strategy",
    "reconcile_broker_state",
    "reduce_live_exposure",
    "resume_live_strategy",
    "submit_live_order",
    "sync_live_positions",
]
