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

This boundary exposes every implemented registered capability. `FEAT-AGT-22`
adds the authenticated operator surface — submit, inspect, cancel,
approve-handoff, replay, quarantine, audit, and disablement — and the role
operations of the implemented leaf agent packages.

Two things are deliberately absent. `FEAT-AGT-09` and `FEAT-AGT-10` are not
implemented, so no fundamental or sentiment operation appears here. And
`open_sandbox` and `stage_code_artifact`, which `WF-AGT-005` names as planned
root exports, are **not** exported: no isolation runtime exists to open, and a
function that returned a lease nothing honours would be worse than the gap.
"""

from app.agentic.agents.engineering.coder.agent import author_code_artifact
from app.agentic.agents.experimentation.experiment_designer.agent import (
    coordinate_simulation,
    design_experiment,
)
from app.agentic.agents.experimentation.optimization_coordinator.agent import (
    coordinate_optimization,
    design_sweep,
)
from app.agentic.agents.experimentation.simulation_interpreter.agent import (
    interpret_analytics_evidence,
)
from app.agentic.agents.market_analysis.quantitative_analyst.agent import (
    analyze_quantitative_evidence,
)
from app.agentic.agents.market_analysis.technical_analyst.agent import (
    analyze_technical_context,
)
from app.agentic.agents.operations.evaluation_manager.agent import (
    critique_candidate,
    evaluate_agent,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.agent import (
    advise_portfolio,
    critique_risk,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst.agent import (
    develop_hypothesis,
    develop_strategy_thesis,
)
from app.agentic.agents.strategy_desk.trader.handoff import submit_trade_proposal
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
from app.agentic.lifecycle.service import (
    assess_promotion,
    get_artifact_history,
    get_artifact_state,
    transition_artifact,
)
from app.agentic.operations.service import (
    get_run_incidents,
    get_run_trace,
    quarantine_agent,
    replay_run,
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
from app.agentic.public_api.dependencies import build_agentic_dependencies
from app.agentic.public_api.service import (
    approve_agentic_handoff,
    cancel_firm_run,
    disable_agentic,
    get_firm_audit,
    get_firm_run,
    get_operator_operations,
    quarantine_firm_agent,
    replay_firm_run,
    submit_firm_request,
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
    "advise_portfolio",
    "analyze_quantitative_evidence",
    "analyze_technical_context",
    "approve_agentic_handoff",
    "assemble_context",
    "assess_promotion",
    "author_code_artifact",
    "authorize_tool_call",
    "build_agent_artifact",
    "build_agent_message",
    "build_agent_policy",
    "build_agent_provenance",
    "build_agent_result",
    "build_agent_task",
    "build_agentic_dependencies",
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
    "cancel_firm_run",
    "cancel_task",
    "classify_injection",
    "coordinate_optimization",
    "coordinate_simulation",
    "critique_candidate",
    "critique_risk",
    "derive_content_hash",
    "derive_object_hash",
    "derive_profile_digest",
    "derive_record_hash",
    "design_experiment",
    "design_sweep",
    "develop_hypothesis",
    "develop_strategy_thesis",
    "disable_agentic",
    "evaluate_agent",
    "expire_task",
    "get_agentic_memory_migration_statements",
    "get_agentic_migration_statements",
    "get_artifact_history",
    "get_artifact_state",
    "get_exclusion_reasons",
    "get_firm_audit",
    "get_firm_run",
    "get_forbidden_permission_classes",
    "get_operator_operations",
    "get_registry_mandate",
    "get_required_upgrade_gates",
    "get_role_registry",
    "get_run_incidents",
    "get_run_trace",
    "interpret_analytics_evidence",
    "invoke_model",
    "is_terminal_state",
    "list_enabled_roles",
    "list_registered_roles",
    "quarantine_agent",
    "quarantine_firm_agent",
    "reject_authorization_language",
    "replay_firm_run",
    "replay_run",
    "resolve_role_manifest",
    "resume_task",
    "retrieve_memory",
    "run_deliberation",
    "store_memory",
    "submit_firm_request",
    "submit_task",
    "submit_trade_proposal",
    "transition_artifact",
    "validate_firm_mandate",
    "validate_model_upgrade",
    "validate_policy_registry",
    "validate_transition",
)
