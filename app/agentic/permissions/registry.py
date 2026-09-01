"""Startup validation of the complete tool and agent policy registry.

Startup fails closed. A registry that names an unregistered feature, an
uncovered tool, a wildcard scope, a forbidden capability, or a role holding
authority its mandate does not grant blocks the package before any model or
tool call.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

from app.agentic.governance.models import FORBIDDEN_PERMISSION_CLASSES
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)


def _validate_tool_against_mandate(tool: ToolPolicy, mandate: FirmMandate) -> None:
    """Validate one tool policy against the mandate.

    Args:
        tool: Candidate tool policy.
        mandate: Validated firm mandate.

    Raises:
        ValueError: If the mandate does not cover the tool, or covers it with a
            different or forbidden permission class.
    """
    if tool.tool_name not in mandate.tool_scopes:
        message = f"tool {tool.tool_name} is not registered by the mandate"
        raise ValueError(message)
    granted = mandate.tool_scopes[tool.tool_name]
    if granted in FORBIDDEN_PERMISSION_CLASSES:
        message = f"tool {tool.tool_name} is granted forbidden class {granted}"
        raise ValueError(message)
    if granted != tool.permission_class:
        message = (
            f"tool {tool.tool_name} declares {tool.permission_class} but the "
            f"mandate grants {granted}"
        )
        raise ValueError(message)
    if tool.owning_feature not in mandate.enabled_features:
        message = (
            f"tool {tool.tool_name} is owned by {tool.owning_feature}, "
            "which the mandate does not enable"
        )
        raise ValueError(message)


def _validate_policy_against_mandate(
    policy: AgentPolicy,
    mandate: FirmMandate,
    tools: Mapping[str, ToolPolicy],
) -> None:
    """Validate one agent policy against the mandate and tool registry.

    Args:
        policy: Candidate agent policy.
        mandate: Validated firm mandate.
        tools: Registered tool identity to policy.

    Raises:
        ValueError: If the policy exceeds its mandate or references an
            unregistered tool.
    """
    if policy.enabled and policy.role_id not in mandate.enabled_roles:
        message = f"role {policy.role_id} is enabled outside the mandate"
        raise ValueError(message)
    for held in policy.permission_classes:
        if held in FORBIDDEN_PERMISSION_CLASSES:
            message = f"role {policy.role_id} holds forbidden class {held}"
            raise ValueError(message)
    for tool_name in policy.allowed_tools:
        tool = tools.get(tool_name)
        if tool is None:
            message = f"role {policy.role_id} allows unregistered tool {tool_name}"
            raise ValueError(message)
        if policy.role_id not in tool.eligible_roles:
            message = (
                f"role {policy.role_id} allows tool {tool_name}, which does not "
                "list it as eligible"
            )
            raise ValueError(message)
        if tool.permission_class not in policy.permission_classes:
            message = (
                f"role {policy.role_id} allows tool {tool_name} requiring "
                f"{tool.permission_class}, which the role does not hold"
            )
            raise ValueError(message)
        if tool.scope.get("environment", policy.environment) != policy.environment:
            message = (
                f"role {policy.role_id} allows tool {tool_name} scoped to a "
                "different environment"
            )
            raise ValueError(message)


def validate_policy_registry(
    mandate: FirmMandate,
    tool_policies: Iterable[ToolPolicy],
    agent_policies: Iterable[AgentPolicy],
) -> tuple[Mapping[str, ToolPolicy], Mapping[str, AgentPolicy]]:
    """Validate the complete policy registry at startup.

    Args:
        mandate: Validated firm mandate.
        tool_policies: Candidate registered tool policies.
        agent_policies: Candidate registered agent policies.

    Returns:
        The validated immutable tool and agent policy maps.

    Raises:
        ValueError: If any identity duplicates, or any policy exceeds or
            contradicts the mandate.
    """
    logger.info("Validating the Agentic policy registry")
    tools: dict[str, ToolPolicy] = {}
    for tool in tool_policies:
        if tool.tool_name in tools:
            message = f"duplicate tool identity: {tool.tool_name}"
            raise ValueError(message)
        _validate_tool_against_mandate(tool, mandate)
        tools[tool.tool_name] = tool

    policies: dict[str, AgentPolicy] = {}
    for policy in agent_policies:
        if policy.role_id in policies:
            message = f"duplicate agent policy identity: {policy.role_id}"
            raise ValueError(message)
        _validate_policy_against_mandate(policy, mandate, tools)
        policies[policy.role_id] = policy

    uncovered = sorted(set(mandate.tool_scopes) - set(tools))
    if uncovered:
        message = f"mandate registers tools with no policy: {', '.join(uncovered)}"
        raise ValueError(message)

    logger.info(
        "Agentic policy registry validated with %d tools and %d agent policies",
        len(tools),
        len(policies),
    )
    return MappingProxyType(tools), MappingProxyType(policies)


def get_forbidden_permission_classes() -> tuple[str, ...]:
    """Return the permission classes never granted to an agent.

    Returns:
        Ordered forbidden permission classes.
    """
    return tuple(sorted(FORBIDDEN_PERMISSION_CLASSES))
