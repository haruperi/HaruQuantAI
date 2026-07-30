"""Provider-neutral Fundamental Analyst agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates narrative to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model.
Applicability is the receiver's answer, read before any model call, so an
analyst cannot produce an issuer claim for an instrument with no issuer
(`FR-AGENTIC-026`). Every reference, coverage count, source kind, availability
instant, and canonical digest is copied from what Research projected, so the
model describes evidence rather than producing it (`FR-AGENTIC-025`). And
claims, assumptions, horizons, and falsifiers are parallel key sets, so a claim
nobody can say how to falsify cannot be expressed (`FR-AGENTIC-027`).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.market_intelligence.fundamental_analyst.schemas import (
    FundamentalEvidencePack,
    build_fundamental_evidence_pack,
)
from app.agentic.agents.market_intelligence.fundamental_analyst.tools import (
    APPLICABILITY_TOOL,
    FUNDAMENTAL_EVIDENCE_TOOL,
    call_intelligence_tool,
    verify_projection,
)
from app.agentic.context_memory.models import classify_injection
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
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from app.agentic.agents.market_intelligence.fundamental_analyst.tools import (
        FundamentalEvidencePort,
    )
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.governance.models import FirmMandate, RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.permissions.authorization import ApprovalNonceStore
    from app.agentic.permissions.models import AgentPolicy, ToolPolicy
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "fundamental_analyst"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_ANALYZE_NODE_ID = "analyze_fundamentals"

_CLAIM_PREFIX = "claim:"
_ASSUMPTION_PREFIX = "assumption:"
_HORIZON_PREFIX = "horizon:"
_FALSIFIER_PREFIX = "falsifier:"


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
    """Build the reproducible lineage for one fundamental reading.

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
) -> object:
    """Build the bounded consumption record for one fundamental reading.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.
        tool_calls: Governed tool calls attempted.

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
            "storage_bytes": 0,
            "search_trials": 0,
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
) -> AgentResult[FundamentalEvidencePack]:
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
        "Fundamental analyst refusing for task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"fundamental:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


def _section(output: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Extract one prefixed section from a model output.

    Args:
        output: Model output mapping.
        prefix: Section prefix to select.

    Returns:
        The section entries keyed without their prefix.
    """
    return {
        key.removeprefix(prefix): value
        for key, value in sorted(output.items())
        if key.startswith(prefix)
    }


def _tuple(value: str | None) -> tuple[str, ...]:
    """Split one comma-delimited projected field.

    Args:
        value: Candidate field value.

    Returns:
        Ordered unique non-empty trimmed entries.
    """
    if not value:
        return ()
    seen: dict[str, None] = {}
    for item in value.split(","):
        trimmed = item.strip()
        if trimmed:
            seen.setdefault(trimmed, None)
    return tuple(seen)


def _coverage(value: str | None) -> dict[str, str]:
    """Parse the projected coverage counts.

    Args:
        value: Candidate `kind=count` pairs.

    Returns:
        Coverage kind to count as text.
    """
    parsed: dict[str, str] = {}
    for item in _tuple(value):
        kind, _, count = item.partition("=")
        if kind.strip() and count.strip():
            parsed[kind.strip()] = count.strip()
    return parsed


def suspected_references(projection: Mapping[str, str]) -> tuple[str, ...]:
    """Return projected references whose text reads as an instruction.

    `FEAT-AGT-06` owns injection classification and is reused rather than
    restated. Anything flagged is excluded before the model is invoked, so
    retrieved text can never occupy an instruction slot.

    Args:
        projection: Receiver-returned projection fields.

    Returns:
        Ordered references the classifier flagged.
    """
    flagged: list[str] = []
    for reference in _tuple(projection.get("document_references")):
        if classify_injection(reference) == "suspected":
            flagged.append(reference)
    return tuple(flagged)


