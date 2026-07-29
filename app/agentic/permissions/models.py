"""Tool, agent, approval, and permission-decision contracts.

Permission is deny-by-default. A tool exists for an agent only if it is
registered here, covered by the mandate, and held by the requesting role's
policy. `controlled_mutation` and `critical` classes are unrepresentable, so
no broker mutation, kill-switch clearance, or production deployment can be
described by a registered Agentic tool at all.

`ToolApprovalAttestation` is Agentic-owned and distinct from the Risk-owned
`ApprovalAttestation v1`. Risk's contract authorizes risk decisions; this one
authorizes a *tool grant*, and it adds the exact object hash, single-use nonce,
and signature that `FR-AGENTIC-014` requires and Risk's shape does not carry.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    field_serializer,
    field_validator,
    model_validator,
)

from app.agentic.governance.models import (
    PermissionClass,  # noqa: TC001 - pydantic resolves annotations at runtime
)
from app.utils import canonical_digest, get_logger

logger = get_logger(__name__)

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64
_WILDCARDS: frozenset[str] = frozenset({"*", "all", "any", ""})

# A tool that changes governed deterministic or external state, or that touches
# a broker, credential, kill switch, or deployment, is never registered for an
# agent (`FR-AGENTIC-015`).
FORBIDDEN_TOOL_TOKENS: frozenset[str] = frozenset(
    {
        "place_order",
        "cancel_order",
        "close_position",
        "modify_position",
        "modify_order",
        "clear_kill_switch",
        "activate_kill_switch",
        "override_mandate",
        "approve_own",
        "deploy",
        "rotate_key",
        "credential",
    },
)

FORBIDDEN_RECEIVER_DOMAINS: frozenset[str] = frozenset({"brokers", "broker"})

SideEffectClass = Literal[
    "read_only", "deterministic_compute", "staging_write", "proposal_submission"
]

DenyReason = Literal[
    "allowed",
    "tool_disabled",
    "tool_not_registered_by_mandate",
    "role_disabled",
    "role_not_eligible_for_tool",
    "permission_class_not_held",
    "tool_not_allowed_for_role",
    "environment_mismatch",
    "scope_mismatch",
    "principal_mismatch",
    "approval_required",
    "approval_expired",
    "approval_replayed",
    "approval_object_mismatch",
    "approval_scope_mismatch",
    "self_approval",
    "budget_exhausted",
]


def _text(value: str, field: str, *, limit: int = _MAX_SHORT_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


def _utc(value: datetime, field: str) -> datetime:
    """Validate an aware UTC timestamp.

    Args:
        value: Candidate timestamp.
        field: Safe field label for validation.

    Returns:
        Validated UTC timestamp.

    Raises:
        ValueError: If the value is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field} must be aware UTC"
        raise ValueError(message)
    return value


def _hash(value: str, field: str) -> str:
    """Validate lowercase SHA-256 hexadecimal.

    Args:
        value: Candidate digest.
        field: Safe field label for validation.

    Returns:
        Validated digest.

    Raises:
        ValueError: If the digest shape is invalid.
    """
    if _SHA256.fullmatch(value) is None:
        message = f"{field} must be lowercase SHA-256 hexadecimal"
        raise ValueError(message)
    return value


def _scope(value: Mapping[str, str], field: str) -> Mapping[str, str]:
    """Validate and freeze a governed scope mapping.

    Args:
        value: Candidate scope mapping.
        field: Safe field label for validation.

    Returns:
        Deterministically ordered read-only scope mapping.

    Raises:
        ValueError: If the mapping is empty, oversized, or wildcard-scoped.
    """
    if not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} keys"
        raise ValueError(message)
    frozen: dict[str, str] = {}
    for key, item in sorted(value.items()):
        safe_key = _text(key, field)
        safe_value = _text(item, field)
        if safe_value.strip().lower() in _WILDCARDS:
            message = f"{field} must not declare a wildcard scope"
            raise ValueError(message)
        frozen[safe_key] = safe_value
    return MappingProxyType(frozen)


