"""Provider-neutral Coder agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`,
opens an attested sandbox lease, and delegates authoring to the injected
`AdkRuntime`.

Three properties are enforced here rather than trusted to the model. Nothing is
generated without an authenticated human specification and a lease attesting to
every isolation property (`FR-AGENTIC-046`). The artefact manifest — files,
digests, dependencies, tests, provenance, and complete search history — is
required by the schema and digested as a whole (`FR-AGENTIC-047`). And every
declared path is validated and resolved inside the staging root before a byte
is written, with nothing imported, executed, or registered (`FR-AGENTIC-048`).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.agentic.agents.engineering.coder.artifact_store import stage_files
from app.agentic.agents.engineering.coder.sandbox import lease_refusal
from app.agentic.agents.engineering.coder.schemas import (
    CodeArtifact,
    build_code_artifact,
    build_generated_file,
)
from app.agentic.agents.engineering.coder.tools import (
    INDICATOR_REGISTRY_TOOL,
    call_registry_tool,
)
from app.agentic.contracts.models import (
    build_agent_provenance,
    build_agent_result,
    build_budget_usage,
)
from app.agentic.governance.registry import (
    resolve_role_manifest,
    verify_prompt_artifact,
)
from app.agentic.runtime.models import build_model_invocation
from app.composition.logging import get_logger
from app.kernel.identity import derive_stable_id
from app.kernel.time import utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from app.agentic.agents.engineering.coder.schemas import (
        ArtifactKind,
        CodeSpecification,
        GeneratedFile,
        SandboxLease,
        SandboxResult,
    )
    from app.agentic.agents.engineering.coder.tools import IndicatorRegistryPort
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.governance.models import FirmMandate, RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)


@runtime_checkable
class AuthenticatedPrincipal(Protocol):
    """The authenticated identity a code specification must carry.

    Utils exposes `create_auth_context` but not the `AuthContext` class, so
    this structural Protocol names only the fields authorisation reads. A real
    `utils.auth_context.v1` satisfies it without a deep import.

    Attributes:
        principal_id: Authenticated identity.
        principal_type: Whether the principal is a user or a service account.
        permissions: Fine-grained permissions the principal holds.
        tenant_or_environment: Environment the context was issued for.
    """

    principal_id: str
    principal_type: str
    permissions: tuple[str, ...]
    tenant_or_environment: str


ROLE_ID = "coder"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_NODE_ID = "author_code_artifact"

# The permission an authenticated human must hold for their specification to
# authorise code generation at all.
AUTHORING_PERMISSION = "agentic:author_code"


def _envelope(task: AgentTask, at_time: datetime) -> dict[str, object]:
    """Return the shared identity, time, and lineage envelope.

    Args:
        task: Owning governed task.
        at_time: Result time.

    Returns:
        The shared contract envelope fields.
    """
    return {
        "created_at": at_time,
        "request_id": task.request_id,
        "workflow_id": task.workflow_id,
        "correlation_id": task.correlation_id,
        "causation_id": task.causation_id,
    }


def _provenance(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    at_time: datetime,
) -> object:
    """Build the reproducible lineage for one authoring attempt.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        at_time: Result time.

    Returns:
        A validated immutable provenance record.
    """
    return build_agent_provenance(
        {
            **_envelope(task, at_time),
            "provenance_id": derive_stable_id("id", f"prov:{task.task_id}:{ROLE_ID}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "role_version": manifest.version,
            "model_profile_id": profile.profile_id,
            "model_provider": profile.provider,
            "model_identifier": profile.model_identifier,
            "base_prompt_hash": manifest.base_prompt_hash,
            "manifest_hash": manifest.manifest_hash,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "tool_refs": manifest.tools,
            "evidence_refs": task.input_refs,
            "mandate_id": "mandate-resolved-at-composition",
            "mandate_version": manifest.version,
            "policy_version": manifest.version,
            "limits_profile_id": manifest.evaluation_set_id,
            "seed": None,
        },
    )


def _usage(
    task: AgentTask,
    at_time: datetime,
    outcome: ModelOutcome | None,
    tool_calls: int,
    storage_bytes: int = 0,
) -> object:
    """Build the bounded consumption record for one authoring attempt.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.
        tool_calls: Governed tool calls attempted.
        storage_bytes: Bytes written to staging.

    Returns:
        A validated immutable usage record.
    """
    return build_budget_usage(
        {
            **_envelope(task, at_time),
            "usage_id": derive_stable_id("id", f"usage:{task.task_id}:{ROLE_ID}"),
            "task_id": task.task_id,
            "tokens": 0 if outcome is None else outcome.tokens_used,
            "model_calls": 0 if outcome is None else 1,
            "tool_calls": tool_calls,
            "cost": Decimal(0) if outcome is None else outcome.cost,
            "compute_seconds": Decimal(0),
            "storage_bytes": storage_bytes,
            "search_trials": 0 if outcome is None else 1,
        },
    )


def _refuse(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    tool_calls: int = 0,
    outcome: ModelOutcome | None = None,
) -> AgentResult[CodeArtifact]:
    """Build one typed refusal carrying provenance and usage.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        reasons: Ordered enumerated refusal codes.
        detail: Bounded advisory detail.
        at_time: Refusal time.
        tool_calls: Governed tool calls attempted.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Coder refusing task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"coder:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


