"""Provider-neutral Evaluation Manager agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates narrative to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. Evaluation
coverage is exact: six set kinds, six graders, six calibrations, read from the
evidence port (`FR-AGENTIC-049`). A critique addresses all seven challenges,
several of them grounded deterministically in the candidate evidence supplied
(`FR-AGENTIC-050`). And the required action is computed from the gates and the
baseline margin, so the model writes the rationale but cannot change the
outcome (`FR-AGENTIC-051`).

This feature decides; it does not mutate. Governance has no role-state
mutation path, so applying a `disable` or `retire` belongs to `FEAT-AGT-18`
lifecycle or a governance manifest re-issue.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.operations.evaluation_manager.evaluator import (
    failed_safety_gates,
    required_action,
)
from app.agentic.agents.operations.evaluation_manager.schemas import (
    CritiqueMemo,
    EconomicAcceptanceVerdict,
    EvaluationPlan,
    build_baseline_comparison,
    build_critique_memo,
    build_economic_acceptance_verdict,
    build_evaluation_plan,
)
from app.agentic.agents.operations.evaluation_manager.tools import (
    BASELINE_TOOL,
    EVALUATION_SET_TOOL,
    GATE_OUTCOME_TOOL,
    GRADER_CALIBRATION_TOOL,
    call_evaluation_tool,
    verify_comparison,
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
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from datetime import datetime

    from app.agentic.agents.engineering.coder.schemas import CodeArtifact
    from app.agentic.agents.experimentation.experiment_designer.schemas import (
        ExperimentVerdict,
    )
    from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
        SweepVerdict,
    )
    from app.agentic.agents.operations.evaluation_manager.tools import (
        EvaluationEvidencePort,
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

ROLE_ID = "evaluation_manager"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_EVALUATE_NODE_ID = "evaluate_agent"
_CRITIQUE_NODE_ID = "critique_candidate"

_GRADER_PREFIX = "grader:"
_CALIBRATION_PREFIX = "calibration:"


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
    """Build the reproducible lineage for one evaluation or critique.

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
    """Build the bounded consumption record for one evaluation or critique.

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


def _refuse[T](
    task: AgentTask,
    manifest: RoleManifest,
    profile: ModelProfile,
    reasons: tuple[str, ...],
    detail: str | None,
    at_time: datetime,
    kind: str,
    tool_calls: int = 0,
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
        kind: Operation label distinguishing the two public use cases.
        tool_calls: Governed tool calls attempted.
        outcome: Model outcome when the refusal followed an invocation.

    Returns:
        A refused typed result.
    """
    logger.info(
        "Evaluation manager refusing %s for task %s: %s",
        kind,
        task.task_id,
        ", ".join(reasons),
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"{kind}:{task.task_id}:refused"),
            "task_id": task.task_id,
            "status": "refused",
            "payload": None,
            "reasons": reasons,
            "detail": detail,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, tool_calls),
        },
    )


class _Evidence:
    """Evaluation evidence gathered from the port before any judgement.

    Attributes:
        refusal: Enumerated reason and detail when gathering failed.
        sets: Versioned evaluation set reference per kind.
        graders: Grader reference per kind.
        calibrations: Calibration reference per kind.
        gates: Gate kind to enumerated outcome.
        comparison: Measured baseline comparison fields.
        tool_calls: Governed tool calls attempted.
    """

    __slots__ = (
        "calibrations",
        "comparison",
        "gates",
        "graders",
        "refusal",
        "sets",
        "tool_calls",
    )

    def __init__(
        self,
        refusal: tuple[str, str] | None,
        sets: Mapping[str, str],
        graders: Mapping[str, str],
        calibrations: Mapping[str, str],
        gates: Mapping[str, str],
        comparison: Mapping[str, str],
        tool_calls: int,
    ) -> None:
        """Store the gathered evidence.

        Args:
            refusal: Enumerated reason and detail, or None.
            sets: Versioned evaluation set reference per kind.
            graders: Grader reference per kind.
            calibrations: Calibration reference per kind.
            gates: Gate kind to enumerated outcome.
            comparison: Measured baseline comparison fields.
            tool_calls: Governed tool calls attempted.
        """
        self.refusal = refusal
        self.sets = sets
        self.graders = graders
        self.calibrations = calibrations
        self.gates = gates
        self.comparison = comparison
        self.tool_calls = tool_calls


