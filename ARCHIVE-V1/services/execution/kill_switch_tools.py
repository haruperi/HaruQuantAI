"""Agent-facing execution kill-switch tools.

Purpose:
    Provide fail-closed tools for global, strategy, and symbol kill switches;
    new-order disabling; emergency close/cancel workflows; kill-switch audit
    events; re-enable approval requirements; and approved kill-switch clearing.

Classes and functions:
    trigger_global_kill_switch: Function. Package global kill-switch trigger.
    trigger_strategy_kill_switch: Function. Package strategy kill-switch trigger.
    trigger_symbol_kill_switch: Function. Package symbol kill-switch trigger.
    check_kill_switch_conditions: Function. Package kill-switch condition checks.
    disable_new_orders: Function. Package new-order disabling.
    close_all_positions: Function. Package emergency close-all request.
    cancel_all_orders: Function. Package emergency cancel-all request.
    record_kill_switch_event: Function. Package kill-switch audit record.
    require_reenable_approval: Function. Package re-enable approval requirement.
    clear_kill_switch_after_approval: Function. Package approved kill-switch clear.
"""

from __future__ import annotations

from typing import Any

from ._common import package_execution_request


def trigger_global_kill_switch(**kwargs: Any) -> dict[str, Any]:
    """Trigger the global trading kill switch after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a global
        kill-switch trigger request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May stop all trading when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        reason: Reason for the kill-switch trigger.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "trigger_global_kill_switch", kwargs, critical=True
    )


def trigger_strategy_kill_switch(**kwargs: Any) -> dict[str, Any]:
    """Trigger a strategy-level kill switch after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a strategy
        kill-switch trigger request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May stop one strategy when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        strategy_id: Strategy identifier.
        reason: Reason for the kill-switch trigger.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "trigger_strategy_kill_switch", kwargs, critical=True
    )


def trigger_symbol_kill_switch(**kwargs: Any) -> dict[str, Any]:
    """Trigger a symbol-level kill switch after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a symbol
        kill-switch trigger request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May stop trading for one symbol when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        symbol: Trading symbol.
        reason: Reason for the kill-switch trigger.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "trigger_symbol_kill_switch", kwargs, critical=True
    )


def check_kill_switch_conditions(**kwargs: Any) -> dict[str, Any]:
    """Evaluate kill-switch trigger conditions after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a
        kill-switch condition evaluation request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        None unless a downstream service acts on the packaged request.

    Inputs:
        approval_id: Required approval identifier.
        conditions: Trigger conditions to evaluate.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "check_kill_switch_conditions", kwargs, critical=True
    )


def disable_new_orders(**kwargs: Any) -> dict[str, Any]:
    """Disable new order submission after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a request
        to block new orders.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May block new order creation when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        scope: Optional global, strategy, or symbol scope.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("disable_new_orders", kwargs, critical=True)


def close_all_positions(**kwargs: Any) -> dict[str, Any]:
    """Close all positions after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package an
        emergency close-all request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May close live broker positions when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        account_id: Optional account identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("close_all_positions", kwargs, critical=True)


def cancel_all_orders(**kwargs: Any) -> dict[str, Any]:
    """Cancel all pending orders after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package an
        emergency cancel-all request.

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
        account_id: Optional account identifier.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("cancel_all_orders", kwargs, critical=True)


def record_kill_switch_event(**kwargs: Any) -> dict[str, Any]:
    """Record a kill-switch event after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package a
        kill-switch audit event.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May write a kill-switch audit record downstream.

    Inputs:
        approval_id: Required approval identifier.
        event_type: Kill-switch event type.
        reason: Event reason.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("record_kill_switch_event", kwargs, critical=True)


def require_reenable_approval(**kwargs: Any) -> dict[str, Any]:
    """Require approval before re-enabling trading.

    Purpose:
        Fail closed unless approval context is present, then package the
        requirement that trading cannot restart silently.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May record or enforce re-enable approval requirements downstream.

    Inputs:
        approval_id: Required approval identifier.
        scope: Optional global, strategy, or symbol scope.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request("require_reenable_approval", kwargs, critical=True)


def clear_kill_switch_after_approval(**kwargs: Any) -> dict[str, Any]:
    """Clear a kill switch only after approval gates.

    Purpose:
        Fail closed unless approval context is present, then package an
        approved kill-switch clear request.

    Tool class:
        critical

    Risk level:
        critical

    Approval required:
        human_and_risk_required

    Side effects:
        May re-enable trading scope when executed downstream.

    Inputs:
        approval_id: Required approval identifier.
        scope: Optional global, strategy, or symbol scope.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        dry_run: If True, package only.
        environment: Runtime environment.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return package_execution_request(
        "clear_kill_switch_after_approval", kwargs, critical=True
    )


__all__ = [
    "cancel_all_orders",
    "check_kill_switch_conditions",
    "clear_kill_switch_after_approval",
    "close_all_positions",
    "disable_new_orders",
    "record_kill_switch_event",
    "require_reenable_approval",
    "trigger_global_kill_switch",
    "trigger_strategy_kill_switch",
    "trigger_symbol_kill_switch",
]
