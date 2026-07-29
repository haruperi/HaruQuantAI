"""Public Agentic domain port.

`app/agentic` is the approved top-level governed multi-agent orchestration
domain. Agentic proposes; only the owning deterministic domain decides. The
package holds no broker credential, broker mutation capability, risk approval,
kill-switch authority, or direct execution route.

The package-root public API consists exclusively of standalone functions.
Contract classes, registries, and constants remain internal to their owning
feature module; construct a contract through its `build_*` function, which also
derives the canonical content digest so a contract can never carry a hash that
disagrees with its content.

This boundary currently exposes `FEAT-AGT-01` through `FEAT-AGT-07`. Each further
registered capability is added here as it is implemented, in Feature Registry
order.
"""

from app.agentic.context_memory.context import assemble_context, get_exclusion_reasons
from app.agentic.context_memory.migrations import (
    build_agentic_memory_migration_request,
    get_agentic_memory_migration_statements,
)
from app.agentic.context_memory.models import (
    build_evidence_claim,
    build_memory_record,
    classify_injection,
    derive_content_hash,
)
from app.agentic.context_memory.repository import (
    build_in_memory_memory_store,
    retrieve_memory,
    store_memory,
)
from app.agentic.contracts.models import (
    build_agent_artifact,
    build_agent_message,
    build_agent_provenance,
    build_agent_result,
    build_agent_task,
    build_budget_usage,
    build_workflow_checkpoint,
)
from app.agentic.deliberation.models import (
    derive_record_hash,
    reject_authorization_language,
)
from app.agentic.deliberation.service import run_deliberation
from app.agentic.governance.models import build_firm_mandate, build_role_manifest
from app.agentic.governance.registry import (
    get_registry_mandate,
    get_role_registry,
    list_enabled_roles,
    list_registered_roles,
    resolve_role_manifest,
    validate_firm_mandate,
)
from app.agentic.orchestration.migrations import (
    build_agentic_migration_request,
    get_agentic_migration_statements,
)
from app.agentic.orchestration.models import (
    build_workflow_definition,
    is_terminal_state,
    validate_transition,
)
from app.agentic.orchestration.repository import build_in_memory_workflow_store
from app.agentic.orchestration.service import (
    cancel_task,
    expire_task,
    resume_task,
    submit_task,
)
from app.agentic.permissions.authorization import (
    authorize_tool_call,
    build_in_memory_nonce_store,
)
from app.agentic.permissions.models import (
    build_agent_policy,
    build_tool_approval_attestation,
    build_tool_policy,
    derive_object_hash,
)
from app.agentic.permissions.registry import (
    get_forbidden_permission_classes,
    validate_policy_registry,
)
from app.agentic.runtime.adk import (
    build_deterministic_adk_runtime,
    build_deterministic_model_gateway,
)
from app.agentic.runtime.gateway import invoke_model
from app.agentic.runtime.models import (
    build_model_invocation,
    build_model_profile,
    derive_profile_digest,
)
from app.agentic.runtime.upgrades import (
    get_required_upgrade_gates,
    validate_model_upgrade,
)

__all__: tuple[str, ...] = (
    "assemble_context",
    "authorize_tool_call",
    "build_agent_artifact",
    "build_agent_message",
    "build_agent_policy",
    "build_agent_provenance",
    "build_agent_result",
    "build_agent_task",
    "build_agentic_memory_migration_request",
    "build_agentic_migration_request",
    "build_budget_usage",
    "build_deterministic_adk_runtime",
    "build_deterministic_model_gateway",
    "build_evidence_claim",
    "build_firm_mandate",
    "build_in_memory_memory_store",
    "build_in_memory_nonce_store",
    "build_in_memory_workflow_store",
    "build_memory_record",
    "build_model_invocation",
    "build_model_profile",
    "build_role_manifest",
    "build_tool_approval_attestation",
    "build_tool_policy",
    "build_workflow_checkpoint",
    "build_workflow_definition",
    "cancel_task",
    "classify_injection",
    "derive_content_hash",
    "derive_object_hash",
    "derive_profile_digest",
    "derive_record_hash",
    "expire_task",
    "get_agentic_memory_migration_statements",
    "get_agentic_migration_statements",
    "get_exclusion_reasons",
    "get_forbidden_permission_classes",
    "get_registry_mandate",
    "get_required_upgrade_gates",
    "get_role_registry",
    "invoke_model",
    "is_terminal_state",
    "list_enabled_roles",
    "list_registered_roles",
    "reject_authorization_language",
    "resolve_role_manifest",
    "resume_task",
    "retrieve_memory",
    "run_deliberation",
    "store_memory",
    "submit_task",
    "validate_firm_mandate",
    "validate_model_upgrade",
    "validate_policy_registry",
    "validate_transition",
)
