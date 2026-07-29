"""Provider-neutral Optimization Coordinator agent.

Resolves the enabled role manifest, verifies the package-local `prompt.md`, and
delegates design and interpretation to the injected `AdkRuntime`.

Three properties are enforced here rather than trusted to the model. The plan
is declared and hashed before any trial runs (`FR-AGENTIC-043`). Only public
Optimization operations are called, through the governed tool path, and the
trial accounting must reconcile (`FR-AGENTIC-044`). And robustness, stability,
and overfit evidence are read from deterministic receiver operations rather
than asserted, so a verdict cannot consist of a rank alone
(`FR-AGENTIC-045`).

Holdout is shared state. A sweep declaring consumption reserves it from the
same `FEAT-AGT-14` ledger an experiment would, so a thesis's single look cannot
be spent once by an experiment and again by a sweep.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
    SweepPlan,
    SweepVerdict,
    build_sweep_plan,
    build_sweep_verdict,
    build_trial_ledger,
)
from app.agentic.agents.experimentation.optimization_coordinator.tools import (
    OVERFIT_TOOL,
    ROBUSTNESS_TOOL,
    STABILITY_TOOL,
    SWEEP_TOOL,
    call_optimization_tool,
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
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from datetime import datetime

    from app.agentic.agents.experimentation.experiment_designer.repository import (
        AgenticExperimentStore,
    )
    from app.agentic.agents.experimentation.experiment_designer.schemas import (
        ExperimentSpec,
    )
    from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
        HoldoutConsumption,
        SearchMethod,
        TrialLedger,
    )
    from app.agentic.agents.experimentation.optimization_coordinator.tools import (
        OptimizationPort,
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

ROLE_ID = "optimization_coordinator"
PROMPT_PATH = Path(__file__).with_name("prompt.md")

_DESIGN_NODE_ID = "design_sweep"
_COORDINATE_NODE_ID = "coordinate_optimization"

# A cumulative search budget past which a finding is weak evidence whatever it
# reports. The plan is not refused for reaching it, but the verdict must say so.
LIFETIME_TRIAL_WARNING = 500


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
    search_trials: int = 0,
) -> object:
    """Build the bounded consumption record for one design or coordination.

    Args:
        task: Owning governed task.
        at_time: Result time.
        outcome: Model outcome when an invocation occurred.
        tool_calls: Governed tool calls attempted.
        search_trials: Search trials consumed.

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
            "search_trials": search_trials,
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
        "Optimization coordinator refusing %s for task %s: %s",
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
    spec: ExperimentSpec,
    parameter_space: Mapping[str, str],
    trial_budget: int,
    holdout_consumption: HoldoutConsumption,
    store: AgenticExperimentStore | None,
) -> tuple[str, str] | None:
    """Determine whether a sweep can be planned at all.

    Each condition refuses before the model is reached, so no model is paid to
    plan a search that could not run.

    Args:
        spec: Pre-registered experiment protocol this sweep serves.
        parameter_space: Bounded candidate values per parameter name.
        trial_budget: Trials this plan would authorise.
        holdout_consumption: Whether this sweep would spend holdout.
        store: Injected experiment ledger.

    Returns:
        The enumerated reason and detail, or None when eligible.
    """
    if not parameter_space:
        return ("SPACE_NOT_BOUNDED", "A sweep must declare a bounded parameter space.")
    if trial_budget <= 0:
        return ("BUDGET_NOT_DECLARED", "A sweep must declare a positive trial budget.")
    if store is None:
        return None
    if store.load_spec(spec.spec_hash) is None:
        return (
            "PROTOCOL_NOT_REGISTERED",
            "The experiment protocol was not pre-registered before the sweep.",
        )
    if holdout_consumption == "consumes" and store.holdout_spent(spec.spec_hash):
        return (
            "HOLDOUT_ALREADY_CONSUMED",
            "This thesis's one look at holdout has already been spent.",
        )
    return None