def _split_calibrations(
    payload: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Split a prefixed grader payload into graders and calibrations.

    Args:
        payload: Receiver-returned prefixed references.

    Returns:
        Grader references and calibration references, each keyed by set kind.
    """
    graders = {
        key.removeprefix(_GRADER_PREFIX): value
        for key, value in sorted(payload.items())
        if key.startswith(_GRADER_PREFIX)
    }
    calibrations = {
        key.removeprefix(_CALIBRATION_PREFIX): value
        for key, value in sorted(payload.items())
        if key.startswith(_CALIBRATION_PREFIX)
    }
    return (graders, calibrations)


def _gather_evidence(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: EvaluationEvidencePort,
    subject_role_id: str,
    principal_id: str,
    task_id: str,
    scope: Mapping[str, str],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> _Evidence:
    """Read every piece of evaluation evidence through the governed path.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected evaluation-evidence port.
        subject_role_id: Role under evaluation.
        principal_id: Authenticated requesting principal.
        task_id: Owning task identity.
        scope: Scope declared for the tool calls.
        at_time: Call time.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.

    Returns:
        The gathered evidence, carrying a refusal when it could not complete.
    """
    empty: Mapping[str, str] = {}
    readers = (
        (EVALUATION_SET_TOOL, port.list_versioned_sets),
        (GRADER_CALIBRATION_TOOL, port.get_grader_calibrations),
        (GATE_OUTCOME_TOOL, port.get_gate_outcomes),
        (BASELINE_TOOL, port.get_baseline_comparison),
    )
    missing = tuple(name for name, _ in readers if name not in tool_policies)
    if missing:
        return _Evidence(
            (
                "EVALUATION_TOOL_DENIED",
                f"Required evaluation tools are not registered: {', '.join(missing)}.",
            ),
            empty,
            empty,
            empty,
            empty,
            empty,
            0,
        )

    gathered: dict[str, Mapping[str, str]] = {}
    attempted = 0
    for name, reader in readers:
        attempted += 1
        outcome = call_evaluation_tool(
            mandate,
            policy,
            tool_policies[name],
            principal_id,
            task_id,
            scope,
            _bind_reader(reader, subject_role_id),
            at_time,
            nonce_store=nonce_store,
            audit_store=audit_store,
            calls_used=attempted - 1,
        )
        if not outcome.allowed or not outcome.payload:
            return _Evidence(
                (
                    "EVALUATION_TOOL_DENIED",
                    f"{name} returned no evidence: {outcome.denial_reason}.",
                ),
                empty,
                empty,
                empty,
                empty,
                empty,
                attempted,
            )
        gathered[name] = outcome.payload

    graders, calibrations = _split_calibrations(gathered[GRADER_CALIBRATION_TOOL])
    return _Evidence(
        None,
        gathered[EVALUATION_SET_TOOL],
        graders,
        calibrations,
        gathered[GATE_OUTCOME_TOOL],
        gathered[BASELINE_TOOL],
        attempted,
    )


def _bind_reader(
    reader: Callable[[str], Mapping[str, str]],
    role_id: str,
) -> Callable[[], Mapping[str, object]]:
    """Bind one evidence reader to a role identity.

    Args:
        reader: Receiver operation taking a role identity.
        role_id: Role under evaluation.

    Returns:
        A zero-argument callable performing the read.
    """

    def read() -> Mapping[str, object]:
        """Perform the bound evidence read.

        Returns:
            The receiver's evidence.
        """
        return reader(role_id)

    return read


def evaluate_agent(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: EvaluationEvidencePort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    subject_role_id: str,
    subject_role_version: str,
    baseline_ref: str,
    sample_size: str,
    consecutive_failures: int = 0,
    principal_id: str = "agent-evaluation-manager",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[EconomicAcceptanceVerdict]:
    """Evaluate one role and decide whether it continues.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected evaluation-evidence port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        subject_role_id: Role under evaluation.
        subject_role_version: Version of the role under evaluation.
        baseline_ref: Simpler baseline the subject is compared against.
        sample_size: Observation count backing the evaluation.
        consecutive_failures: Prior consecutive failed evaluations.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a binding acceptance verdict, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Evaluation manager evaluating role %s", subject_role_id)

    evidence = _gather_evidence(
        mandate,
        policy,
        tool_policies,
        port,
        subject_role_id,
        principal_id,
        task.task_id,
        scope,
        now,
        nonce_store,
        audit_store,
    )
    if evidence.refusal is not None:
        reason, detail = evidence.refusal
        return _refuse(
            task,
            manifest,
            profile,
            (reason,),
            detail,
            now,
            "evaluate",
            evidence.tool_calls,
        )

    try:
        plan = build_evaluation_plan(
            {
                "plan_id": derive_stable_id("id", f"eval-plan:{task.task_id}"),
                "task_id": task.task_id,
                "subject_role_id": subject_role_id,
                "subject_role_version": subject_role_version,
                "evaluation_sets": dict(evidence.sets),
                "graders": dict(evidence.graders),
                "grader_calibrations": dict(evidence.calibrations),
                "baseline_ref": baseline_ref,
                "sample_size": sample_size,
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("EVALUATION_COVERAGE_INCOMPLETE",),
            str(error),
            now,
            "evaluate",
            evidence.tool_calls,
        )

    comparison_failure = verify_comparison(evidence.comparison)
    if comparison_failure is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("BASELINE_COMPARISON_UNAVAILABLE",),
            comparison_failure,
            now,
            "evaluate",
            evidence.tool_calls,
        )

    return _decide(
        task,
        manifest,
        runtime,
        profile,
        plan,
        evidence,
        consecutive_failures,
        now,
    )


def _decide(
    task: AgentTask,
    manifest: RoleManifest,
    runtime: AdkRuntime,
    profile: ModelProfile,
    plan: EvaluationPlan,
    evidence: _Evidence,
    consecutive_failures: int,
    at_time: datetime,
) -> AgentResult[EconomicAcceptanceVerdict]:
    """Compute the acceptance outcome and have the model explain it.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        plan: Validated evaluation plan.
        evidence: Gathered evaluation evidence.
        consecutive_failures: Prior consecutive failed evaluations.
        at_time: Result time.

    Returns:
        A typed result carrying a binding verdict, or a refusal.
    """
    try:
        comparison = build_baseline_comparison(
            {
                "candidate_score": Decimal(evidence.comparison["candidate_score"]),
                "baseline_score": Decimal(evidence.comparison["baseline_score"]),
                "uncertainty_halfwidth": Decimal(
                    evidence.comparison["uncertainty_halfwidth"],
                ),
                "cost_delta": Decimal(evidence.comparison["cost_delta"]),
                "metric": evidence.comparison["metric"],
            },
        )
    except (InvalidOperation, ValueError) as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("BASELINE_COMPARISON_UNAVAILABLE",),
            f"The baseline comparison could not be read: {error}",
            at_time,
            "evaluate",
            evidence.tool_calls,
        )

    # The outcome is arithmetic on evidence. The model explains it; it cannot
    # change it, and it is computed before the model is even invoked.
    failed = failed_safety_gates(evidence.gates)
    action = required_action(failed, comparison.survives, consecutive_failures)

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"eval:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "subject_role_id": plan.subject_role_id,
                "plan_hash": plan.plan_hash,
                "metric": comparison.metric,
                "margin": str(comparison.margin),
                "hurdle": str(comparison.hurdle),
                "survives_baseline": str(comparison.survives),
                "failed_gates": ",".join(failed) or "none",
                "required_action": action,
                "sample_size": plan.sample_size,
            },
            "untrusted_evidence": {
                f"set:{kind}": ref for kind, ref in sorted(plan.evaluation_sets.items())
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_EVALUATE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The manager declined to explain the acceptance outcome.",
            at_time,
            "evaluate",
            evidence.tool_calls,
            outcome,
        )

    verdict = build_economic_acceptance_verdict(
        {
            "verdict_id": derive_stable_id("id", f"eval:{task.task_id}:verdict"),
            "task_id": task.task_id,
            "plan_id": plan.plan_id,
            "plan_hash": plan.plan_hash,
            "subject_role_id": plan.subject_role_id,
            "gate_outcomes": dict(evidence.gates),
            "comparison": comparison,
            # Computed, not taken from the model.
            "required_action": action,
            "rationale": outcome.output.get("rationale", ""),
            "uncertainty_statement": outcome.output.get("uncertainty_statement", ""),
            "consecutive_failures": consecutive_failures,
        },
    )
    logger.info(
        "Evaluation manager decided %s for role %s: margin %s against hurdle %s",
        verdict.required_action,
        plan.subject_role_id,
        comparison.margin,
        comparison.hurdle,
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"evaluate:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": verdict,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, evidence.tool_calls),
        },
    )


