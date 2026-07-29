"""Executable FEAT-AGT-15 Optimization Coordinator usage example.

Demonstrates the two registered public operations through the documented API.
The Optimization receiver arrives as an injected port bound to deterministic
doubles: no search executes, no network call occurs, and Agentic holds no
credential.

The point of the demonstration is where authority sits — the plan is declared
and hashed before any trial runs, the trial accounting must reconcile, and
robustness, stability, and overfit come from deterministic receiver operations
rather than from the model or from rank.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    retrieve_memory,
)
from app.agentic.agents.experimentation.experiment_designer.repository import (
    build_in_memory_experiment_store,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    SplitWindow,
    build_experiment_spec,
)
from app.agentic.agents.experimentation.optimization_coordinator import (
    build_sweep_plan,
    build_sweep_verdict,
    coordinate_optimization,
    design_sweep,
)
from app.agentic.agents.experimentation.optimization_coordinator.agent import (
    LIFETIME_TRIAL_WARNING,
)
from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
    build_trial_ledger,
    derive_plan_hash,
)
from app.agentic.agents.experimentation.optimization_coordinator.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from agentic.fixtures import (
    build_sweep_mandate,
    build_sweep_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-sweep-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

SPACE = {"period": "10,20,30", "threshold": "0.5,1.0"}
OBJECTIVE = "sharpe_ratio"
BUDGET = 24
SEED = 20260729

SPLITS = (
    SplitWindow.model_validate(
        {
            "label": "discovery",
            "start": datetime(2022, 1, 1, tzinfo=UTC),
            "end": datetime(2023, 1, 1, tzinfo=UTC),
        },
    ),
    SplitWindow.model_validate(
        {
            "label": "validation",
            "start": datetime(2023, 2, 1, tzinfo=UTC),
            "end": datetime(2024, 1, 1, tzinfo=UTC),
        },
    ),
    SplitWindow.model_validate(
        {
            "label": "holdout",
            "start": datetime(2024, 3, 1, tzinfo=UTC),
            "end": datetime(2025, 1, 1, tzinfo=UTC),
        },
    ),
)

REQUEST = {
    "schema_id": "optimization.search_request.v1",
    "method": "grid",
    "seed": str(SEED),
}

RESULT = {
    "schema_id": "optimization.result.v1",
    "search_id": "search-usage-a",
    "reproducibility_hash": "sha256:evidence-usage",
    "final_decision": "validation_needed",
    "seed": str(SEED),
    "trials_attempted": "24",
    "trials_completed": "21",
    "failed_trial:t07": "timed out after the runtime bound",
    "failed_trial:t11": "objective was not finite",
    "failed_trial:t19": "adapter raised on an empty window",
    "selected:period": "20",
    "selected:threshold": "1.0",
    "warnings": "the objective surface is flat near the optimum",
}

ROBUSTNESS = {"score": "62.5", "checks_applied": "8"}
STABILITY = {"stability_percentage": "41.7", "varying_parameters": "threshold"}
OVERFIT = {"degradation": "0.34", "threshold": "0.20", "flagged": "true"}

DESIGN_OUTPUT = {
    "early_stop_policy": "Stop when 8 consecutive trials fail to beat the baseline.",
    "justification": (
        "Three periods and two thresholds bound the space to 24 trials, which is "
        "small enough that a survivor is still interpretable."
    ),
}

VERDICT_OUTPUT = {
    "economic_effect": (
        "The improvement is smaller than the modelled spread on this instrument."
    ),
    "unresolved_risk": (
        "The objective surface is flat, so the optimum is not well identified."
    ),
}


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicPort:
    """Deterministic Optimization port."""

    def __init__(self, result=None):
        self.result = RESULT if result is None else result
        self.calls = []
        self.requests = []

    def run_sweep(self, request):
        """Execute one receiver-owned bounded search."""
        self.calls.append("sweep")
        self.requests.append(dict(request))
        return self.result

    def robustness_score(self, search_id):
        """Return the deterministic robustness score."""
        self.calls.append(f"robustness:{search_id}")
        return ROBUSTNESS

    def parameter_stability(self, search_id):
        """Return the deterministic parameter stability."""
        self.calls.append(f"stability:{search_id}")
        return STABILITY

    def overfit_evidence(self, search_id):
        """Return the deterministic overfit evidence."""
        self.calls.append(f"overfit:{search_id}")
        return OVERFIT


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, outputs=None, status="ok", reasons=()):
        self.outputs = {} if status != "ok" else (outputs or {})
        self.status = status
        self.reasons = reasons
        self.nodes = []

    def execute_node(self, node_id, profile, invocation):
        """Return a reproducible outcome for one node execution."""
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.outputs.get(node_id) if self.status == "ok" else None,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 880,
                "latency_ms": 75,
                "cost": Decimal("0.05"),
            },
        )


def make_runtime(**overrides):
    """Build the deterministic runtime with per-node declared output."""
    outputs = {
        "design_sweep": dict(DESIGN_OUTPUT),
        "coordinate_optimization": dict(VERDICT_OUTPUT),
    }
    outputs.update(overrides)
    return DeterministicRuntime(outputs=outputs)


def make_profile():
    """Build the evaluated model profile."""
    return build_model_profile(
        {
            "profile_id": "profile-market-analysis-a",
            "version": "1.0.0",
            "provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "region": "europe-west4",
            "credential_ref": "vault://agentic/gemini",
            "structured_output_mode": "json_schema",
            "max_context_tokens": 120_000,
            "max_output_tokens": 8_000,
            "max_latency_ms": 30_000,
            "max_cost_per_call": Decimal("0.50"),
            "retention_policy": "zero-retention",
            "training_use_permitted": False,
            "fallback_profile_id": None,
            "evaluation_state": "evaluated",
            "enabled": True,
        },
    )


def make_task():
    """Build the bounded governed sweep task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "design_sweep",
            "workflow_version": "1.0.0",
            "objective": "Declare and run a bounded search for the protocol.",
            "input_refs": ("agentic.experiment_spec:overlap",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-sweep-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def make_spec():
    """Build the pre-registered experiment protocol this sweep serves."""
    return build_experiment_spec(
        {
            "spec_id": derive_stable_id("id", "spec-sweep-usage"),
            "task_id": TASK_ID,
            "thesis_id": derive_stable_id("id", "thesis-sweep-usage"),
            "hypothesis_ids": (derive_stable_id("id", "hyp-sweep-usage"),),
            "input_refs": ("data.market_dataset:EURUSD-H1@v3",),
            "splits": SPLITS,
            "embargo_seconds": 7 * 24 * 3600,
            "cost_model_ref": "simulator.execution_profile:retail_fx_v1",
            "seed": SEED,
            "baseline_ref": "analytics.baseline:buy_and_hold_v1",
            "metrics": ("sharpe_ratio",),
            "stop_rules": ("Stop if discovery yields no effect above baseline.",),
            "falsification_outcome": "The holdout Sharpe is at or below baseline.",
            "leakage_controls": ("Warm-up is contained inside each split.",),
        },
    )


def make_tool(name, **overrides):
    """Build one registered read-evidence tool policy."""
    data = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-15",
        "receiver_domain": name.split(".")[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("optimization_coordinator",),
        "scope": dict(SCOPE),
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 8,
        "enabled": True,
    }
    data.update(overrides)
    return build_tool_policy(data)


def make_tool_policies(**overrides):
    """Build every registered tool policy for this role."""
    return {name: make_tool(name, **overrides) for name in get_registered_tool_names()}


def make_policy():
    """Build the optimization-coordinator agent policy."""
    return build_agent_policy(
        {
            "role_id": "optimization_coordinator",
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def make_registry():
    """Build the validated role registry for this role."""
    return get_role_registry(
        build_sweep_mandate(),
        (build_sweep_role_manifest(),),
        NOW,
    )


def design(**overrides):
    """Declare one bounded sweep with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "spec": make_spec(),
        "parameter_space": dict(SPACE),
        "objective": OBJECTIVE,
        "method": "grid",
        "trial_budget": BUDGET,
        "seed": SEED,
        "at_time": NOW,
    }
    data.update(overrides)
    return design_sweep(**data)


def coordinate(**overrides):
    """Coordinate one search with the deterministic doubles."""
    data = {
        "registry": make_registry(),
        "task": make_task(),
        "mandate": build_sweep_mandate(),
        "policy": make_policy(),
        "tool_policies": make_tool_policies(),
        "port": DeterministicPort(),
        "runtime": make_runtime(),
        "profile": make_profile(),
        "plan": design().payload,
        "request": dict(REQUEST),
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return coordinate_optimization(**data)


def fr_agentic_043() -> None:
    """FR-AGENTIC-043: The plan is declared in full before anything runs."""
    _header(
        "FR-AGENTIC-043: Sweep plans declare bounded spaces, objectives, trial "
        "budgets, early-stop policy, search method, and holdout consumption "
        "before execution."
    )

    plan = design().payload
    print(f"  plan digest:      {plan.plan_hash}")
    print(f"  parameter space:  {dict(plan.parameter_space)}")
    print(f"  objective:        {plan.objective}")
    print(f"  method:           {plan.method}")
    print(f"  trial budget:     {plan.trial_budget}")
    print(f"  seed:             {plan.seed}")
    print(f"  holdout:          {plan.holdout_consumption}")
    print(f"  early stop:       {plan.early_stop_policy}")
    print(f"  justification:    {plan.justification}")

    poisoned = {**DESIGN_OUTPUT, "trial_budget": "100000", "seed": "1"}
    forged = design(runtime=make_runtime(design_sweep=poisoned)).payload
    print(f"  model-supplied budget ignored: {forged.trial_budget}")
    print(f"  model-supplied seed ignored:   {forged.seed}")

    widened = {**plan.model_dump(), "trial_budget": 10_000}
    print(
        "  widening the budget changes the digest: "
        f"{derive_plan_hash(widened) != plan.plan_hash}"
    )

    for label, override in (
        ("an unbounded space", {"parameter_space": {}}),
        ("a zero budget", {"trial_budget": 0}),
    ):
        runtime = make_runtime()
        refused = design(runtime=runtime, **override)
        print(
            f"  {label:<20} -> {refused.status} ({refused.reasons[0]}), "
            f"model calls: {len(runtime.nodes)}"
        )

    try:
        build_sweep_plan({**plan.model_dump(), "trial_budget": 0})
        outcome = "ERROR: an unbounded budget was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "An unbounded budget is unrepresentable"
    print(f"  {outcome}")


def fr_agentic_044() -> None:
    """FR-AGENTIC-044: Public operations only, and every trial counts."""
    _header(
        "FR-AGENTIC-044: Optimization coordination invokes only public "
        "Optimization operations and preserves every attempted trial and "
        "failure."
    )

    port = DeterministicPort()
    audit = build_in_memory_memory_store()
    result = coordinate(port=port, audit_store=audit)
    verdict = result.payload
    print(f"  governed tool calls: {port.calls}")
    print(
        f"  audited tool calls:  {len(retrieve_memory(audit, 'audit', TASK_ID, NOW))}"
    )
    print(f"  request unchanged:   {port.requests[0] == dict(REQUEST)}")
    print(f"  trials attempted:    {verdict.trials.attempted}")
    print(f"  trials completed:    {verdict.trials.completed}")
    print(f"  trials failed:       {verdict.trials.failed}")
    for trial, reason in verdict.trials.failure_reasons.items():
        print(f"    [{trial}] {reason}")

    hidden = {**RESULT, "trials_completed": "24"}
    refused = coordinate(port=DeterministicPort(result=hidden))
    print(f"  hidden failures   -> {refused.status} ({refused.reasons[0]})")
    print(f"  detail: {refused.detail}")

    other_seed = {**RESULT, "seed": "999"}
    runtime = make_runtime()
    mismatched = coordinate(port=DeterministicPort(result=other_seed), runtime=runtime)
    print(f"  wrong seed        -> {mismatched.status} ({mismatched.reasons[0]})")
    print(f"  verdict model calls: {len(runtime.nodes)}")

    denied_port = DeterministicPort()
    denied = coordinate(
        port=denied_port,
        tool_policies=make_tool_policies(enabled=False),
    )
    print(f"  disabled tool     -> {denied.status} ({denied.reasons[0]})")
    print(f"  receiver reached: {len(denied_port.calls)} times")

    for label, fields in (
        (
            "attempted != completed + failed",
            {
                "attempted": 24,
                "completed": 21,
                "failed": 0,
                "failure_reasons": {},
                "budget": 24,
            },
        ),
        (
            "a failure with no reason",
            {
                "attempted": 24,
                "completed": 21,
                "failed": 3,
                "failure_reasons": {"t07": "timed out"},
                "budget": 24,
            },
        ),
        (
            "a search over budget",
            {
                "attempted": 40,
                "completed": 40,
                "failed": 0,
                "failure_reasons": {},
                "budget": 24,
            },
        ),
    ):
        try:
            build_trial_ledger(fields)
            outcome = f"ERROR: {label} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"{label} is unrepresentable"
        print(f"  {outcome}")


def fr_agentic_045() -> None:
    """FR-AGENTIC-045: Robustness over rank."""
    _header(
        "FR-AGENTIC-045: Sweep verdicts report robustness, instability, "
        "overfit evidence, economic effect, and unresolved risk, not only the "
        "winning parameters."
    )

    verdict = coordinate().payload
    print(f"  receiver decision:  {verdict.receiver_decision}")
    print(f"  search identity:    {verdict.search_id}")
    print(f"  reproducibility:    {verdict.reproducibility_hash}")
    print(f"  robustness:         {verdict.robustness_evidence}")
    print(f"  instability:        {verdict.instability_evidence}")
    print(f"  overfit:            {verdict.overfit_evidence}")
    print(f"  economic effect:    {verdict.economic_effect}")
    print(f"  selected (last):    {dict(verdict.selected_parameters)}")
    print(f"  preserved warnings: {verdict.warnings}")
    for risk in verdict.unresolved_risk:
        print(f"  unresolved risk:    {risk}")

    poisoned = {**VERDICT_OUTPUT, "robustness_evidence": "robustness: score=99.9"}
    forged = coordinate(runtime=make_runtime(coordinate_optimization=poisoned)).payload
    print(f"  model-supplied robustness ignored: {forged.robustness_evidence}")

    large = coordinate(
        plan=design(prior_trials_consumed=LIFETIME_TRIAL_WARNING).payload,
    ).payload
    print(f"  lifetime trials:    {large.lifetime_trials}")
    print(
        f"  cumulative warning: "
        f"{any('Cumulative search' in r for r in large.unresolved_risk)}"
    )

    for field in ("robustness_evidence", "economic_effect"):
        try:
            build_sweep_verdict({**verdict.model_dump(), field: ""})
            outcome = f"ERROR: a verdict with no {field} was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"A verdict with no {field} is unrepresentable"
        print(f"  {outcome}")

    try:
        build_sweep_verdict({**verdict.model_dump(), "unresolved_risk": ()})
        outcome = "ERROR: a verdict with no unresolved risk was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "A verdict with no unresolved risk is unrepresentable"
    print(f"  {outcome}")

    print("\n  Holdout is one look, shared with FEAT-AGT-14:")
    store = build_in_memory_experiment_store()
    spec = make_spec()
    store.save_spec(spec)
    store.reserve_holdout(spec.spec_hash, TASK_ID, "run-from-experiment", NOW)
    runtime = make_runtime()
    refused = design(
        spec=spec,
        holdout_consumption="consumes",
        store=store,
        runtime=runtime,
    )
    print(
        f"    an experiment already spent it -> {refused.status} "
        f"({refused.reasons[0]}), model calls: {len(runtime.nodes)}"
    )


def main() -> None:
    """Run every functional-requirement demonstration for the coordinator."""
    fr_agentic_043()
    fr_agentic_044()
    fr_agentic_045()


if __name__ == "__main__":
    main()
