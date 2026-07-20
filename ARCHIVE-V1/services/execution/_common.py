"""Shared execution-service helpers.

Purpose:
    Provide shared execution module accessors, lazy service fallback, and the
    standard result helpers used by agent-facing execution tools.

Classes and functions:
    execution_approval_module: Function. Return the execution approval module.
    execution_live_module: Function. Return the live execution module.
    execution_monitoring_module: Function. Return the execution monitoring module.
    execution_performance_module: Function. Return the execution performance module.
    execution_reconciliation_module: Function. Return the reconciliation module.
    execution_trade_governor_module: Function. Return the trade governor module.
    execution_tool_result: Function. Build a standard execution tool envelope.
    execution_tool_context: Function. Extract common tool context fields.
    package_execution_request: Function. Package a deterministic execution request.
    __getattr__: Function. Resolve lower-level execution attributes lazily.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import ModuleType
from typing import Any
from uuid import uuid4

from app.services import load_service_module, resolve_service_attr, service_modules
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

_PRIORITY_MODULES = (
    "app.services.execution.approval",
    "app.services.execution.core",
    "app.services.execution.metadata_cache",
    "app.services.execution.pre_send",
    "app.services.execution.readiness",
    "app.services.execution.reconciliation",
    "app.services.execution.send_service",
    "app.services.execution.trade_action_governor",
    "app.services.execution.live",
    "app.services.execution.live.session",
)


def _service_modules() -> tuple[str, ...]:
    """Return prioritized execution service modules for lazy resolution."""
    return _PRIORITY_MODULES + tuple(
        module
        for module in service_modules("app.services.execution")
        if module not in _PRIORITY_MODULES
        and module not in {"app.services.execution", "app.services.execution._common"}
    )


def execution_approval_module() -> ModuleType:
    """Return the execution approval service module."""
    module: ModuleType = load_service_module("app.services.execution.approval")
    return module


def execution_live_module() -> ModuleType:
    """Return the live execution service module."""
    module: ModuleType = load_service_module("app.services.execution.live")
    return module


def execution_monitoring_module() -> ModuleType:
    """Return the execution monitoring service module."""
    module: ModuleType = load_service_module("app.services.execution.monitoring")
    return module


def execution_performance_module() -> ModuleType:
    """Return the execution performance service module."""
    module: ModuleType = load_service_module("app.services.execution.performance")
    return module


def execution_reconciliation_module() -> ModuleType:
    """Return the execution reconciliation service module."""
    module: ModuleType = load_service_module("app.services.execution.reconciliation")
    return module


def execution_trade_governor_module() -> ModuleType:
    """Return the trade action governor service module."""
    module: ModuleType = load_service_module(
        "app.services.execution.trade_action_governor"
    )
    return module


def execution_tool_result(
    name: str,
    *,
    status: str = "success",
    data: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    risk_level: str = "high",
    approval_required: str = "risk_governor_required",
    side_effects: list[str] | None = None,
) -> dict[str, Any]:
    """Build the standard HaruQuant result envelope for execution tools.

    Purpose:
        Centralize the common result shape used by all agent-facing execution
        tools.

    Args:
        name: Tool name.
        status: Tool status.
        data: Business payload.
        errors: Validation, policy, or runtime errors.
        warnings: Non-blocking warnings.
        request_id: Optional external request identifier.
        agent_name: Optional caller agent name.
        environment: Runtime environment.
        dry_run: Whether the call simulated behavior only.
        risk_level: Tool risk level.
        approval_required: Approval policy.
        side_effects: Side effects created by the call.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    _ = (
        agent_name,
        environment,
        dry_run,
        warnings,
        side_effects,
        approval_required,
        uuid4,
        datetime,
        timezone,
    )
    error_list = errors or []
    normalized_status = "success" if status == "success" and not error_list else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=name,
            tool_category="execution",
            tool_risk_level=risk_level,
            read_only=dry_run,
            places_trade=risk_level == "critical",
            requires_approval=risk_level == "critical",
            requires_network=risk_level == "critical",
        ),
        status=normalized_status,
        message=(
            "Execution tool executed successfully."
            if normalized_status == "success"
            else "Execution tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "PERMISSION_DENIED"
            if "approval" in "; ".join(error_list).lower()
            else "TOOL_EXECUTION_FAILED",
            "details": "; ".join(error_list) or "Execution tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def execution_tool_context(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract common execution tool context fields from keyword arguments.

    Purpose:
        Keep tool implementations focused on business validation while using a
        consistent context shape.

    Args:
        kwargs: Tool keyword arguments.

    Returns:
        Context fields accepted by execution_tool_result.
    """
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name"),
        "environment": kwargs.get("environment", "development"),
        "dry_run": kwargs.get("dry_run", True),
    }


def package_execution_request(
    name: str,
    kwargs: dict[str, Any],
    *,
    critical: bool = False,
) -> dict[str, Any]:
    """Package a deterministic execution request without live side effects.

    Purpose:
        Provide the common implementation for execution tools that validate
        and package requests while fail-closing critical live-capital actions.

    Args:
        name: Tool name.
        kwargs: Tool keyword arguments.
        critical: Whether the action is a critical live-capital action.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    if critical and not kwargs.get("approval_id"):
        return execution_tool_result(
            name,
            status="blocked",
            data=None,
            errors=["approval_id is required"],
            risk_level="critical",
            approval_required="human_and_risk_required",
            **execution_tool_context(kwargs),
        )
    return execution_tool_result(
        name,
        data={
            "request": {
                key: value
                for key, value in kwargs.items()
                if key not in {"request_id", "agent_name", "environment", "dry_run"}
            },
            "message": "Request validated. No live side effects executed by default.",
        },
        risk_level="critical" if critical else "medium",
        approval_required="human_and_risk_required" if critical else "audit_required",
        **execution_tool_context(kwargs),
    )


def __getattr__(name: str) -> Any:
    """Resolve lower-level execution service attributes lazily."""
    if name.startswith("__"):
        raise AttributeError(name)
    return resolve_service_attr(name, _service_modules())


__all__ = [
    "execution_approval_module",
    "execution_live_module",
    "execution_monitoring_module",
    "execution_performance_module",
    "execution_reconciliation_module",
    "execution_tool_context",
    "execution_tool_result",
    "execution_trade_governor_module",
    "package_execution_request",
]
