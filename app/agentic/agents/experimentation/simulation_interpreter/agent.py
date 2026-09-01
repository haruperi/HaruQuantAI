"""Provider-neutral Simulation Interpreter agent.

Resolves the enabled role manifest, loads and verifies the package-local
`prompt.md`, binds only the declared output schema, and delegates execution to
the injected `AdkRuntime`. It imports no ADK object, no provider SDK, and no
credential, and it embeds no prompt text.

The interpreter reads completed deterministic evidence. It never recomputes an
upstream value: the only owner-domain operation it calls is the receiving
domain's own contract-version validator, and its output schema has no numeric
field to put a recomputed metric in.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.experimentation.simulation_interpreter.schemas import (
    RunInterpretation,
    build_run_interpretation,
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

    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.governance.models import RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "simulation_interpreter"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_NODE_ID = "interpret_evidence"

# Keys a completed evidence artefact must carry before it can be interpreted.
_REQUIRED_EVIDENCE_KEYS: tuple[str, ...] = (
    "evidence_ref",
    "schema_id",
    "contract_version",
)


def _refuse(
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    outcome: ModelOutcome | None = None,
) -> AgentResult[RunInterpretation]:
    """Build one typed refusal carrying provenance and usage.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        profile: Pinned evaluated model profile.
        reasons: Ordered enumerated refusal codes.
        detail: Bounded advisory detail.
        at_time: Refusal time.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Simulation interpreter refusing task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"interp:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome),
        },
    )


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
    """Build the reproducible lineage for one interpretation.

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
) -> object:
    """Build the bounded consumption record for one interpretation.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.

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
            "tool_calls": 0,
            "cost": Decimal(0) if outcome is None else outcome.cost,
            "compute_seconds": Decimal(0),
            "storage_bytes": 0,
            "search_trials": 0,
        },
    )


def _validate_evidence(evidence: Mapping[str, str]) -> str | None:
    """Validate that the artefact is present, complete, and versioned.

    Args:
        evidence: Candidate completed evidence artefact.

    Returns:
        The enumerated refusal reason, or None when the artefact is eligible.
    """
    if not evidence:
        return "EVIDENCE_ABSENT"
    missing = [key for key in _REQUIRED_EVIDENCE_KEYS if not evidence.get(key)]
    if missing:
        logger.warning("Evidence artefact missing keys: %s", ", ".join(missing))
        return "EVIDENCE_INCOMPLETE"
    return None


def interpret_analytics_evidence(
    registry: RoleRegistry,
    task: AgentTask,
    evidence: Mapping[str, str],
    runtime: AdkRuntime,
    profile: ModelProfile,
    accepted_contract_versions: tuple[str, ...] = ("v1",),
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[RunInterpretation]:
    """Interpret one completed deterministic evidence artefact.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        evidence: Completed versioned evidence from the owning domain.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        accepted_contract_versions: Versions this interpreter can read.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a cited interpretation, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    # A mutated or missing prompt fails closed before any model call.
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Simulation interpreter starting for task %s", task.task_id)

    evidence_refusal = _validate_evidence(evidence)
    if evidence_refusal is not None:
        return _refuse(
            task,
            manifest,
            profile,
            (evidence_refusal,),
            "The artefact was absent or missing required contract fields.",
            now,
        )

    if evidence["contract_version"] not in accepted_contract_versions:
        return _refuse(
            task,
            manifest,
            profile,
            ("EVIDENCE_CONTRACT_INCOMPATIBLE",),
            "The artefact declares a contract version this role cannot read.",
            now,
        )

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"interp:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "objective": task.objective,
                "evidence_schema_id": evidence["schema_id"],
                "evidence_contract_version": evidence["contract_version"],
            },
            "untrusted_evidence": dict(evidence),
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The interpreter declined to interpret the supplied artefact.",
            now,
            outcome,
        )

    interpretation = build_run_interpretation(
        {
            "interpretation_id": derive_stable_id("id", f"run-interp:{task.task_id}"),
            "task_id": task.task_id,
            "evidence_ref": evidence["evidence_ref"],
            "evidence_schema_id": evidence["schema_id"],
            "evidence_contract_version": evidence["contract_version"],
            "measured_facts": _section(outcome.output, "fact:"),
            "deterministic_derivations": _section(outcome.output, "derivation:"),
            "model_inferences": _section(outcome.output, "inference:"),
            "recommendations": _lines(outcome.output.get("recommendations")),
            "limitations": _lines(outcome.output.get("limitations")),
            "open_questions": _lines(outcome.output.get("open_questions")),
            "uncertainty": outcome.output.get(
                "uncertainty",
                "The interpreter reported no explicit uncertainty basis.",
            ),
            "falsifiers": _lines(outcome.output.get("falsifiers")),
        },
    )
    logger.info(
        "Simulation interpreter produced %d cited facts for task %s",
        len(interpretation.measured_facts),
        task.task_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"interp:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": interpretation,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome),
        },
    )


def _section(output: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Extract one citation-keyed section from structured model output.

    Args:
        output: Structured model output.
        prefix: Section key prefix identifying the statement kind.

    Returns:
        Source reference to statement for that section.
    """
    return {
        key.removeprefix(prefix): value
        for key, value in output.items()
        if key.startswith(prefix)
    }


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
