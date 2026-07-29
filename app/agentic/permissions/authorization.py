"""Deny-by-default authorization of one scoped tool call.

Every facet must agree before a call is authorized: the tool must be enabled
and registered by the mandate, the role must be enabled and eligible, the role
must hold the tool's permission class and list the tool, the environment and
scope must match, the budget must not be exhausted, and any required approval
must be authenticated, unexpired, bound to the exact object, and unused.

A grant authorizes only *calling* a tool. The receiving deterministic domain
applies its own complete controls regardless, so no grant can be escalated
into a trade, an activation, or a registration.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict

from app.agentic.permissions.models import PermissionDecision, derive_object_hash
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from app.agentic.governance.models import FirmMandate
    from app.agentic.permissions.models import (
        AgentPolicy,
        DenyReason,
        ToolApprovalAttestation,
        ToolPolicy,
    )

logger = get_logger(__name__)


@runtime_checkable
class ApprovalNonceStore(Protocol):
    """Single-use enforcement for approval attestations.

    `permissions/` owns no persistence, so replay protection arrives through
    this injected port. Against the in-memory reference below the guarantee is
    process-local; a durable store supplied by a composition root extends it.
    """

    def consume(self, nonce: str) -> bool:
        """Consume one nonce exactly once.

        Args:
            nonce: Single-use replay guard.

        Returns:
            True when the nonce was unused and is now consumed.
        """
        ...

    def is_consumed(self, nonce: str) -> bool:
        """Report whether one nonce was already consumed.

        Args:
            nonce: Single-use replay guard.

        Returns:
            True when the nonce was already consumed.
        """
        ...


class _InMemoryNonceStore:
    """Deterministic process-local reference implementation of the port."""

    def __init__(self) -> None:
        """Initialise empty consumed-nonce state."""
        self._consumed: set[str] = set()

    def consume(self, nonce: str) -> bool:
        """Consume one nonce exactly once.

        Args:
            nonce: Single-use replay guard.

        Returns:
            True when the nonce was unused and is now consumed.
        """
        if nonce in self._consumed:
            return False
        self._consumed.add(nonce)
        return True

    def is_consumed(self, nonce: str) -> bool:
        """Report whether one nonce was already consumed.

        Args:
            nonce: Single-use replay guard.

        Returns:
            True when the nonce was already consumed.
        """
        return nonce in self._consumed


def build_in_memory_nonce_store() -> ApprovalNonceStore:
    """Build the deterministic process-local approval-nonce store.

    Returns:
        A store satisfying the `ApprovalNonceStore` port.
    """
    logger.debug("Building the in-memory Agentic approval-nonce store")
    return _InMemoryNonceStore()


def _deny(
    reason: DenyReason,
    tool: ToolPolicy,
    policy: AgentPolicy,
    principal_id: str,
    at_time: datetime,
) -> PermissionDecision:
    """Build one deterministic denial.

    Args:
        reason: Enumerated denial reason.
        tool: Tool evaluated.
        policy: Requesting agent policy.
        principal_id: Authenticated principal.
        at_time: Evaluation time.

    Returns:
        The denial decision.
    """
    logger.warning(
        "Denying tool %s for role %s: %s",
        tool.tool_name,
        policy.role_id,
        reason,
    )
    return PermissionDecision(
        decision_id=derive_stable_id(
            "id",
            f"deny:{tool.tool_name}:{policy.role_id}:{at_time.isoformat()}",
        ),
        allowed=False,
        reason=reason,
        tool_name=tool.tool_name,
        role_id=policy.role_id,
        principal_id=principal_id,
        environment=policy.environment,
        evaluated_at=at_time,
        grant_expires_at=None,
    )


def _check_registration(
    tool: ToolPolicy,
    policy: AgentPolicy,
    mandate: FirmMandate,
) -> DenyReason | None:
    """Check tool and role registration facts.

    Args:
        tool: Tool evaluated.
        policy: Requesting agent policy.
        mandate: Validated firm mandate.

    Returns:
        The denial reason, or None when every registration fact agrees.
    """
    checks: tuple[tuple[bool, DenyReason], ...] = (
        (not tool.enabled, "tool_disabled"),
        (not policy.enabled, "role_disabled"),
        (tool.tool_name not in mandate.tool_scopes, "tool_not_registered_by_mandate"),
        (
            mandate.tool_scopes.get(tool.tool_name) != tool.permission_class,
            "tool_not_registered_by_mandate",
        ),
        (policy.role_id not in tool.eligible_roles, "role_not_eligible_for_tool"),
        (
            tool.permission_class not in policy.permission_classes,
            "permission_class_not_held",
        ),
        (tool.tool_name not in policy.allowed_tools, "tool_not_allowed_for_role"),
    )
    for failed, reason in checks:
        if failed:
            return reason
    return None


def _check_scope(
    tool: ToolPolicy,
    policy: AgentPolicy,
    request_scope: Mapping[str, str],
) -> DenyReason | None:
    """Check environment and scope agreement.

    Args:
        tool: Tool evaluated.
        policy: Requesting agent policy.
        request_scope: Scope the caller declares for this call.

    Returns:
        The denial reason, or None when scope agrees.
    """
    tool_environment = tool.scope.get("environment")
    if tool_environment is not None and tool_environment != policy.environment:
        return "environment_mismatch"
    request_environment = request_scope.get("environment")
    if request_environment is not None and request_environment != policy.environment:
        return "environment_mismatch"
    for key, required in tool.scope.items():
        if key == "environment":
            continue
        declared = request_scope.get(key)
        if declared is not None and declared != required:
            return "scope_mismatch"
    return None


def _approval_binding_failure(
    tool: ToolPolicy,
    policy: AgentPolicy,
    attestation: ToolApprovalAttestation,
    object_hash: str,
) -> DenyReason | None:
    """Check that the approval is bound to this exact tool and object.

    Args:
        tool: Tool evaluated.
        policy: Requesting agent policy.
        attestation: Supplied approval attestation.
        object_hash: Digest of the exact object being acted on.

    Returns:
        The denial reason, or None when the binding agrees.
    """
    checks: tuple[tuple[bool, DenyReason], ...] = (
        (attestation.tool_name != tool.tool_name, "approval_object_mismatch"),
        (attestation.tool_version != tool.version, "approval_object_mismatch"),
        (attestation.object_hash != object_hash, "approval_object_mismatch"),
        (
            attestation.permission_class != tool.permission_class,
            "approval_scope_mismatch",
        ),
        (attestation.environment != policy.environment, "approval_scope_mismatch"),
    )
    for failed, reason in checks:
        if failed:
            return reason
    return None


def _approval_use_failure(
    attestation: ToolApprovalAttestation,
    principal_id: str,
    nonce_store: ApprovalNonceStore | None,
    at_time: datetime,
) -> DenyReason | None:
    """Check that the approval is unexpired, not self-issued, and unused.

    Args:
        attestation: Supplied approval attestation.
        principal_id: Authenticated requesting principal.
        nonce_store: Injected single-use enforcement port.
        at_time: Evaluation time.

    Returns:
        The denial reason, or None when the approval is valid and consumed.
    """
    if not (attestation.issued_at <= at_time < attestation.expires_at):
        return "approval_expired"
    # An agent may never approve its own work: the approving principal must be
    # distinct from the principal the agent is acting as.
    if attestation.principal_id == principal_id:
        return "self_approval"
    # Without single-use enforcement the attestation is replayable, so the call
    # fails closed rather than proceeding unprotected.
    if nonce_store is None or nonce_store.is_consumed(attestation.nonce):
        return "approval_replayed"
    if not nonce_store.consume(attestation.nonce):
        return "approval_replayed"
    return None


def _check_approval(
    tool: ToolPolicy,
    policy: AgentPolicy,
    principal_id: str,
    object_hash: str,
    attestation: ToolApprovalAttestation | None,
    nonce_store: ApprovalNonceStore | None,
    at_time: datetime,
) -> DenyReason | None:
    """Check the approval attestation when the tool requires one.

    Args:
        tool: Tool evaluated.
        policy: Requesting agent policy.
        principal_id: Authenticated requesting principal.
        object_hash: Digest of the exact object being acted on.
        attestation: Supplied approval attestation.
        nonce_store: Injected single-use enforcement port.
        at_time: Evaluation time.

    Returns:
        The denial reason, or None when the approval is valid and consumed.
    """
    if not tool.requires_approval:
        return None
    if attestation is None:
        return "approval_required"
    binding = _approval_binding_failure(tool, policy, attestation, object_hash)
    if binding is not None:
        return binding
    return _approval_use_failure(attestation, principal_id, nonce_store, at_time)


def authorize_tool_call(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool: ToolPolicy,
    principal_id: str,
    object_hash: str,
    request_scope: Mapping[str, str] | None = None,
    attestation: ToolApprovalAttestation | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    calls_used: int = 0,
    at_time: datetime | None = None,
) -> PermissionDecision:
    """Authorize one scoped tool call, denying by default.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool: Registered tool policy.
        principal_id: Authenticated requesting principal.
        object_hash: Digest of the exact object being acted on.
        request_scope: Scope the caller declares for this call.
        attestation: Approval attestation when the tool requires one.
        nonce_store: Injected single-use enforcement port.
        calls_used: Tool invocations already consumed by this task.
        at_time: Optional evaluation time; current UTC when omitted.

    Returns:
        The deterministic permission decision.
    """
    now = at_time if at_time is not None else utc_now()
    scope = request_scope if request_scope is not None else {}
    logger.info(
        "Authorizing tool %s for role %s in %s",
        tool.tool_name,
        policy.role_id,
        policy.environment,
    )

    for check in (
        _check_registration(tool, policy, mandate),
        _check_scope(tool, policy, scope),
    ):
        if check is not None:
            return _deny(check, tool, policy, principal_id, now)

    if calls_used >= policy.max_tool_calls or calls_used >= tool.max_calls_per_task:
        return _deny("budget_exhausted", tool, policy, principal_id, now)

    approval_denial = _check_approval(
        tool,
        policy,
        principal_id,
        object_hash,
        attestation,
        nonce_store,
        now,
    )
    if approval_denial is not None:
        return _deny(approval_denial, tool, policy, principal_id, now)

    # A grant is time-bounded and enforced at each invocation, not only at
    # issue. An approved call inherits the attestation's expiry; an ordinary
    # read inherits the tool's own call timeout.
    grant_expiry = (
        attestation.expires_at
        if attestation is not None
        else now + timedelta(seconds=tool.timeout_seconds)
    )
    logger.info(
        "Granted tool %s to role %s until %s",
        tool.tool_name,
        policy.role_id,
        grant_expiry.isoformat(),
    )
    return PermissionDecision(
        decision_id=derive_stable_id(
            "id",
            f"allow:{tool.tool_name}:{policy.role_id}:{now.isoformat()}",
        ),
        allowed=True,
        reason="allowed",
        tool_name=tool.tool_name,
        role_id=policy.role_id,
        principal_id=principal_id,
        environment=policy.environment,
        evaluated_at=now,
        grant_expires_at=grant_expiry,
    )


# --------------------------------------------------------------------------
# Governed tool-call wrapper
#
# `docs/dev/agentic_firm/11_tool_standard.md` places authorization before
# invocation in the tool call lifecycle, and `FR-AGENTIC-013` assigns that
# enforcement to this feature. The wrapper lives here so every registered agent
# package shares one implementation rather than repeating it.
#
# The audit sink is an injected hook, not a direct store call: `permissions/`
# owns authorization and must not depend on `context_memory/`.
# --------------------------------------------------------------------------

# A bounded result keeps an oversized or unbounded receiver payload out of
# model context.
MAX_TOOL_RESULT_ENTRIES = 64
MAX_TOOL_RESULT_VALUE_CHARS = 2_000


class ToolCallOutcome(BaseModel):
    """The bounded outcome of one governed tool call.

    Attributes:
        tool_name: Tool identity invoked or denied.
        allowed: Whether authorization permitted the call.
        denial_reason: Enumerated denial reason when refused.
        payload: Bounded receiver result when allowed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    tool_name: str
    allowed: bool
    denial_reason: str | None = None
    payload: Mapping[str, str] | None = None


