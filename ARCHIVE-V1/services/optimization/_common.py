"""Shared optimization-service helpers.

Purpose:
    Provide only generic helpers reused by multiple optimization files:
    lazy service-attribute resolution, strategy-class normalization, and the
    standard result/request packaging helpers used by agent-facing tools.

Classes and functions:
    service_strategy_class: Function. Normalize strategy class factories.
    optimization_tool_result: Function. Build a standard HaruQuant result envelope.
    optimization_tool_context: Function. Extract common tool context fields.
    optimization_business_payload: Function. Strip context fields from a request.
    package_optimization_request: Function. Package a deterministic optimization request.
    __getattr__: Function. Resolve lower-level optimization attributes lazily.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import Any
from uuid import uuid4

from app.services import resolve_service_attr, service_modules
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

_SERVICE_MODULES = tuple(
    module_name
    for module_name in service_modules("app.services.optimization")
    if module_name
    not in {"app.services.optimization", "app.services.optimization._common"}
)


def service_strategy_class(strategy_class: Any) -> Any:
    """Normalize a strategy class or class factory.

    Purpose:
        Let multiple optimization wrappers accept either a concrete strategy
        class or a callable that returns one.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        May call a provided factory to resolve a class.

    Inputs:
        strategy_class: Strategy class or callable returning one.

    Returns:
        Strategy class suitable for optimization methods.
    """
    if callable(strategy_class) and not isinstance(strategy_class, type):
        maybe_class = strategy_class()
        if isinstance(maybe_class, type):
            return maybe_class
    return getattr(strategy_class, "_service_strategy_class", strategy_class)


def optimization_tool_result(
    tool_name: str,
    *,
    data: dict[str, Any] | None = None,
    status: str = "success",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    side_effects: list[str] | None = None,
) -> dict[str, Any]:
    """Build the standard HaruQuant result envelope for optimization tools.

    Purpose:
        Centralize the auditable envelope used by agent-facing optimization and
        robustness tools.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        tool_name: Name of the tool creating the result.
        data: Business payload.
        status: Result status.
        errors: Validation or runtime errors.
        warnings: Non-blocking warnings.
        request_id: Optional external trace/request ID.
        agent_name: Name of the calling agent.
        environment: Runtime environment.
        dry_run: Whether the operation is simulated.
        side_effects: Side effects created by the operation.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    _ = (
        agent_name,
        environment,
        dry_run,
        warnings,
        side_effects,
        uuid4,
        datetime,
        timezone,
    )
    error_list = errors or []
    normalized_status = "success" if status == "success" and not error_list else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="optimization",
            tool_risk_level="medium",
            read_only=False,
        ),
        status=normalized_status,
        message=(
            "Optimization tool executed successfully."
            if normalized_status == "success"
            else "Optimization tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "TOOL_EXECUTION_FAILED",
            "details": "; ".join(error_list) or "Optimization tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def optimization_tool_context(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract common optimization tool context fields.

    Purpose:
        Keep individual tools focused on business behavior while using one
        standard context shape.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        kwargs: Tool keyword arguments.

    Returns:
        Context dictionary accepted by optimization_tool_result.
    """
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name"),
        "environment": kwargs.get("environment", "development"),
        "dry_run": kwargs.get("dry_run", True),
    }


def optimization_business_payload(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Strip common context fields from optimization request payloads.

    Purpose:
        Preserve business request data without duplicating audit context fields.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.

    Inputs:
        kwargs: Tool keyword arguments.

    Returns:
        Business-only request payload.
    """
    return {
        key: value
        for key, value in kwargs.items()
        if key not in {"request_id", "agent_name", "environment", "dry_run"}
    }


def package_optimization_request(
    tool_name: str, kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Package an optimization request without executing compute-heavy jobs.

    Purpose:
        Provide a deterministic dry-run request package for optimization and
        robustness workflows.

    Tool class:
        write_controlled

    Risk level:
        medium

    Approval required:
        audit_required

    Side effects:
        None; returns a packaged request.

    Inputs:
        tool_name: Tool name.
        kwargs: Tool keyword arguments.

    Returns:
        Standard HaruQuant tool result dictionary.
    """
    return optimization_tool_result(
        tool_name,
        data={
            "request": optimization_business_payload(kwargs),
            "created_at": datetime.now(UTC).isoformat(),
        },
        **optimization_tool_context(kwargs),
    )


def __getattr__(name: str) -> Any:
    """Resolve lower-level optimization service attributes lazily."""
    if name.startswith("__"):
        raise AttributeError(name)
    return resolve_service_attr(name, _SERVICE_MODULES)


__all__ = [
    "optimization_business_payload",
    "optimization_tool_context",
    "optimization_tool_result",
    "package_optimization_request",
    "service_strategy_class",
]
