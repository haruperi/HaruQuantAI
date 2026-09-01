"""Governed Optimization bindings for the Optimization Coordinator.

`FR-AGENTIC-044` requires coordination to invoke only public Optimization
operations. Two things enforce that here.

First, the port takes a caller-supplied request and returns what the receiver
returned; this module constructs no `SearchRequest` and no `OptimizationResult`,
so there is no site at which Agentic could author either.

Second, robustness, stability, and overfit are each a deterministic public
operation, exposed here as their own port methods. The coordinator reads what
they returned; it never computes one, and the model is never asked for one.

Authorization runs before invocation through the shared `call_governed_tool`
wrapper owned by `FEAT-AGT-05`; this module supplies only the audit sink, so
`permissions/` stays free of a `context_memory/` dependency.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.context_memory.repository import store_memory
from app.agentic.permissions.authorization import ToolCallOutcome, call_governed_tool
from app.composition.logging import get_logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy

logger = get_logger(__name__)

# Registered tool identities this role may request. Each maps to exactly one
# public Optimization operation.
SWEEP_TOOL = "optimization.run_parameter_sweep"
ROBUSTNESS_TOOL = "optimization.calculate_robustness_score"
STABILITY_TOOL = "optimization.calculate_parameter_stability"
OVERFIT_TOOL = "optimization.detect_overfit_parameters"

# Fields a completed Optimization result must carry for a verdict to bind to
# it. These are read from `optimization.result.v1`, never derived here.
REQUIRED_RESULT_FIELDS: tuple[str, ...] = (
    "final_decision",
    "reproducibility_hash",
    "search_id",
)


@runtime_checkable
class OptimizationPort(Protocol):
    """Read-only access to the public Optimization operations this role uses."""

    def run_sweep(self, request: Mapping[str, str]) -> Mapping[str, str]:
        """Execute one receiver-owned bounded search.

        Args:
            request: Caller-supplied search request payload.

        Returns:
            The receiver's `optimization.result.v1` payload, empty when no
            search completed.
        """
        ...

    def robustness_score(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic robustness score for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's robustness evidence.
        """
        ...

    def parameter_stability(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic parameter stability for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's stability evidence.
        """
        ...

    def overfit_evidence(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic overfit evidence for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's overfit evidence.
        """
        ...


def verify_result_binding(
    plan_seed: int,
    result: Mapping[str, str],
) -> str | None:
    """Report whether a returned search result can be read at all.

    Args:
        plan_seed: Seed the plan pre-declared.
        result: The `optimization.result.v1` payload returned.

    Returns:
        The failing binding condition, or None when the result binds.
    """
    missing = tuple(field for field in REQUIRED_RESULT_FIELDS if not result.get(field))
    if missing:
        return f"result omits required evidence: {', '.join(missing)}"
    returned_seed = result.get("seed")
    if returned_seed is not None and returned_seed != str(plan_seed):
        return (
            f"result reports seed {returned_seed} but the plan pre-declared {plan_seed}"
        )
    return None


def call_optimization_tool(
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
    """Authorize and perform one governed Optimization call.

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


class _OptimizationPort:
    """Binds the real public Optimization operations.

    Constructed only by an approved composition root. Every call passes the
    caller's request through unchanged and returns the receiver's evidence
    unchanged; no broker, credential, or provider is involved.
    """

    def __init__(self, optimization: object) -> None:
        """Store the injected Optimization facade.

        Args:
            optimization: Optimization package-root facade.
        """
        self._optimization = optimization

    def run_sweep(self, request: Mapping[str, str]) -> Mapping[str, str]:
        """Execute one receiver-owned bounded search.

        Args:
            request: Caller-supplied search request payload.

        Returns:
            The receiver's result payload, unaltered.
        """
        return self._optimization.run_sweep(request)  # type: ignore[attr-defined,no-any-return]

    def robustness_score(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic robustness score for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's robustness evidence, unaltered.
        """
        return self._optimization.robustness_score(search_id)  # type: ignore[attr-defined,no-any-return]

    def parameter_stability(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic parameter stability for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's stability evidence, unaltered.
        """
        return self._optimization.parameter_stability(search_id)  # type: ignore[attr-defined,no-any-return]

    def overfit_evidence(self, search_id: str) -> Mapping[str, str]:
        """Return the deterministic overfit evidence for one search.

        Args:
            search_id: Receiver-returned search identity.

        Returns:
            The receiver's overfit evidence, unaltered.
        """
        return self._optimization.overfit_evidence(search_id)  # type: ignore[attr-defined,no-any-return]


def build_optimization_port(optimization: object) -> OptimizationPort:
    """Build the port bound to public Optimization operations.

    Args:
        optimization: Optimization package-root facade.

    Returns:
        A port satisfying `OptimizationPort`.
    """
    logger.debug("Building the optimization-coordinator port")
    return _OptimizationPort(optimization)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (OVERFIT_TOOL, ROBUSTNESS_TOOL, STABILITY_TOOL, SWEEP_TOOL)
