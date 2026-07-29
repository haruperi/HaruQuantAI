"""Governed Indicators-registry bindings for the Coder.

Whether an indicator exists is a fact the Indicators registry owns, so it is
read through the governed authorization path rather than imported directly.
The model never asserts that an indicator is registered; the receiver answers.

This module is not in the canonical §4.16 file list. It exists because the
alternative — importing `app.services.indicators` directly from `agent.py` —
would bypass the permission enforcement point that every other receiver call in
this domain traverses.

Authorization runs before invocation through the shared `call_governed_tool`
wrapper owned by `FEAT-AGT-05`; this module supplies only the audit sink, so
`permissions/` stays free of a `context_memory/` dependency.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.context_memory.repository import store_memory
from app.agentic.permissions.authorization import ToolCallOutcome, call_governed_tool
from app.utils import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)

# Registered tool identities this role may request.
INDICATOR_REGISTRY_TOOL = "indicators.list_indicators"


@runtime_checkable
class IndicatorRegistryPort(Protocol):
    """Read-only access to the official indicator registry."""

    def list_registered_indicators(self) -> Mapping[str, str]:
        """Return every registered indicator and its version.

        Returns:
            Indicator identifier to registered version.
        """
        ...


def call_registry_tool(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool: ToolPolicy,
    principal_id: str,
    task_id: str,
    request_scope: Mapping[str, str],
    receiver_call: Callable[[], Mapping[str, object]],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    calls_used: int = 0,
) -> ToolCallOutcome:
    """Authorize and perform one governed registry lookup.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool: Registered tool policy.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        request_scope: Scope declared for this call.
        receiver_call: Zero-argument callable invoking the receiver operation.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        calls_used: Tool invocations already consumed by this task.

    Returns:
        The bounded outcome, denied or completed.
    """

    def audit_hook(tool_name: str, outcome: str) -> None:
        """Record one redacted tool-call audit entry.

        Args:
            tool_name: Tool identity invoked.
            outcome: Enumerated call outcome.
        """
        if audit_store is None:
            return
        # The ordinal keeps two calls to the same tool in the same instant
        # distinguishable; without it they would share a content identity.
        store_memory(
            audit_store,
            "audit",
            task_id,
            policy.role_id,
            {
                "tool": tool_name,
                "outcome": outcome,
                "call": str(calls_used + 1),
            },
            {"environment": "sandbox"},
            "audit-730d",
            at_time=at_time,
        )

    return call_governed_tool(
        mandate,
        policy,
        tool,
        principal_id,
        task_id,
        request_scope,
        receiver_call,
        at_time,
        nonce_store=nonce_store,
        audit_hook=audit_hook,
        calls_used=calls_used,
    )


class _IndicatorsRegistryPort:
    """Binds the real Indicators registry.

    Constructed only by an approved composition root. The single call is a
    read-only listing through a documented public API; no credential, broker,
    or provider is involved.
    """

    def __init__(self, indicators: object) -> None:
        """Store the injected Indicators facade.

        Args:
            indicators: Indicators package-root facade.
        """
        self._indicators = indicators

    def list_registered_indicators(self) -> Mapping[str, str]:
        """Return every registered indicator and its version.

        Returns:
            Indicator identifier to registered version.
        """
        return self._indicators.list_registered_indicators()  # type: ignore[attr-defined,no-any-return]


def build_indicator_registry_port(indicators: object) -> IndicatorRegistryPort:
    """Build the registry port bound to Indicators public operations.

    Args:
        indicators: Indicators package-root facade.

    Returns:
        A port satisfying `IndicatorRegistryPort`.
    """
    logger.debug("Building the coder indicator-registry port")
    return _IndicatorsRegistryPort(indicators)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (INDICATOR_REGISTRY_TOOL,)
