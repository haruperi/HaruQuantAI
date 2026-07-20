"""Shared helpers for the risk service package.

Purpose:
    Provide generic helpers reused by multiple risk service files. This module
    intentionally avoids specialized risk tool implementations.

Functions:
    risk_tool_result: Build a standard HaruQuant tool result envelope.
    risk_tool_context: Extract standard request context from keyword inputs.
    risk_limit_check: Build a deterministic max/min threshold check result.
    risk_business_payload: Return non-control fields from a tool request.
    risk_policy_module: Return the risk policy service module.
    risk_portfolio_module: Return the risk portfolio service module.
    risk_safety_module: Return the risk safety service module.
    risk_live_module: Return the live risk service module.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import ModuleType
from typing import Any
from uuid import uuid4

from app.services import load_service_module, resolve_service_attr, service_modules
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

_PRIORITY_MODULES = (
    "app.services.risk.metrics.base",
    "app.services.risk.scoring.base",
    "app.services.risk.policy",
    "app.services.risk.policy.compliance_rollout",
    "app.services.risk.portfolio",
    "app.services.risk.safety",
)
_SERVICE_MODULES = _PRIORITY_MODULES + tuple(
    module
    for module in service_modules("app.services.risk")
    if module not in _PRIORITY_MODULES
    and module not in {"app.services.risk", "app.services.risk._common"}
    and not module.startswith("app.services.risk.live")
)


def risk_tool_result(
    tool_name: str,
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
    """Build the standard result envelope for risk service tool functions."""
    _ = (
        agent_name,
        environment,
        dry_run,
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
            tool_name=tool_name,
            tool_category="risk",
            tool_risk_level=risk_level,
            read_only=True,
        ),
        status=normalized_status,
        message=(
            "Risk tool executed successfully."
            if normalized_status == "success"
            else "Risk tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "VALIDATION_FAILED",
            "details": "; ".join(error_list) or "Risk validation failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def risk_tool_context(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Extract common request metadata from a risk tool keyword payload."""
    return {
        "request_id": kwargs.get("request_id"),
        "agent_name": kwargs.get("agent_name"),
        "environment": kwargs.get("environment", "development"),
        "dry_run": kwargs.get("dry_run", True),
    }


def risk_business_payload(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return business inputs after removing standard control fields."""
    control_fields = {"request_id", "agent_name", "environment", "dry_run"}
    return {key: value for key, value in kwargs.items() if key not in control_fields}


def risk_limit_check(
    tool_name: str,
    *,
    value: float,
    limit: float,
    comparator: str = "max",
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Evaluate a deterministic risk threshold and return a standard result."""
    passed = value <= limit if comparator == "max" else value >= limit
    return risk_tool_result(
        tool_name,
        status="success" if passed else "rejected",
        data={"passed": passed, "value": value, "limit": limit},
        errors=[] if passed else [f"{tool_name} failed"],
        request_id=request_id,
        agent_name=agent_name,
        environment=environment,
        dry_run=dry_run,
    )


def risk_policy_module() -> ModuleType:
    """Return the risk policy service module."""
    module: ModuleType = load_service_module("app.services.risk.policy")
    return module


def risk_portfolio_module() -> ModuleType:
    """Return the risk portfolio service module."""
    module: ModuleType = load_service_module("app.services.risk.portfolio")
    return module


def risk_safety_module() -> ModuleType:
    """Return the risk safety service module."""
    module: ModuleType = load_service_module("app.services.risk.safety")
    return module


def risk_live_module() -> ModuleType:
    """Return the live risk service module."""
    module: ModuleType = load_service_module("app.services.risk.live")
    return module


def __getattr__(name: str) -> Any:
    """Resolve lower-level risk service attributes lazily."""
    if name.startswith("__"):
        raise AttributeError(name)
    return resolve_service_attr(name, _SERVICE_MODULES)


__all__ = [
    "risk_business_payload",
    "risk_limit_check",
    "risk_live_module",
    "risk_policy_module",
    "risk_portfolio_module",
    "risk_safety_module",
    "risk_tool_context",
    "risk_tool_result",
]