def bound_tool_result(
    value: Mapping[str, object],
    tool_name: str,
) -> Mapping[str, str]:
    """Bound and validate a receiver result as untrusted input.

    Args:
        value: Raw receiver result.
        tool_name: Tool identity that produced it.

    Returns:
        A bounded mapping safe to place in model context.

    Raises:
        ValueError: If the result exceeds the bound.
        TypeError: If the result is not a string mapping.
    """
    if len(value) > MAX_TOOL_RESULT_ENTRIES:
        message = f"{tool_name} returned more than {MAX_TOOL_RESULT_ENTRIES} entries"
        raise ValueError(message)
    bounded: dict[str, str] = {}
    for key, item in sorted(value.items(), key=lambda entry: str(entry[0])):
        if not isinstance(item, str):
            message = f"{tool_name} returned a non-string result entry"
            raise TypeError(message)
        bounded[str(key)] = item[:MAX_TOOL_RESULT_VALUE_CHARS]
    return bounded


def call_governed_tool(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool: ToolPolicy,
    principal_id: str,
    task_id: str,
    request_scope: Mapping[str, str],
    receiver_call: Callable[[], Mapping[str, object]],
    at_time: datetime,
    attestation: ToolApprovalAttestation | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_hook: Callable[[str, str], None] | None = None,
    calls_used: int = 0,
) -> ToolCallOutcome:
    """Authorize and perform one governed tool call.

    Authorization runs before invocation, so a denied call never reaches the
    receiver at all.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool: Registered tool policy.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        request_scope: Scope declared for this call.
        receiver_call: Zero-argument callable invoking the receiver operation.
        at_time: Call time.
        attestation: Approval attestation when the tool requires one.
        nonce_store: Injected single-use approval enforcement.
        audit_hook: Optional sink receiving the tool identity and outcome.
        calls_used: Tool invocations already consumed by this task.

    Returns:
        The bounded outcome, denied or completed.
    """
    decision = authorize_tool_call(
        mandate,
        policy,
        tool,
        principal_id,
        derive_object_hash({"task": task_id, "tool": tool.tool_name}),
        request_scope=dict(request_scope),
        attestation=attestation,
        nonce_store=nonce_store,
        calls_used=calls_used,
        at_time=at_time,
    )
    if not decision.allowed:
        if audit_hook is not None:
            audit_hook(tool.tool_name, "denied")
        return ToolCallOutcome(
            tool_name=tool.tool_name,
            allowed=False,
            denial_reason=decision.reason,
            payload=None,
        )

    logger.info(
        "Invoking governed tool %s for role %s",
        tool.tool_name,
        policy.role_id,
    )
    payload = bound_tool_result(receiver_call(), tool.tool_name)
    if audit_hook is not None:
        audit_hook(tool.tool_name, "completed")
    return ToolCallOutcome(
        tool_name=tool.tool_name,
        allowed=True,
        denial_reason=None,
        payload=payload,
    )