def _authentication_failure(
    specification: CodeSpecification,
    auth: AuthenticatedPrincipal,
    policy: AgentPolicy,
) -> str | None:
    """Report why a specification is not authenticated for authoring.

    A model-authored specification cannot self-authenticate: the principal,
    the permission, and the environment all come from the auth context a human
    obtained.

    Args:
        specification: Candidate specification.
        auth: Authenticated principal and trace context.
        policy: Requesting agent policy.

    Returns:
        The failing condition, or None when the specification is authorised.
    """
    if auth.principal_type != "USER":
        return "code generation requires a human principal, not a service account"
    if auth.principal_id != specification.principal_id:
        return "the specification names a different principal than the auth context"
    if AUTHORING_PERMISSION not in auth.permissions:
        return f"the principal does not hold {AUTHORING_PERMISSION}"
    if auth.tenant_or_environment != specification.environment:
        return "the auth context environment differs from the specification's"
    if specification.environment != policy.environment:
        return "the specification environment differs from the agent policy's"
    return None


def _resolve_registry(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: IndicatorRegistryPort,
    principal_id: str,
    task_id: str,
    scope: Mapping[str, str],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> tuple[frozenset[str], str | None]:
    """Read the registered indicator identifiers through a governed tool.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected registry port.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        scope: Scope declared for the call.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.

    Returns:
        The registered identifiers, and a denial detail when the call failed.
    """
    tool = tool_policies.get(INDICATOR_REGISTRY_TOOL)
    if tool is None:
        return (frozenset(), "The indicator registry tool is not registered.")
    outcome = call_registry_tool(
        mandate,
        policy,
        tool,
        principal_id,
        task_id,
        scope,
        port.list_registered_indicators,
        at_time,
        nonce_store=nonce_store,
        audit_store=audit_store,
    )
    if not outcome.allowed or outcome.payload is None:
        return (
            frozenset(),
            f"A governed tool was denied: {outcome.denial_reason}.",
        )
    return (frozenset(outcome.payload), None)


def _indicator_gap(
    specification: CodeSpecification,
    registered: frozenset[str],
) -> tuple[str, ...]:
    """Return the required indicators the registry does not know.

    Args:
        specification: Authenticated specification.
        registered: Registered indicator identifiers.

    Returns:
        Ordered unregistered identifiers.
    """
    return tuple(
        sorted(set(specification.required_indicators) - registered),
    )


def _files_from_output(output: Mapping[str, str]) -> tuple[GeneratedFile, ...]:
    """Extract the declared files from structured model output.

    Args:
        output: Structured model output.

    Returns:
        Ordered generated files with derived digests.
    """
    return tuple(
        build_generated_file(key.removeprefix("file:"), value)
        for key, value in sorted(output.items())
        if key.startswith("file:")
    )


def _lines(value: str | None) -> tuple[str, ...]:
    """Split one newline-delimited output field into bounded statements.

    Args:
        value: Candidate newline-delimited field.

    Returns:
        Ordered non-empty statements.
    """
    if not value:
        return ()
    return tuple(line.strip() for line in value.split("\n") if line.strip())


def _promotion_status(
    unregistered: tuple[str, ...],
    sandbox_result: SandboxResult,
) -> str:
    """Determine whether a staged artefact may be considered for promotion.

    Args:
        unregistered: Required identifiers the registry does not know.
        sandbox_result: Evidence from exercising the artefact.

    Returns:
        The enumerated promotion status.
    """
    if unregistered:
        return "blocked_on_indicator_merge"
    if not sandbox_result.all_passed:
        return "blocked_on_tests"
    return "ready"


def author_code_artifact(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    registry_port: IndicatorRegistryPort,
    sandbox: object,
    runtime: AdkRuntime,
    profile: ModelProfile,
    specification: CodeSpecification,
    auth: AuthenticatedPrincipal,
    staging_root: Path,
    kind: ArtifactKind = "strategy_evaluator",
    principal_id: str = "agent-coder",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[CodeArtifact]:
    """Author one staged code artefact under an authenticated specification.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        registry_port: Injected Indicators registry port.
        sandbox: Injected sandbox port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        specification: Authenticated human specification.
        auth: Authenticated principal and trace context.
        staging_root: Root every artefact is written beneath.
        kind: Artefact kind to author; must be authorised by the specification.
        principal_id: Authenticated requesting principal for tool calls.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a staged artefact, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Coder starting %s for task %s", kind, task.task_id)

    gate = _pre_generation_gate(
        specification,
        auth,
        policy,
        kind,
        sandbox,
        task.task_id,
    )
    if gate.refusal is not None:
        reason, detail = gate.refusal
        return _refuse(task, manifest, profile, (reason,), detail, now)

    registered, denial = _resolve_registry(
        mandate,
        policy,
        tool_policies,
        registry_port,
        principal_id,
        task.task_id,
        scope,
        now,
        nonce_store,
        audit_store,
    )
    if denial is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("REGISTRY_TOOL_DENIED",),
            denial,
            now,
            1,
        )

    unregistered = _indicator_gap(specification, registered)
    if unregistered and "indicator_candidate" not in specification.artifact_kinds:
        return _refuse(
            task,
            manifest,
            profile,
            ("INDICATOR_NOT_REGISTERED",),
            (
                "The specification requires unregistered indicators and does not "
                "authorise authoring them: "
                f"{', '.join(unregistered)}."
            ),
            now,
            1,
        )

    return _generate(
        task,
        manifest,
        runtime,
        profile,
        specification,
        gate.lease,
        sandbox,
        kind,
        registered,
        unregistered,
        staging_root,
        now,
    )


class _Gate:
    """Outcome of the checks that precede any model call.

    Attributes:
        refusal: Enumerated reason and detail when generation is refused.
        lease: Attested sandbox lease when generation may proceed.
    """

    __slots__ = ("lease", "refusal")

    def __init__(
        self,
        refusal: tuple[str, str] | None,
        lease: SandboxLease | None,
    ) -> None:
        """Store the gate outcome.

        Args:
            refusal: Enumerated reason and detail, or None.
            lease: Attested lease, or None.
        """
        self.refusal = refusal
        self.lease = lease


def _pre_generation_gate(
    specification: CodeSpecification,
    auth: AuthenticatedPrincipal,
    policy: AgentPolicy,
    kind: ArtifactKind,
    sandbox: object,
    task_id: str,
) -> _Gate:
    """Run every check that must pass before a model is called.

    Args:
        specification: Candidate specification.
        auth: Authenticated principal and trace context.
        policy: Requesting agent policy.
        kind: Artefact kind to author.
        sandbox: Injected sandbox port.
        task_id: Owning task identity.

    Returns:
        The gate outcome, carrying either a refusal or an attested lease.
    """
    auth_failure = _authentication_failure(specification, auth, policy)
    if auth_failure is not None:
        return _Gate(("SPECIFICATION_NOT_AUTHENTICATED", auth_failure), None)
    if kind not in specification.artifact_kinds:
        return _Gate(
            (
                "ARTIFACT_KIND_NOT_AUTHORISED",
                f"The specification does not authorise authoring a {kind}.",
            ),
            None,
        )
    lease: SandboxLease = sandbox.open_lease(task_id)  # type: ignore[attr-defined]
    unattested = lease_refusal(lease)
    if unattested is not None:
        return _Gate(("SANDBOX_NOT_ATTESTED", unattested), None)
    return _Gate(None, lease)


def _generate(
    task: AgentTask,
    manifest: RoleManifest,
    runtime: AdkRuntime,
    profile: ModelProfile,
    specification: CodeSpecification,
    lease: SandboxLease | None,
    sandbox: object,
    kind: ArtifactKind,
    registered: frozenset[str],
    unregistered: tuple[str, ...],
    staging_root: Path,
    at_time: datetime,
) -> AgentResult[CodeArtifact]:
    """Author, exercise, and stage one artefact.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        specification: Authenticated specification.
        lease: Attested sandbox lease.
        sandbox: Injected sandbox port.
        kind: Artefact kind to author.
        registered: Registered indicator identifiers.
        unregistered: Required identifiers the registry does not know.
        staging_root: Root every artefact is written beneath.
        at_time: Result time.

    Returns:
        A typed result carrying a staged artefact, or a refusal.
    """
    assert lease is not None  # noqa: S101 - the gate guarantees it.
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"coder:{task.task_id}:{kind}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # The authorised specification and the registry answer are trusted;
            # both came from a human or a deterministic receiver.
            "trusted_context": {
                "artifact_kind": kind,
                "target_contract": specification.target_contract,
                "objective": specification.objective,
                "environment": specification.environment,
                "registered_indicators": ",".join(sorted(registered)),
                "unregistered_indicators": ",".join(unregistered),
                **{
                    f"acceptance:{index}": item
                    for index, item in enumerate(specification.acceptance_criteria)
                },
            },
            "untrusted_evidence": {
                f"thesis:{index}": ref
                for index, ref in enumerate(specification.thesis_refs)
            },
            "max_output_tokens": profile.max_output_tokens,
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_NODE_ID, profile, invocation)
    sandbox.close_lease(lease)  # type: ignore[attr-defined]
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The coder declined to author the requested artefact.",
            at_time,
            1,
            outcome,
        )

    files = _files_from_output(outcome.output)
    if not files:
        return _refuse(
            task,
            manifest,
            profile,
            ("NO_FILES_GENERATED",),
            "The coder returned no files.",
            at_time,
            1,
            outcome,
        )

    sandbox_result = sandbox.run_files(lease, files)  # type: ignore[attr-defined]
    artifact_id = derive_stable_id("id", f"artifact:{task.task_id}:{kind}")
    try:
        staged = stage_files(staging_root, artifact_id, files)
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("STAGING_PATH_REJECTED",),
            str(error),
            at_time,
            1,
            outcome,
        )

    artifact = build_code_artifact(
        {
            "artifact_id": artifact_id,
            "task_id": task.task_id,
            "specification_id": specification.specification_id,
            "kind": kind,
            "files": files,
            "dependencies": _dependencies(outcome.output),
            "tests": tuple(
                item.relative_path
                for item in files
                if item.relative_path.startswith("tests/")
            )
            or ("no-tests-declared",),
            "required_indicators": specification.required_indicators,
            "unregistered_indicators": unregistered,
            "model_profile_id": profile.profile_id,
            "base_prompt_hash": manifest.base_prompt_hash,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "tool_refs": (INDICATOR_REGISTRY_TOOL,),
            "search_history": _lines(outcome.output.get("search_history"))
            or (f"attempt 1: authored {len(files)} files",),
            "sandbox_result": sandbox_result,
            "staging_path": artifact_id,
            "promotion_status": _promotion_status(unregistered, sandbox_result),
        },
    )
    logger.info(
        "Coder staged artefact %s with %d files, status %s",
        artifact.artifact_hash,
        len(staged),
        artifact.promotion_status,
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"coder:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": artifact,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(
                task,
                at_time,
                outcome,
                1,
                sum(item.byte_count for item in files),
            ),
        },
    )


def _dependencies(output: Mapping[str, str]) -> dict[str, str]:
    """Extract the declared dependency and SBOM entries from model output.

    Args:
        output: Structured model output.

    Returns:
        Dependency name to declared version.
    """
    return {
        key.removeprefix("dependency:"): value
        for key, value in sorted(output.items())
        if key.startswith("dependency:")
    }
