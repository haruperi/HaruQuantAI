"""Governed Simulation bindings for the Experiment Designer.

`FR-AGENTIC-041` requires that coordination use only the public Simulation
request and result contracts and never invent or alter a result. Two things
enforce that here.

First, the port takes a caller-supplied request and returns what the receiver
returned; this module constructs no request and no result, so there is no site
at which Agentic could author either.

Second, `verify_result_binding` checks that the returned lineage corresponds to
the request that was actually submitted. A result that does not bind is a fault
to report, not a discrepancy to reconcile.

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
# public Simulation operation.
BACKTEST_TOOL = "simulation.run_backtest"
RUN_LOOKUP_TOOL = "simulation.resolve_idempotent_run"

# Lineage a completed Simulation result must carry for a conclusion to be
# traceable. These are read from `simulation.result.v1`, never derived here.
REQUIRED_LINEAGE: tuple[str, ...] = (
    "artifact_manifest_ref",
    "config_hash",
    "engine_version",
    "journal_ref",
    "request_hash",
    "run_id",
)


@runtime_checkable
class SimulationPort(Protocol):
    """Read-only access to the public Simulation operations this role may use."""

    def submit_backtest(self, request: Mapping[str, str]) -> Mapping[str, str]:
        """Execute one receiver-owned backtest request.

        Args:
            request: Caller-supplied `simulation.backtest_request.v1` payload.

        Returns:
            The receiver's `simulation.result.v1` payload, empty when no run
            completed.
        """
        ...

    def resolve_run(self, run_id: str) -> Mapping[str, str]:
        """Resolve one previously executed run by identity.

        Args:
            run_id: Receiver-returned run identity.

        Returns:
            The receiver's recorded run, empty when unknown.
        """
        ...


def verify_result_binding(
    request: Mapping[str, str],
    result: Mapping[str, str],
) -> str | None:
    """Report whether a returned result belongs to the submitted request.

    Args:
        request: The `simulation.backtest_request.v1` payload submitted.
        result: The `simulation.result.v1` payload returned.

    Returns:
        The failing binding condition, or None when the result binds.
    """
    missing = tuple(field for field in REQUIRED_LINEAGE if not result.get(field))
    if missing:
        return f"result omits required lineage: {', '.join(missing)}"

    submitted = request.get("config_hash")
    returned = result.get("config_hash")
    if submitted and returned and submitted != returned:
        return (
            f"result config_hash {returned} does not match the submitted "
            f"request config_hash {submitted}"
        )

    status = result.get("status")
    if status is not None and status != "completed":
        return f"result reports status {status} rather than a completed run"
    return None


def call_simulation_tool(
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
    """Authorize and perform one governed Simulation call.

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


class _SimulatorPort:
    """Binds the real Simulation public operations.

    Constructed only by an approved composition root. Every call passes the
    caller's request through unchanged and returns the receiver's result
    unchanged; no broker, credential, or provider is involved.
    """

    def __init__(self, simulator: object) -> None:
        """Store the injected Simulation facade.

        Args:
            simulator: Simulation package-root facade.
        """
        self._simulator = simulator

    def submit_backtest(self, request: Mapping[str, str]) -> Mapping[str, str]:
        """Execute one receiver-owned backtest request.

        Args:
            request: Caller-supplied backtest request payload.

        Returns:
            The receiver's result payload, unaltered.
        """
        return self._simulator.submit_backtest(request)  # type: ignore[attr-defined,no-any-return]

    def resolve_run(self, run_id: str) -> Mapping[str, str]:
        """Resolve one previously executed run by identity.

        Args:
            run_id: Receiver-returned run identity.

        Returns:
            The receiver's recorded run, unaltered.
        """
        return self._simulator.resolve_run(run_id)  # type: ignore[attr-defined,no-any-return]


def build_simulator_port(simulator: object) -> SimulationPort:
    """Build the Simulation port bound to public Simulation operations.

    Args:
        simulator: Simulation package-root facade.

    Returns:
        A port satisfying `SimulationPort`.
    """
    logger.debug("Building the experiment-designer Simulation port")
    return _SimulatorPort(simulator)


def get_registered_tool_names() -> tuple[str, ...]:
    """Return the tool identities this role may request.

    Returns:
        Ordered registered tool identities.
    """
    return (BACKTEST_TOOL, RUN_LOOKUP_TOOL)
