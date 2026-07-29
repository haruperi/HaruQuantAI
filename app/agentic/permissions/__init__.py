"""Public `FEAT-AGT-05` tool registry, permissions, and approvals API."""

from app.agentic.permissions.authorization import (
    ApprovalNonceStore,
    authorize_tool_call,
    build_in_memory_nonce_store,
)
from app.agentic.permissions.models import (
    AgentPolicy,
    PermissionDecision,
    ToolApprovalAttestation,
    ToolPolicy,
    build_agent_policy,
    build_tool_approval_attestation,
    build_tool_policy,
    derive_object_hash,
)
from app.agentic.permissions.registry import (
    get_forbidden_permission_classes,
    validate_policy_registry,
)

__all__: tuple[str, ...] = (
    "AgentPolicy",
    "ApprovalNonceStore",
    "PermissionDecision",
    "ToolApprovalAttestation",
    "ToolPolicy",
    "authorize_tool_call",
    "build_agent_policy",
    "build_in_memory_nonce_store",
    "build_tool_approval_attestation",
    "build_tool_policy",
    "derive_object_hash",
    "get_forbidden_permission_classes",
    "validate_policy_registry",
)