def _grounded_challenges(
    artifact: CodeArtifact | None,
    sweep: SweepVerdict | None,
    experiment: ExperimentVerdict | None,
) -> dict[str, str]:
    """Derive challenges the supplied evidence already substantiates.

    A critic is not asked whether a sweep had failed trials or whether an
    artefact is blocked; the evidence says so, and the challenge is written
    from it.

    Args:
        artifact: Candidate code artefact, when one was supplied.
        sweep: Candidate sweep verdict, when one was supplied.
        experiment: Candidate experiment verdict, when one was supplied.

    Returns:
        Challenge kind to grounded statement.
    """
    grounded: dict[str, str] = {}
    if artifact is not None and artifact.promotion_status != "ready":
        grounded["operational"] = (
            f"The candidate artefact is {artifact.promotion_status}, so it is not "
            "operationally complete; whatever blocks it must be resolved by a "
            "human before this candidate can be considered further."
        )
    if sweep is not None and sweep.trials.failed:
        grounded["robustness"] = (
            f"{sweep.trials.failed} of {sweep.trials.attempted} search trials "
            "failed, so the surviving candidates are not a random sample of the "
            "space and the reported robustness is conditional on that."
        )
    if experiment is not None and experiment.holdout_consumed:
        grounded["causality"] = (
            "This candidate has already consumed its thesis's holdout, so no "
            "further out-of-sample evidence is available to distinguish a causal "
            "mechanism from a fitted one."
        )
    return grounded


