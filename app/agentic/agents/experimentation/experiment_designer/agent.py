"""Provider-neutral Experiment Designer agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates design and interpretation to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. A protocol
is pre-registered and hashed before any run, so its falsification criterion
cannot be rewritten afterwards (`FR-AGENTIC-040`). The receiver's request is
passed through unchanged and its result is checked for binding rather than
reconciled, so no simulation request or result is ever authored here
(`FR-AGENTIC-041`). And every conclusion is keyed by the run identifier the
receiver returned, never by one the model supplied (`FR-AGENTIC-042`).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.experimentation.experiment_designer.schemas import (
    ExperimentSpec,
    ExperimentVerdict,
    build_experiment_spec,
    build_experiment_verdict,
    validate_split_windows,
)
from app.agentic.agents.experimentation.experiment_designer.tools import (
    BACKTEST_TOOL,
    REQUIRED_LINEAGE,
    call_simulation_tool,
    verify_result_binding,
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

    from app.agentic.agents.experimentation.experiment_designer.repository import (
        AgenticExperimentStore,
    )
    from app.agentic.agents.experimentation.experiment_designer.schemas import (
        EvidenceClass,
        SplitWindow,
    )
    from app.agentic.agents.experimentation.experiment_designer.tools import (
        SimulationPort,
    )
    from app.agentic.agents.strategy_desk.strategy_thesis_analyst.schemas import (
        Hypothesis,
        StrategyThesis,
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

ROLE_ID = "experiment_designer"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_DESIGN_NODE_ID = "design_experiment"
_COORDINATE_NODE_ID = "coordinate_simulation"

_VERDICT_OUTCOMES = frozenset({"refuted", "not_refuted", "inconclusive"})


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
    """Build the reproducible lineage for one design or coordination.

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
    """Build the bounded consumption record for one design or coordination.

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
        "Experiment designer refusing %s for task %s: %s",
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


def _design_ineligibility(
    hypotheses: tuple[Hypothesis, ...],
    input_refs: tuple[str, ...],
    baseline_ref: str,
    splits: tuple[SplitWindow, ...],
    embargo_seconds: int,
) -> tuple[str, str] | None:
    """Determine whether a protocol can be designed at all.

    Each condition refuses before the model is reached, so no model is paid to
    design a protocol that could not be pre-registered.

    Args:
        hypotheses: Hypotheses under test.
        input_refs: Versioned immutable inputs.
        baseline_ref: Registered baseline to compare against.
        splits: Declared evaluation windows.
        embargo_seconds: Gap required between consecutive splits.

    Returns:
        The enumerated reason and detail, or None when eligible.
    """
    # Falsifiability itself is not re-checked here: `FEAT-AGT-13` makes a
    # `Hypothesis` without a rejection criterion unrepresentable, so a thesis
    # that could not fail cannot reach this function at all.
    if not hypotheses:
        return ("HYPOTHESES_ABSENT", "A protocol must name the hypotheses it tests.")
    if not input_refs:
        return ("INPUTS_ABSENT", "A protocol must name its versioned inputs.")
    if not baseline_ref:
        return (
            "BASELINE_ABSENT",
            "A protocol must name a baseline to compare against.",
        )
    split_failure = validate_split_windows(splits, embargo_seconds)
    if split_failure is not None:
        return ("SPLITS_INVALID", split_failure)
    return None


def design_experiment(
    registry: RoleRegistry,
    task: AgentTask,
    runtime: AdkRuntime,
    profile: ModelProfile,
    thesis: StrategyThesis,
    hypotheses: tuple[Hypothesis, ...],
    input_refs: tuple[str, ...],
    splits: tuple[SplitWindow, ...],
    embargo_seconds: int,
    baseline_ref: str,
    cost_model_ref: str,
    metrics: tuple[str, ...],
    seed: int,
    store: AgenticExperimentStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[ExperimentSpec]:
    """Design one immutable, pre-registered experiment protocol.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        thesis: Thesis this protocol is designed to refute.
        hypotheses: Hypotheses under test, at least one falsifiable.
        input_refs: Versioned immutable inputs the protocol reads.
        splits: Ordered non-overlapping evaluation windows.
        embargo_seconds: Gap enforced between consecutive splits.
        baseline_ref: Registered baseline every conclusion compares against.
        cost_model_ref: Registered execution-cost model applied.
        metrics: Catalogued metric names evaluated.
        seed: Reproducibility seed for every run under this protocol.
        store: Injected experiment ledger; the protocol is recorded when given.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a pre-registered protocol, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Experiment designer starting design for task %s", task.task_id)

    ineligible = _design_ineligibility(
        hypotheses,
        input_refs,
        baseline_ref,
        splits,
        embargo_seconds,
    )
    if ineligible is not None:
        reason, detail = ineligible
        return _refuse(task, manifest, profile, (reason,), detail, now, "design")

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"design:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # Windows, baseline, costs, and seed are deterministic caller facts.
            # The model designs the criterion, not the configuration.
            "trusted_context": {
                "thesis_id": thesis.thesis_id,
                "baseline_ref": baseline_ref,
                "cost_model_ref": cost_model_ref,
                "seed": str(seed),
                "embargo_seconds": str(embargo_seconds),
                **{
                    f"split:{window.label}": (
                        f"{window.start.isoformat()}/{window.end.isoformat()}"
                    )
                    for window in splits
                },
                **{f"metric:{metric}": "catalogued" for metric in metrics},
            },
            "untrusted_evidence": {
                f"hypothesis:{hypothesis.hypothesis_id}": (
                    hypothesis.rejection_criterion
                )
                for hypothesis in hypotheses
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": seed,
        },
    )
    outcome = runtime.execute_node(_DESIGN_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The designer declined to specify a protocol.",
            now,
            "design",
            outcome=outcome,
        )

    spec = build_experiment_spec(
        {
            "spec_id": derive_stable_id("id", f"spec:{task.task_id}"),
            "task_id": task.task_id,
            "thesis_id": thesis.thesis_id,
            "hypothesis_ids": tuple(
                hypothesis.hypothesis_id for hypothesis in hypotheses
            ),
            "input_refs": input_refs,
            "splits": splits,
            "embargo_seconds": embargo_seconds,
            "cost_model_ref": cost_model_ref,
            "seed": seed,
            "baseline_ref": baseline_ref,
            "metrics": metrics,
            "stop_rules": _lines(outcome.output.get("stop_rules")),
            "falsification_outcome": outcome.output.get(
                "falsification_outcome",
                "",
            ),
            "leakage_controls": _lines(outcome.output.get("leakage_controls")),
        },
    )
    if store is not None:
        store.save_spec(spec)
    logger.info(
        "Experiment designer pre-registered protocol %s for task %s",
        spec.spec_hash,
        task.task_id,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"design:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": spec,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, 0),
        },
    )