def _tuple(
    value: tuple[str, ...], field: str, *, required: bool = True
) -> tuple[str, ...]:
    """Validate a bounded ordered tuple of trimmed entries.

    Args:
        value: Candidate entries.
        field: Safe field label for validation.
        required: Whether at least one entry is required.

    Returns:
        Validated entries.

    Raises:
        ValueError: If the tuple is empty when required, oversized, or duplicated.
    """
    if required and not value:
        message = f"{field} is required"
        raise ValueError(message)
    if len(value) > _MAX_ITEMS:
        message = f"{field} must not exceed {_MAX_ITEMS} entries"
        raise ValueError(message)
    validated = tuple(_text(item, field) for item in value)
    if len(set(validated)) != len(validated):
        message = f"{field} must not repeat an entry"
        raise ValueError(message)
    return validated


class _PermissionModel(BaseModel):
    """Private strict immutable behaviour shared by permission contracts."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )


class ToolPolicy(_PermissionModel):
    """One registered narrow typed adapter to a public deterministic operation.

    Attributes:
        tool_name: Stable tool identity.
        version: Exact tool version.
        owning_feature: Canonical owning `FEAT-AGT-NN` feature.
        receiver_domain: Deterministic receiver domain.
        public_operation: Receiver-owned public operation invoked.
        request_schema_id: Namespaced request schema identity.
        result_schema_id: Namespaced result schema identity.
        permission_class: Permission class the tool requires.
        side_effect_class: Declared side-effect class.
        eligible_roles: Role identities permitted to request this tool.
        scope: Environment, asset, account, and data scope.
        idempotent: Whether repeated invocation is safe.
        requires_approval: Whether an approval attestation is mandatory.
        max_input_bytes: Maximum request size.
        max_output_bytes: Maximum result size.
        timeout_seconds: Maximum call duration.
        max_calls_per_task: Maximum invocations within one task.
        enabled: Whether the tool may be invoked.
    """

    tool_name: str
    version: str
    owning_feature: str
    receiver_domain: str
    public_operation: str
    request_schema_id: str
    result_schema_id: str
    permission_class: PermissionClass
    side_effect_class: SideEffectClass
    eligible_roles: tuple[str, ...]
    scope: Mapping[str, str]
    idempotent: bool
    requires_approval: bool
    max_input_bytes: int
    max_output_bytes: int
    timeout_seconds: int
    max_calls_per_task: int
    enabled: bool

    @field_validator(
        "tool_name",
        "version",
        "owning_feature",
        "public_operation",
        "request_schema_id",
        "result_schema_id",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded tool reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "tool policy reference")

    @field_validator("receiver_domain")
    @classmethod
    def _validate_receiver(cls, value: str) -> str:
        """Reject a receiver domain Agentic may never reach.

        Args:
            value: Candidate receiver domain.

        Returns:
            Validated receiver domain.

        Raises:
            ValueError: If the receiver is a broker domain.
        """
        domain = _text(value, "receiver_domain")
        if domain.lower() in FORBIDDEN_RECEIVER_DOMAINS:
            message = (
                "Agentic has no Brokers dependency; a broker tool is never registered"
            )
            raise ValueError(message)
        return domain

    @field_validator("eligible_roles")
    @classmethod
    def _validate_roles(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the eligible role identities.

        Args:
            value: Candidate role identities.

        Returns:
            Validated role identities.
        """
        return _tuple(value, "eligible_roles")

    @field_validator("scope")
    @classmethod
    def _validate_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the governed tool scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Frozen ordered scope mapping.
        """
        return _scope(value, "tool scope")

    @field_validator(
        "max_input_bytes",
        "max_output_bytes",
        "timeout_seconds",
        "max_calls_per_task",
    )
    @classmethod
    def _validate_bound(cls, value: int) -> int:
        """Validate one positive tool bound.

        Args:
            value: Candidate bound.

        Returns:
            Validated bound.

        Raises:
            ValueError: If the bound is not positive.
        """
        if value <= 0:
            message = "tool policy bound must be positive"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def _validate_capability(self) -> Self:
        """Reject a tool naming a capability never granted to an agent.

        Returns:
            The validated tool policy.

        Raises:
            ValueError: If the tool names a forbidden capability, or a
                staging/proposal side effect lacks an approval requirement.
        """
        subject = f"{self.tool_name} {self.public_operation}".lower()
        for token in FORBIDDEN_TOOL_TOKENS:
            if token in subject:
                message = (
                    f"tool {self.tool_name} names {token}, which is never "
                    "registered for an agent"
                )
                raise ValueError(message)
        if (
            self.side_effect_class in {"staging_write", "proposal_submission"}
            and not self.requires_approval
        ):
            message = (
                f"tool {self.tool_name} declares {self.side_effect_class} and "
                "must require an approval attestation"
            )
            raise ValueError(message)
        return self

    @field_serializer("scope", mode="plain")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the tool scope deterministically.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class AgentPolicy(_PermissionModel):
    """The capability envelope one registered role holds.

    Attributes:
        role_id: Registered role identity.
        role_version: Exact role manifest version.
        permission_classes: Permission classes the role holds.
        allowed_tools: Tool identities the role may request.
        environment: Environment the policy applies to.
        max_tool_calls: Maximum tool invocations per task.
        max_cost: Maximum cost per task.
        enabled: Whether the role may request any tool.
    """

    role_id: str
    role_version: str
    permission_classes: tuple[PermissionClass, ...]
    allowed_tools: tuple[str, ...]
    environment: str
    max_tool_calls: int
    max_cost: Decimal
    enabled: bool

    @field_validator("role_id", "role_version", "environment")
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded agent-policy reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "agent policy reference")

    @field_validator("permission_classes")
    @classmethod
    def _validate_classes(
        cls,
        value: tuple[PermissionClass, ...],
    ) -> tuple[PermissionClass, ...]:
        """Validate the held permission classes.

        Args:
            value: Candidate permission classes.

        Returns:
            Validated permission classes.

        Raises:
            ValueError: If the tuple is empty or repeated.
        """
        if not value:
            message = "permission_classes is required"
            raise ValueError(message)
        if len(set(value)) != len(value):
            message = "permission_classes must not repeat a class"
            raise ValueError(message)
        return value

    @field_validator("allowed_tools")
    @classmethod
    def _validate_tools(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the allowed tool identities.

        Args:
            value: Candidate tool identities.

        Returns:
            Validated tool identities.
        """
        return _tuple(value, "allowed_tools", required=False)

    @field_validator("max_tool_calls")
    @classmethod
    def _validate_call_bound(cls, value: int) -> int:
        """Validate the per-task tool-call bound.

        Args:
            value: Candidate bound.

        Returns:
            Validated bound.

        Raises:
            ValueError: If the bound is negative.
        """
        if value < 0:
            message = "max_tool_calls must be non-negative"
            raise ValueError(message)
        return value

    @field_validator("max_cost")
    @classmethod
    def _validate_cost(cls, value: Decimal) -> Decimal:
        """Validate the per-task cost bound.

        Args:
            value: Candidate bound.

        Returns:
            Validated bound.

        Raises:
            ValueError: If the bound is non-finite or negative.
        """
        if not value.is_finite() or value < 0:
            message = "max_cost must be finite and non-negative"
            raise ValueError(message)
        return value

    @field_serializer("max_cost", mode="plain")
    def _serialize_cost(self, value: Decimal) -> str:
        """Serialize the cost bound without precision loss.

        Args:
            value: Exact cost bound.

        Returns:
            Canonical decimal string.
        """
        return str(value)