def critique_candidate(
    registry: RoleRegistry,
    task: AgentTask,
    runtime: AdkRuntime,
    profile: ModelProfile,
    candidate_ref: str,
    artifact: CodeArtifact | None = None,
    sweep_verdict: SweepVerdict | None = None,
    experiment_verdict: ExperimentVerdict | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[CritiqueMemo]:
    """Critique one candidate across every required challenge.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        candidate_ref: Candidate artefact under critique.
        artifact: Candidate code artefact, when one was produced.
        sweep_verdict: Candidate sweep verdict, when one was produced.
        experiment_verdict: Candidate experiment verdict, when one was
            produced.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a critique memo, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Evaluation manager critiquing candidate %s", candidate_ref)

    if artifact is None and sweep_verdict is None and experiment_verdict is None:
        return _refuse(
            task,
            manifest,
            profile,
            ("CANDIDATE_EVIDENCE_ABSENT",),
            "A critique requires at least one piece of candidate evidence.",
            now,
            "critique",
        )

    grounded = _grounded_challenges(artifact, sweep_verdict, experiment_verdict)
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"critique:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            "trusted_context": {
                "candidate_ref": candidate_ref,
                **{f"grounded:{kind}": text for kind, text in sorted(grounded.items())},
            },
            "untrusted_evidence": _candidate_evidence(
                artifact,
                sweep_verdict,
                experiment_verdict,
            ),
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": None,
        },
    )
    outcome = runtime.execute_node(_CRITIQUE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The critic declined to critique the candidate.",
            now,
            "critique",
            outcome=outcome,
        )

    # Grounded challenges override the model's: where the evidence already
    # says something, the evidence is what the memo records.
    challenges = {
        **_section(outcome.output, "challenge:"),
        **grounded,
    }
    try:
        memo = build_critique_memo(
            {
                "memo_id": derive_stable_id("id", f"critique:{task.task_id}"),
                "task_id": task.task_id,
                "candidate_ref": candidate_ref,
                "challenges": challenges,
                "unsubstantiated": _lines(outcome.output.get("unsubstantiated")),
                "blocking_concerns": _lines(outcome.output.get("blocking_concerns")),
                "evidence_refs": _lines(outcome.output.get("evidence_refs")),
            },
        )
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("CRITIQUE_COVERAGE_INCOMPLETE",),
            str(error),
            now,
            "critique",
            outcome=outcome,
        )

    logger.info(
        "Evaluation manager recorded %d blocking concerns for candidate %s",
        len(memo.blocking_concerns),
        candidate_ref,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"critique:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": memo,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, 0),
        },
    )


def _candidate_evidence(
    artifact: CodeArtifact | None,
    sweep: SweepVerdict | None,
    experiment: ExperimentVerdict | None,
) -> dict[str, str]:
    """Render the supplied candidate evidence as bounded untrusted context.

    Args:
        artifact: Candidate code artefact, when one was supplied.
        sweep: Candidate sweep verdict, when one was supplied.
        experiment: Candidate experiment verdict, when one was supplied.

    Returns:
        Bounded untrusted evidence entries.
    """
    evidence: dict[str, str] = {}
    if artifact is not None:
        evidence["artifact:hash"] = artifact.artifact_hash
        evidence["artifact:status"] = artifact.promotion_status
    if sweep is not None:
        evidence["sweep:search_id"] = sweep.search_id
        evidence["sweep:robustness"] = sweep.robustness_evidence
        evidence["sweep:overfit"] = sweep.overfit_evidence
    if experiment is not None:
        evidence["experiment:outcome"] = experiment.outcome
        evidence["experiment:spec_hash"] = experiment.spec_hash
    return evidence


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
