"""Provider-neutral Strategy Thesis Analyst agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
turns specialist evidence packs into falsifiable hypotheses and non-executable
theses through the injected `AdkRuntime`.

Two properties are enforced here rather than trusted to the model. First, the
evidence references and retained conflicts on a thesis are taken from the
supplied packs and dissent, not from model output — so a synthesis cannot cite
evidence it was never given or quietly drop a conflict. Second, agreement is
never treated as evidence: a thesis whose inputs disagree is `contested` and
must carry those conflicts forward (`FR-AGENTIC-039`).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.strategy_desk.strategy_thesis_analyst.schemas import (
    Hypothesis,
    StrategyThesis,
    build_hypothesis,
    build_strategy_thesis,
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
    from collections.abc import Mapping, Sequence
    from datetime import datetime

    from app.agentic.contracts.models import AgentResult, AgentTask
    from app.agentic.deliberation.models import DissentRecord
    from app.agentic.governance.models import RoleManifest
    from app.agentic.governance.registry import RoleRegistry
    from app.agentic.runtime.adk import AdkRuntime
    from app.agentic.runtime.models import ModelOutcome, ModelProfile

logger = get_logger(__name__)

ROLE_ID = "strategy_thesis_analyst"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_HYPOTHESIS_NODE = "develop_hypothesis"
_THESIS_NODE = "develop_strategy_thesis"


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
    """Build the reproducible lineage for one synthesis.

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
    """Build the bounded consumption record for one synthesis.

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


def _refuse[T](
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    outcome: ModelOutcome | None = None,
) -> AgentResult[T]:
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
        "Strategy thesis analyst refusing task %s: %s",
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"thesis:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome),
        },
    )


def _section(output: Mapping[str, str], prefix: str) -> dict[str, str]:
    """Extract one keyed section from structured model output.

    Args:
        output: Structured model output.
        prefix: Section key prefix.

    Returns:
        Identifier to statement for that section.
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


def develop_hypothesis(
    registry: RoleRegistry,
    task: AgentTask,
    evidence_packs: Mapping[str, Mapping[str, str]],
    runtime: AdkRuntime,
    profile: ModelProfile,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[Hypothesis]:
    """Develop one falsifiable hypothesis from specialist evidence packs.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        evidence_packs: Evidence pack reference to bounded pack content.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a falsifiable hypothesis, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Developing a hypothesis for task %s", task.task_id)

    if not evidence_packs:
        return _refuse(
            task,
            manifest,
            profile,
            ("EVIDENCE_PACKS_ABSENT",),
            "A hypothesis requires at least one specialist evidence pack.",
            now,
        )

    flattened = {
        f"{pack_ref}:{key}": value
        for pack_ref, pack in sorted(evidence_packs.items())
        for key, value in sorted(pack.items())
    }
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"hypothesis:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {"objective": task.objective},
            "untrusted_evidence": flattened,
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_HYPOTHESIS_NODE, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The analyst declined to form a hypothesis from this evidence.",
            now,
            outcome,
        )

    hypothesis = build_hypothesis(
        {
            "hypothesis_id": derive_stable_id("id", f"hyp:{task.task_id}"),
            "task_id": task.task_id,
            "statement": outcome.output["statement"],
            "asset_scope": _lines(outcome.output.get("asset_scope")),
            "horizon": outcome.output["horizon"],
            "mechanism": outcome.output["mechanism"],
            "prerequisites": _lines(outcome.output.get("prerequisites")),
            "confounders": _lines(outcome.output.get("confounders")),
            "rejection_criterion": outcome.output["rejection_criterion"],
            # Evidence references come from what was actually supplied, so a
            # hypothesis cannot cite a pack it never received.
            "evidence_refs": tuple(sorted(evidence_packs)),
            "leakage_constraints": _lines(outcome.output.get("leakage_constraints")),
        },
    )
    logger.info(
        "Hypothesis %s formed for task %s",
        hypothesis.hypothesis_id,
        task.task_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"hyp:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": hypothesis,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome),
        },
    )


def develop_strategy_thesis(
    registry: RoleRegistry,
    task: AgentTask,
    hypotheses: Sequence[Hypothesis],
    evidence_packs: Mapping[str, Mapping[str, str]],
    runtime: AdkRuntime,
    profile: ModelProfile,
    dissent: Sequence[DissentRecord] = (),
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[StrategyThesis]:
    """Synthesize hypotheses into one non-executable strategy thesis.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        hypotheses: Falsifiable hypotheses the thesis rests on.
        evidence_packs: Evidence pack reference to bounded pack content.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        dissent: Preserved dissent from deliberation, carried forward.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a non-executable thesis, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Developing a strategy thesis for task %s", task.task_id)

    if not hypotheses:
        return _refuse(
            task,
            manifest,
            profile,
            ("HYPOTHESES_ABSENT",),
            "A thesis requires at least one falsifiable hypothesis.",
            now,
        )

    # Conflicts are taken from the deliberation record, not from the model, so
    # a synthesis cannot quietly drop a dissent it found inconvenient.
    unresolved = tuple(
        f"{item.dissenting_role_id}: {item.statement}"
        for item in dissent
        if item.unresolved
    )
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"thesis:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "objective": task.objective,
                "hypothesis_count": str(len(hypotheses)),
                "unresolved_conflicts": str(len(unresolved)),
            },
            "untrusted_evidence": {
                f"{pack_ref}:{key}": value
                for pack_ref, pack in sorted(evidence_packs.items())
                for key, value in sorted(pack.items())
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_THESIS_NODE, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The analyst declined to synthesize a thesis.",
            now,
            outcome,
        )

    # Agreement is not evidence: an unresolved conflict forces `contested`
    # regardless of what the model would prefer to claim.
    declared_stance = outcome.output.get("stance", "supported")
    stance = "contested" if unresolved else declared_stance
    if stance != declared_stance:
        logger.warning(
            "Overriding declared stance %s with contested: %d unresolved conflicts",
            declared_stance,
            len(unresolved),
        )

    thesis = build_strategy_thesis(
        {
            "thesis_id": derive_stable_id("id", f"thesis:{task.task_id}"),
            "task_id": task.task_id,
            "title": outcome.output["title"],
            "summary": outcome.output["summary"],
            "stance": stance,
            "hypothesis_ids": tuple(item.hypothesis_id for item in hypotheses),
            "signals": _section(outcome.output, "signal:"),
            "intended_behaviour": _section(outcome.output, "behaviour:"),
            "supporting_evidence": tuple(sorted(evidence_packs)),
            "retained_conflicts": unresolved,
            "assumptions": _lines(outcome.output.get("assumptions")),
            "uncertainty": outcome.output["uncertainty"],
            "next_test": outcome.output["next_test"],
        },
    )
    logger.info(
        "Thesis %s formed for task %s with stance %s",
        thesis.thesis_id,
        task.task_id,
        thesis.stance,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"thesis:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": thesis,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome),
        },
    )