def analyze_fundamentals(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: FundamentalEvidencePort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    instrument: str,
    asset_class: str,
    model: str,
    decision_time: str,
    principal_id: str = "agent-fundamental-analyst",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[FundamentalEvidencePack]:
    """Read point-in-time fundamental evidence for one instrument.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected fundamental-evidence port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        instrument: Instrument under analysis.
        asset_class: Normalized instrument asset class.
        model: Requested fundamental model.
        decision_time: Point in time the evidence must be available by.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a bounded evidence pack, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info(
        "Fundamental analyst reading %s evidence for %s",
        model,
        instrument,
    )

    missing = tuple(
        name
        for name in (APPLICABILITY_TOOL, FUNDAMENTAL_EVIDENCE_TOOL)
        if name not in tool_policies
    )
    if missing:
        return _refuse(
            task,
            manifest,
            profile,
            ("INTELLIGENCE_TOOL_DENIED",),
            f"Required evidence tools are not registered: {', '.join(missing)}.",
            now,
        )

    applicability = call_intelligence_tool(
        mandate,
        policy,
        tool_policies[APPLICABILITY_TOOL],
        principal_id,
        task.task_id,
        scope,
        lambda: port.assess_applicability(asset_class, model),
        now,
        nonce_store=nonce_store,
        audit_store=audit_store,
        calls_used=0,
    )
    if not applicability.allowed or not applicability.payload:
        return _refuse(
            task,
            manifest,
            profile,
            ("INTELLIGENCE_TOOL_DENIED",),
            f"Applicability was not returned: {applicability.denial_reason}.",
            now,
            1,
        )
    # The receiver decides whether the model applies. An analyst that
    # substituted its own judgement here could produce an issuer claim for an
    # instrument that has no issuer.
    if str(applicability.payload.get("status")) != "applicable":
        return _refuse(
            task,
            manifest,
            profile,
            ("FUNDAMENTAL_MODEL_NOT_APPLICABLE",),
            (
                f"Research reports the {model!r} model does not apply to "
                f"{asset_class!r}: {applicability.payload.get('reasons')}."
            ),
            now,
            1,
        )

    evidence = call_intelligence_tool(
        mandate,
        policy,
        tool_policies[FUNDAMENTAL_EVIDENCE_TOOL],
        principal_id,
        task.task_id,
        scope,
        lambda: port.get_fundamental_projection(
            instrument,
            asset_class,
            model,
            decision_time,
        ),
        now,
        nonce_store=nonce_store,
        audit_store=audit_store,
        calls_used=1,
    )
    if not evidence.allowed or not evidence.payload:
        return _refuse(
            task,
            manifest,
            profile,
            ("FUNDAMENTAL_COVERAGE_INSUFFICIENT",),
            f"Evidence was not returned: {evidence.denial_reason}.",
            now,
            2,
        )

    projection = {key: str(value) for key, value in evidence.payload.items()}
    failure = verify_projection(projection)
    if failure is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("FUNDAMENTAL_COVERAGE_INSUFFICIENT",),
            failure,
            now,
            2,
        )

    return _read(
        task,
        manifest,
        runtime,
        profile,
        projection,
        instrument,
        asset_class,
        model,
        decision_time,
        now,
    )


def _read(
    task: AgentTask,
    manifest: RoleManifest,
    runtime: AdkRuntime,
    profile: ModelProfile,
    projection: Mapping[str, str],
    instrument: str,
    asset_class: str,
    model: str,
    decision_time: str,
    at_time: datetime,
) -> AgentResult[FundamentalEvidencePack]:
    """Have the model read the projected evidence and build the pack.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        projection: Receiver-returned projection fields.
        instrument: Instrument under analysis.
        asset_class: Normalized instrument asset class.
        model: Fundamental model Research applied.
        decision_time: Point in time the evidence was available by.
        at_time: Result time.

    Returns:
        A typed result carrying a bounded evidence pack, or a refusal.
    """
    # Flagged references never reach the model. `FEAT-AGT-06` decides what
    # reads as an instruction; this package does not restate that judgement.
    flagged = suspected_references(projection)
    references = tuple(
        reference
        for reference in _tuple(projection.get("document_references"))
        if reference not in flagged
    )
    if not references:
        return _refuse(
            task,
            manifest,
            profile,
            ("FUNDAMENTAL_COVERAGE_INSUFFICIENT",),
            "Every projected reference was excluded as suspected instruction.",
            at_time,
            2,
        )

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"fundamental:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "instrument": instrument,
                "asset_class": asset_class,
                "model": model,
                "decision_time": decision_time,
                "canonical_hash": projection["canonical_hash"],
                "excluded_references": str(len(flagged)),
            },
            "untrusted_evidence": {
                f"reference:{index}": reference
                for index, reference in enumerate(references)
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_ANALYZE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The analyst declined to read the supplied evidence.",
            at_time,
            2,
            outcome,
        )

    uncertainty = outcome.output.get("uncertainty", "")
    if flagged:
        uncertainty = (
            f"{uncertainty} {len(flagged)} reference(s) were excluded before "
            "reading because they read as instructions rather than evidence."
        ).strip()

    try:
        pack = build_fundamental_evidence_pack(
            {
                "pack_id": derive_stable_id("id", f"fundamental:{task.task_id}"),
                "task_id": task.task_id,
                "instrument": instrument,
                "asset_class": asset_class,
                "model": model,
                "claims": _section(outcome.output, _CLAIM_PREFIX),
                "assumptions": _section(outcome.output, _ASSUMPTION_PREFIX),
                "horizons": _section(outcome.output, _HORIZON_PREFIX),
                "falsifiers": _section(outcome.output, _FALSIFIER_PREFIX),
                # Everything below is the receiver's, copied rather than
                # described, so the model cannot misreport what it read.
                "evidence_refs": references,
                "source_kinds": _tuple(projection.get("source_kinds"))
                or ("unreported",),
                "coverage": _coverage(projection.get("coverage")),
                "observed_from": projection.get("observed_from", decision_time),
                "available_by": projection.get("available_by", decision_time),
                "canonical_hash": projection["canonical_hash"],
                "uncertainty": uncertainty,
                "issued_at": at_time.isoformat(),
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("FUNDAMENTAL_CLAIM_NOT_FALSIFIABLE",),
            str(error),
            at_time,
            2,
            outcome,
        )

    logger.info(
        "Fundamental analyst recorded %d claims for %s",
        len(pack.claims),
        instrument,
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"fundamental:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": pack,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, 2),
        },
    )