def design_sweep(
    registry: RoleRegistry,
    task: AgentTask,
    runtime: AdkRuntime,
    profile: ModelProfile,
    spec: ExperimentSpec,
    parameter_space: Mapping[str, str],
    objective: str,
    method: SearchMethod,
    trial_budget: int,
    seed: int,
    holdout_consumption: HoldoutConsumption = "none",
    prior_trials_consumed: int = 0,
    store: AgenticExperimentStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[SweepPlan]:
    """Declare one bounded sweep in full before anything runs.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        spec: Pre-registered experiment protocol this sweep serves.
        parameter_space: Bounded candidate values per parameter name.
        objective: Objective the search optimises.
        method: Search method the receiver will use.
        trial_budget: Maximum trials this plan authorises.
        seed: Reproducibility seed for the search.
        holdout_consumption: Whether this sweep spends the thesis's holdout.
        prior_trials_consumed: Trials already spent on this thesis.
        store: Injected experiment ledger.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a pre-declared plan, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    logger.info("Optimization coordinator planning for task %s", task.task_id)

    ineligible = _design_ineligibility(
        spec,
        parameter_space,
        trial_budget,
        holdout_consumption,
        store,
    )
    if ineligible is not None:
        reason, detail = ineligible
        return _refuse(task, manifest, profile, (reason,), detail, now, "design")

    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id("id", f"sweep-plan:{task.task_id}"),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # Space, budget, method, and seed are deterministic caller facts.
            # The model justifies the search; it does not size it.
            "trusted_context": {
                "spec_hash": spec.spec_hash,
                "objective": objective,
                "method": method,
                "trial_budget": str(trial_budget),
                "seed": str(seed),
                "holdout_consumption": holdout_consumption,
                "prior_trials_consumed": str(prior_trials_consumed),
                **{
                    f"space:{name}": values
                    for name, values in sorted(parameter_space.items())
                },
            },
            "untrusted_evidence": {"falsification": spec.falsification_outcome},
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
            "The coordinator declined to plan a sweep.",
            now,
            "design",
            outcome=outcome,
        )

    plan = build_sweep_plan(
        {
            "plan_id": derive_stable_id("id", f"sweep-plan:{task.task_id}"),
            "task_id": task.task_id,
            "spec_hash": spec.spec_hash,
            "parameter_space": dict(parameter_space),
            "objective": objective,
            "method": method,
            "trial_budget": trial_budget,
            "early_stop_policy": outcome.output.get("early_stop_policy", ""),
            "seed": seed,
            "holdout_consumption": holdout_consumption,
            "prior_trials_consumed": prior_trials_consumed,
            "justification": outcome.output.get("justification", ""),
        },
    )
    logger.info(
        "Optimization coordinator declared plan %s with %d trials",
        plan.plan_hash,
        plan.trial_budget,
    )
    return build_agent_result(
        {
            **_envelope(task, now),
            "result_id": derive_stable_id("id", f"design:{task.task_id}:ok"),
            "task_id": task.task_id,
            "status": "ok",
            "payload": plan,
            "reasons": (),
            "detail": None,
            "provenance": _provenance(task, manifest, profile, now),
            "budget_usage": _usage(task, now, outcome, 0),
        },
    )


class _Evidence:
    """Deterministic evidence gathered from the receiver before interpretation.

    Attributes:
        refusal: Enumerated reason and detail when gathering failed.
        result: Receiver-returned search result.
        robustness: Receiver-returned robustness evidence.
        stability: Receiver-returned stability evidence.
        overfit: Receiver-returned overfit evidence.
        tool_calls: Governed tool calls attempted.
    """

    __slots__ = (
        "overfit",
        "refusal",
        "result",
        "robustness",
        "stability",
        "tool_calls",
    )

    def __init__(
        self,
        refusal: tuple[str, str] | None,
        result: Mapping[str, str],
        robustness: Mapping[str, str],
        stability: Mapping[str, str],
        overfit: Mapping[str, str],
        tool_calls: int,
    ) -> None:
        """Store the gathered evidence.

        Args:
            refusal: Enumerated reason and detail, or None.
            result: Receiver-returned search result.
            robustness: Receiver-returned robustness evidence.
            stability: Receiver-returned stability evidence.
            overfit: Receiver-returned overfit evidence.
            tool_calls: Governed tool calls attempted.
        """
        self.refusal = refusal
        self.result = result
        self.robustness = robustness
        self.stability = stability
        self.overfit = overfit
        self.tool_calls = tool_calls


def _gather_evidence(
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: OptimizationPort,
    plan: SweepPlan,
    request: Mapping[str, str],
    principal_id: str,
    task_id: str,
    scope: Mapping[str, str],
    at_time: datetime,
    nonce_store: ApprovalNonceStore | None,
    audit_store: AgenticMemoryStore | None,
) -> _Evidence:
    """Run the search and read every deterministic evidence operation.

    Args:
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected Optimization port.
        plan: Pre-declared sweep plan.
        request: Caller-supplied receiver-owned search request.
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
    missing = tuple(
        name
        for name in (SWEEP_TOOL, ROBUSTNESS_TOOL, STABILITY_TOOL, OVERFIT_TOOL)
        if name not in tool_policies
    )
    if missing:
        return _Evidence(
            (
                "OPTIMIZATION_TOOL_DENIED",
                "Required Optimization tools are not registered: "
                f"{', '.join(missing)}.",
            ),
            empty,
            empty,
            empty,
            empty,
            0,
        )

    attempted = 1
    sweep = call_optimization_tool(
        mandate,
        policy,
        tool_policies[SWEEP_TOOL],
        principal_id,
        task_id,
        scope,
        lambda: port.run_sweep(request),
        at_time,
        nonce_store=nonce_store,
        audit_store=audit_store,
    )
    if not sweep.allowed or not sweep.payload:
        return _Evidence(
            (
                "OPTIMIZATION_TOOL_DENIED",
                f"A governed tool was denied: {sweep.denial_reason}.",
            ),
            empty,
            empty,
            empty,
            empty,
            attempted,
        )

    binding_failure = verify_result_binding(plan.seed, sweep.payload)
    if binding_failure is not None:
        return _Evidence(
            ("RESULT_NOT_FOR_PLAN", binding_failure),
            empty,
            empty,
            empty,
            empty,
            attempted,
        )

    search_id = sweep.payload["search_id"]
    gathered: dict[str, Mapping[str, str]] = {}
    for name, reader in (
        (ROBUSTNESS_TOOL, port.robustness_score),
        (STABILITY_TOOL, port.parameter_stability),
        (OVERFIT_TOOL, port.overfit_evidence),
    ):
        attempted += 1
        outcome = call_optimization_tool(
            mandate,
            policy,
            tool_policies[name],
            principal_id,
            task_id,
            scope,
            _bind_reader(reader, search_id),
            at_time,
            nonce_store=nonce_store,
            audit_store=audit_store,
            calls_used=attempted - 1,
        )
        if not outcome.allowed or not outcome.payload:
            return _Evidence(
                (
                    "ROBUSTNESS_EVIDENCE_UNAVAILABLE",
                    f"{name} returned no evidence: {outcome.denial_reason}.",
                ),
                empty,
                empty,
                empty,
                empty,
                attempted,
            )
        gathered[name] = outcome.payload

    return _Evidence(
        None,
        sweep.payload,
        gathered[ROBUSTNESS_TOOL],
        gathered[STABILITY_TOOL],
        gathered[OVERFIT_TOOL],
        attempted,
    )


def _bind_reader(
    reader: Callable[[str], Mapping[str, str]],
    search_id: str,
) -> Callable[[], Mapping[str, object]]:
    """Bind one evidence reader to a search identity.

    Args:
        reader: Receiver operation taking a search identity.
        search_id: Receiver-returned search identity.

    Returns:
        A zero-argument callable performing the read.
    """

    def read() -> Mapping[str, object]:
        """Perform the bound evidence read.

        Returns:
            The receiver's evidence.
        """
        return reader(search_id)

    return read


def _ledger_from_result(
    plan: SweepPlan,
    result: Mapping[str, str],
) -> TrialLedger:
    """Build the trial ledger from what the receiver reported.

    Args:
        plan: Pre-declared sweep plan.
        result: Receiver-returned search result.

    Returns:
        A validated immutable ledger.

    Raises:
        ValueError: If the reported accounting does not reconcile.
    """
    failure_reasons = {
        key.removeprefix("failed_trial:"): value
        for key, value in sorted(result.items())
        if key.startswith("failed_trial:")
    }
    completed = int(result.get("trials_completed", "0"))
    return build_trial_ledger(
        {
            "attempted": int(result.get("trials_attempted", "0")),
            "completed": completed,
            "failed": len(failure_reasons),
            "failure_reasons": failure_reasons,
            "budget": plan.trial_budget,
        },
    )


def coordinate_optimization(
    registry: RoleRegistry,
    task: AgentTask,
    mandate: FirmMandate,
    policy: AgentPolicy,
    tool_policies: Mapping[str, ToolPolicy],
    port: OptimizationPort,
    runtime: AdkRuntime,
    profile: ModelProfile,
    plan: SweepPlan,
    request: Mapping[str, str],
    store: AgenticExperimentStore | None = None,
    principal_id: str = "agent-optimization-coordinator",
    request_scope: Mapping[str, str] | None = None,
    nonce_store: ApprovalNonceStore | None = None,
    audit_store: AgenticMemoryStore | None = None,
    prompt_path: Path | None = None,
    at_time: datetime | None = None,
) -> AgentResult[SweepVerdict]:
    """Run one pre-declared sweep and report what the whole search showed.

    Args:
        registry: Validated role registry.
        task: Bounded governed task.
        mandate: Validated firm mandate.
        policy: Requesting agent policy.
        tool_policies: Registered tool identity to policy.
        port: Injected Optimization port.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        plan: Pre-declared sweep plan.
        request: Caller-supplied receiver-owned search request, passed through
            unchanged.
        store: Injected experiment ledger.
        principal_id: Authenticated requesting principal.
        request_scope: Scope declared for the tool calls.
        nonce_store: Injected single-use approval enforcement.
        audit_store: Injected governed audit store.
        prompt_path: Optional prompt override; the package artefact by default.
        at_time: Optional result time; current UTC when omitted.

    Returns:
        A typed result carrying a robustness-focused verdict, or a refusal.

    Raises:
        ValueError: If the role is unregistered or disabled, or its prompt
            artefact fails integrity verification.
    """
    now = at_time if at_time is not None else utc_now()
    manifest = resolve_role_manifest(registry, ROLE_ID)
    verify_prompt_artifact(manifest, prompt_path or PROMPT_PATH)
    scope = dict(request_scope or {"environment": policy.environment})
    logger.info("Optimization coordinator coordinating task %s", task.task_id)

    if (
        plan.holdout_consumption == "consumes"
        and store is not None
        and store.holdout_spent(plan.spec_hash)
    ):
        return _refuse(
            task,
            manifest,
            profile,
            ("HOLDOUT_ALREADY_CONSUMED",),
            "This thesis's one look at holdout has already been spent.",
            now,
            "coordinate",
        )

    evidence = _gather_evidence(
        mandate,
        policy,
        tool_policies,
        port,
        plan,
        request,
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
            "coordinate",
            evidence.tool_calls,
        )

    return _interpret(
        task,
        manifest,
        runtime,
        profile,
        plan,
        evidence,
        store,
        now,
    )


def _interpret(
    task: AgentTask,
    manifest: RoleManifest,
    runtime: AdkRuntime,
    profile: ModelProfile,
    plan: SweepPlan,
    evidence: _Evidence,
    store: AgenticExperimentStore | None,
    at_time: datetime,
) -> AgentResult[SweepVerdict]:
    """Read the gathered evidence into a robustness-focused verdict.

    Args:
        task: Owning governed task.
        manifest: Resolved role manifest.
        runtime: Injected agent-graph runtime.
        profile: Pinned evaluated model profile.
        plan: Pre-declared sweep plan.
        evidence: Deterministic evidence gathered from the receiver.
        store: Injected experiment ledger.
        at_time: Result time.

    Returns:
        A typed result carrying a verdict, or a refusal.
    """
    try:
        ledger = _ledger_from_result(plan, evidence.result)
    except ValueError as error:
        return _refuse(
            task,
            manifest,
            profile,
            ("TRIALS_NOT_RECONCILED",),
            str(error),
            at_time,
            "coordinate",
            evidence.tool_calls,
        )

    search_id = evidence.result["search_id"]
    invocation = build_model_invocation(
        {
            "invocation_id": derive_stable_id(
                "id", f"sweep:{task.task_id}:{search_id}"
            ),
            "task_id": task.task_id,
            "role_id": manifest.role_id,
            "composite_instruction_hash": manifest.composite_instruction_hash,
            # Robustness, stability, and overfit came from deterministic
            # operations. The model reads them; it never produces one.
            "trusted_context": {
                "plan_hash": plan.plan_hash,
                "search_id": search_id,
                "trials_attempted": str(ledger.attempted),
                "trials_completed": str(ledger.completed),
                "trials_failed": str(ledger.failed),
                "lifetime_trials": str(plan.prior_trials_consumed + ledger.attempted),
                **{
                    f"robustness:{k}": v for k, v in sorted(evidence.robustness.items())
                },
                **{f"stability:{k}": v for k, v in sorted(evidence.stability.items())},
                **{f"overfit:{k}": v for k, v in sorted(evidence.overfit.items())},
            },
            "untrusted_evidence": {
                f"candidate:{key}": value
                for key, value in sorted(evidence.result.items())
                if key.startswith("candidate:")
            },
            "max_output_tokens": min(profile.max_output_tokens, 4_000),
            "seed": plan.seed,
        },
    )
    outcome = runtime.execute_node(_COORDINATE_NODE_ID, profile, invocation)
    if outcome.status != "ok" or outcome.output is None:
        return _refuse(
            task,
            manifest,
            profile,
            outcome.reasons or ("MODEL_REFUSED",),
            "The coordinator declined to read the completed search.",
            at_time,
            "coordinate",
            evidence.tool_calls,
            outcome,
        )

    consumed = _consume_holdout(plan, store, task.task_id, search_id, at_time)
    verdict = build_sweep_verdict(
        {
            "verdict_id": derive_stable_id("id", f"sweep:{task.task_id}:{search_id}"),
            "task_id": task.task_id,
            "plan_id": plan.plan_id,
            "plan_hash": plan.plan_hash,
            # Both identities come from the receiver, never from the model.
            "search_id": search_id,
            "reproducibility_hash": evidence.result["reproducibility_hash"],
            "receiver_decision": evidence.result["final_decision"],
            "trials": ledger,
            "selected_parameters": _selected(evidence.result),
            "robustness_evidence": _summarise(evidence.robustness, "robustness"),
            "instability_evidence": _summarise(evidence.stability, "stability"),
            "overfit_evidence": _summarise(evidence.overfit, "overfit"),
            "economic_effect": outcome.output.get("economic_effect", ""),
            "unresolved_risk": _unresolved(outcome.output, plan, ledger),
            "holdout_consumed": consumed,
            "lifetime_trials": plan.prior_trials_consumed + ledger.attempted,
            "warnings": _lines(evidence.result.get("warnings")),
        },
    )
    logger.info(
        "Optimization coordinator bound verdict to search %s: %d of %d trials failed",
        search_id,
        ledger.failed,
        ledger.attempted,
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
            "budget_usage": _usage(
                task,
                at_time,
                outcome,
                evidence.tool_calls,
                ledger.attempted,
            ),
        },
    )