class ToolApprovalAttestation(_PermissionModel):
    """One authenticated, single-use, scoped approval for a tool grant.

    An agent cannot manufacture one: it carries an exact object hash, a
    single-use nonce, and a signature or trusted identity proof supplied by an
    authenticated principal outside the model boundary.

    Attributes:
        attestation_id: Stable attestation identity.
        principal_id: Authenticated approving principal.
        permission_class: Permission class approved.
        tool_name: Tool identity approved.
        tool_version: Exact tool version approved.
        object_hash: Digest of the exact object approved.
        workflow_id: Workflow trace identity.
        run_id: Run the approval applies to.
        environment: Environment the approval applies to.
        scope: Account and asset scope approved.
        issued_at: UTC issue time.
        expires_at: UTC expiry time.
        nonce: Single-use replay guard.
        policy_version: Permission-policy version at issue.
        signature: Signature or trusted identity proof.
    """

    attestation_id: str
    principal_id: str
    permission_class: PermissionClass
    tool_name: str
    tool_version: str
    object_hash: str
    workflow_id: str
    run_id: str
    environment: str
    scope: Mapping[str, str]
    issued_at: datetime
    expires_at: datetime
    nonce: str
    policy_version: str
    signature: str

    @field_validator(
        "attestation_id",
        "principal_id",
        "tool_name",
        "tool_version",
        "workflow_id",
        "run_id",
        "environment",
        "nonce",
        "policy_version",
        "signature",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded attestation reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "attestation reference")

    @field_validator("object_hash")
    @classmethod
    def _validate_object_hash(cls, value: str) -> str:
        """Validate the approved-object digest.

        Args:
            value: Candidate digest.

        Returns:
            Validated digest.
        """
        return _hash(value, "object_hash")

    @field_validator("issued_at", "expires_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate one attestation timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "attestation timestamp")

    @field_validator("scope")
    @classmethod
    def _validate_scope(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate and freeze the approved scope.

        Args:
            value: Candidate scope mapping.

        Returns:
            Frozen ordered scope mapping.
        """
        return _scope(value, "attestation scope")

    @model_validator(mode="after")
    def _validate_window(self) -> Self:
        """Validate the attestation validity window.

        Returns:
            The validated attestation.

        Raises:
            ValueError: If the window is inverted.
        """
        if self.issued_at >= self.expires_at:
            message = "issued_at must precede expires_at"
            raise ValueError(message)
        return self

    @field_serializer("scope", mode="plain")
    def _serialize_scope(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the approved scope deterministically.

        Args:
            value: Frozen scope mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


class PermissionDecision(_PermissionModel):
    """The deterministic outcome of one authorization evaluation.

    Attributes:
        decision_id: Stable decision identity.
        allowed: Whether the call is authorized.
        reason: Enumerated decision reason.
        tool_name: Tool evaluated.
        role_id: Requesting role.
        principal_id: Authenticated principal.
        environment: Environment evaluated.
        evaluated_at: UTC evaluation time.
        grant_expires_at: Expiry of the issued grant when allowed.
    """

    decision_id: str
    allowed: bool
    reason: DenyReason
    tool_name: str
    role_id: str
    principal_id: str
    environment: str
    evaluated_at: datetime
    grant_expires_at: datetime | None = None

    @field_validator(
        "decision_id",
        "tool_name",
        "role_id",
        "principal_id",
        "environment",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one bounded decision reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "permission decision reference")

    @field_validator("evaluated_at")
    @classmethod
    def _validate_time(cls, value: datetime) -> datetime:
        """Validate the evaluation timestamp.

        Args:
            value: Candidate timestamp.

        Returns:
            Validated UTC timestamp.
        """
        return _utc(value, "evaluated_at")

    @model_validator(mode="after")
    def _validate_decision(self) -> Self:
        """Validate that the decision and reason agree.

        Returns:
            The validated decision.

        Raises:
            ValueError: If an allow carries a denial reason or vice versa.
        """
        if self.allowed and self.reason != "allowed":
            message = "an allowed decision must carry the allowed reason"
            raise ValueError(message)
        if not self.allowed and self.reason == "allowed":
            message = "a denied decision must carry a denial reason"
            raise ValueError(message)
        if not self.allowed and self.grant_expires_at is not None:
            message = "a denied decision must not issue a grant"
            raise ValueError(message)
        return self


def build_tool_policy(fields: Mapping[str, object]) -> ToolPolicy:
    """Build one registered tool policy.

    Args:
        fields: Complete tool-policy fields.

    Returns:
        A validated immutable tool policy.
    """
    logger.debug("Building tool policy %s", fields.get("tool_name"))
    return ToolPolicy.model_validate(fields)


def build_agent_policy(fields: Mapping[str, object]) -> AgentPolicy:
    """Build one registered agent policy.

    Args:
        fields: Complete agent-policy fields.

    Returns:
        A validated immutable agent policy.
    """
    return AgentPolicy.model_validate(fields)


def build_tool_approval_attestation(
    fields: Mapping[str, object],
) -> ToolApprovalAttestation:
    """Build one authenticated single-use tool approval.

    Args:
        fields: Complete attestation fields.

    Returns:
        A validated immutable attestation.
    """
    logger.debug("Building tool approval attestation")
    return ToolApprovalAttestation.model_validate(fields)


def derive_object_hash(value: object) -> str:
    """Derive the canonical digest of the exact object being approved.

    Args:
        value: JSON-safe object material.

    Returns:
        The canonical object digest.
    """
    return canonical_digest(value)