def _coordination_ineligibility(
    spec: ExperimentSpec,
    evidence_class: EvidenceClass,
    store: AgenticExperimentStore | None,
) -> tuple[str, str] | None:
    """Determine whether a run may be coordinated against a protocol.

    Args:
        spec: Pre-registered protocol.
        evidence_class: Evidence class the run would represent.
        store: Injected experiment ledger.

    Returns:
        The enumerated reason and detail, or None when eligible.
    """
    if store is None:
        return None
    if store.load_spec(spec.spec_hash) is None:
        return (
            "PROTOCOL_NOT_REGISTERED",
            "The protocol was not pre-registered before the run.",
        )
    if evidence_class == "holdout" and store.holdout_spent(spec.spec_hash):
        return (
            "HOLDOUT_ALREADY_CONSUMED",
            "This protocol's one look at holdout has already been spent.",
        )
    return None


def coordinate_simulation(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: SimulationPort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    spec: ExperimentSpec,
    request: Mapping[str, str],
    evidence_class: EvidenceClass = "discovery",
    store: AgenticExperimentStore | None = None,
    principal_id: str = "agent-experiment-designer",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[ExperimentVerdict]:
    """Execute one receiver-owned run and bind a verdict to what it returned.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected Simulation port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        spec: Pre-registered protocol this run belongs to.
        request: Caller-supplied receiver-owned backtest request, passed
            through unchanged.
        evidence_class: Evidence class this run represents.
        store: Injected experiment ledger.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a run-bound verdict, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Experiment designer coordinating a run for task %s", task.task_id)

    ineligible = _coordination_ineligibility(spec, evidence_class, store)
    if ineligible is not None:
        reason, detail = ineligible
        return _refuse(task, manifest, profile, (reason,), detail, now, "coordinate")

    tool = tool_policies.get(BACKTEST_TOOL)
    if tool is None:
        return _refuse(
            task,
            manifest,
            profile,
            ("SIMULATION_TOOL_DENIED",),
            "The Simulation backtest tool is not registered.",
            now,
            "coordinate",
        )
    result = call_simulation_tool(
        mandate,
        policy,
        tool,
        principal_id,
        task.task_id,
        scope,
        lambda: port.submit_backtest(request),
        now,
        nonce_store=nonce_store,
        audit_store=audit_store,
    )
    if not result.allowed or not result.payload:
        return _refuse(
            task,
            manifest,
            profile,
            ("SIMULATION_TOOL_DENIED",),
            f"A governed tool was denied: {result.denial_reason}.",
            now,
            "coordinate",
            1,
        )

    # The receiver owns its result. A returned result that does not bind to the
    # submitted request is a fault to report, never one to reconcile.
    binding_failure = verify_result_binding(request, result.payload)
    if binding_failure is not None:
        return _refuse(
            task,
            manifest,
            profile,
            ("RESULT_NOT_FOR_REQUEST",),
            binding_failure,
            now,
            "coordinate",
            1,
        )

    run_id = result.payload["run_id"]
    lineage = {field: result.payload[field] for field in REQUIRED_LINEAGE}
    consumed = _consume_holdout(spec, evidence_class, store, task.task_id, run_id, now)
    if store is not None:
        store.record_run(spec.spec_hash, run_id, evidence_class, lineage, now)

    return _interpret_run(
        registry,
        task,
        manifest,
        runtime,
        profile,
        spec,
        run_id,
        lineage,
        evidence_class,
        consumed,
        store,
        now,
    )


def _consume_holdout(
    spec: ExperimentSpec,
    evidence_class: EvidenceClass,
    store: AgenticExperimentStore | None,
    task_id: str,
    run_id: str,
    at_time: datetime,
) -> bool:
    """Claim the protocol's single holdout use when this run needs it.

    Args:
        spec: Pre-registered protocol.
        evidence_class: Evidence class this run represents.
        store: Injected experiment ledger.
        task_id: Owning task identity.
        run_id: Receiver-returned run identity.
        at_time: Consumption time.

    Returns:
        True when this run spent the protocol's holdout.
    """
    if evidence_class != "holdout":
        return False
    if store is None:
        return True
    return store.reserve_holdout(spec.spec_hash, task_id, run_id, at_time)


def _interpret_run(
    registry: RoleRegistry,
    task: AgentTask,
    manifest: RoleManifest,
    runtime: AdkRuntime,
    profile: ModelProfile,
    spec: ExperimentSpec,
    run_id: str,
    lineage: dict[str, str],
    evidence_class: EvidenceClass,
    holdout_consumed: bool,
    store: AgenticExperimentStore | None,
    at_time: datetime,
) -> AgentResult[ExperimentVerdict]:
    """Read one completed run against its pre-registered falsification outcome.

    Args:
        registry: Validated role registry.
        task: Owning governed task.
        manifest: Resolved role manifest.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        spec: Pre-registered protocol.
        run_id: Receiver-returned run identity.
        lineage: Receiver-returned reproducibility references.
        evidence_class: Evidence class this run represents.
        holdout_consumed: Whether this run spent the protocol's holdout.
        store: Injected experiment ledger.
        at_time: Result time.

    Returns:
        A typed result carrying a run-bound verdict, or a refusal.
    """
    del registry
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"verdict:{task.task_id}:{run_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # The pre-registered criterion is trusted context: it was fixed
            # before the run, so the model reads it rather than restating it.
            "trusted_context": {
                "spec_hash": spec.spec_hash,
                "falsification_outcome": spec.falsification_outcome,
                "baseline_ref": spec.baseline_ref,
                "evidence_class": evidence_class,
                "run_id": run_id,
            },
            "untrusted_evidence": dict(sorted(lineage.items())),
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": spec.seed,
        },
    )
    outcome = runtime.execute_node(_COORDINATE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The designer declined to read the completed run.",
            at_time,
            "coordinate",
            1,
            outcome,
        )

    declared = outcome.output.get("outcome", "inconclusive")
    verdict = build_experiment_verdict(
        {
            "verdict_id": derive_stable_id("id", f"verdict:{task.task_id}:{run_id}"),
            "task_id": task.task_id,
            "spec_id": spec.spec_id,
            "spec_hash": spec.spec_hash,
            # Keyed by the run the receiver returned, never by one the model
            # supplied: a conclusion cannot name a run that did not execute.
            "conclusions": {run_id: outcome.output.get("conclusion", "")},
            "evidence_classes": {run_id: evidence_class},
            "outcome": declared if declared in _VERDICT_OUTCOMES else "inconclusive",
            "holdout_consumed": holdout_consumed,
            "limitations": _lines(outcome.output.get("limitations")),
            "retained_conflicts": _lines(outcome.output.get("conflicts")),
        },
    )
    if store is not None:
        store.save_verdict(verdict)
    logger.info(
        "Experiment designer bound verdict %s to run %s",
        verdict.outcome,
        run_id,
    )
    return build_agent_result(
        {
            **_envelope(task, at_time),
            "result_id": derive_stable_id("id", f"coordinate:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": verdict,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, at_time),
            "budget_usage": _usage(task, at_time, outcome, 1),
        },
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