def _consume_holdout(
    plan: SweepPlan,
    store: AgenticExperimentStore | None,
    task_id: str,
    search_id: str,
    at_time: datetime,
) -> bool:
    """Claim the thesis's single holdout use when this sweep needs it.

    Args:
        plan: Pre-declared sweep plan.
        store: Injected experiment ledger.
        task_id: Owning task identity.
        search_id: Receiver-returned search identity.
        at_time: Consumption time.

    Returns:
        True when this sweep spent the thesis's holdout.
    """
    if plan.holdout_consumption != "consumes":
        return False
    if store is None:
        return True
    return store.reserve_holdout(plan.spec_hash, task_id, search_id, at_time)


def _selected(result: Mapping[str, str]) -> dict[str, str]:
    """Extract the best-ranked parameter set from the receiver's result.

    Args:
        result: Receiver-returned search result.

    Returns:
        Parameter name to selected value.
    """
    return {
        key.removeprefix("selected:"): value
        for key, value in sorted(result.items())
        if key.startswith("selected:")
    }


def _summarise(evidence: Mapping[str, str], label: str) -> str:
    """Render one deterministic evidence mapping as bounded disclosure text.

    The text is assembled from what the receiver returned, so the model has no
    opportunity to restate a score it was not given.

    Args:
        evidence: Receiver-returned evidence.
        label: Evidence label.

    Returns:
        Bounded disclosure text.
    """
    if not evidence:
        return f"{label}: no evidence returned"
    body = "; ".join(f"{key}={value}" for key, value in sorted(evidence.items()))
    return f"{label}: {body}"


def _unresolved(
    output: Mapping[str, str],
    plan: SweepPlan,
    ledger: TrialLedger,
) -> tuple[str, ...]:
    """Assemble the unresolved-risk statements for one verdict.

    Two risks are added deterministically rather than left to the model: a
    large cumulative search budget, and a search in which trials failed.

    Args:
        output: Structured model output.
        plan: Pre-declared sweep plan.
        ledger: Reconciled trial accounting.

    Returns:
        Ordered unresolved-risk statements.
    """
    stated = list(_lines(output.get("unresolved_risk")))
    lifetime = plan.prior_trials_consumed + ledger.attempted
    if lifetime >= LIFETIME_TRIAL_WARNING:
        stated.append(
            f"Cumulative search reached {lifetime} trials on this thesis; a "
            "finding from a large search is weak evidence.",
        )
    if ledger.failed:
        stated.append(
            f"{ledger.failed} of {ledger.attempted} trials failed; the completed "
            "set is not a random sample of the space.",
        )
    return tuple(stated) or ("No unresolved risk was stated.",)


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
