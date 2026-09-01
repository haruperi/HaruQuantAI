"""Integration evidence for FEAT-AGT-15 across the governed control plane.

Exercises `WF-AGT-004` steps 1 through 5: a bounded plan declared from an
approved protocol, a receiver-owned search through the governed tool path,
every trial and failure preserved, robustness and overfit evidence read rather
than ranked, and a robustness-focused verdict bound to the returned search.

It also covers the cross-feature guarantee: holdout is one thesis-wide look,
shared with `FEAT-AGT-14`, so an experiment and a sweep cannot each spend it.

`WF-AGT-004` itself stays `Missing` until `build_sweep_plan` and
`build_sweep_verdict` are exposed on the Agentic public root, which the
registry assigns to `FEAT-AGT-22`.

The Optimization receiver arrives as an injected port bound to deterministic
doubles, so no search executes. What is exercised is the governance path,
which is real.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    resolve_role_manifest,
    retrieve_memory,
    validate_firm_mandate,
    validate_policy_registry,
)
from app.agentic.agents.experimentation.experiment_designer.repository import (
    build_in_memory_experiment_store,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    SplitWindow,
    build_experiment_spec,
)
from app.agentic.agents.experimentation.optimization_coordinator import (
    coordinate_optimization,
    design_sweep,
)
from app.agentic.agents.experimentation.optimization_coordinator.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    NOW,
    SWEEP_ROLE_ID,
    build_sweep_mandate,
    build_sweep_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-sweep-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

SPACE = {"period": "10,20,30"}
OBJECTIVE = "sharpe_ratio"
BUDGET = 12
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
    "search_id": "search-integration-a",
    "reproducibility_hash": "sha256:evidence-integration",
    "final_decision": "research_only",
    "seed": str(SEED),
    "trials_attempted": "12",
    "trials_completed": "10",
    "failed_trial:t04": "objective was not finite",
    "failed_trial:t09": "timed out after the runtime bound",
    "selected:period": "20",
    "warnings": "two trials failed on the same window",
}

ROBUSTNESS = {"score": "50.0", "checks_applied": "6"}
STABILITY = {"stability_percentage": "33.3"}
OVERFIT = {"degradation": "0.41", "flagged": "true"}

OUTPUTS = {
    "design_sweep": {
        "early_stop_policy": "Stop after 4 consecutive trials below baseline.",
        "justification": "Three periods bound the space to 12 interpretable trials.",
    },
    "coordinate_optimization": {
        "economic_effect": "The gain does not survive the modelled spread.",
        "unresolved_risk": "The optimum sits on a narrow ridge.",
    },
}


class _Port:
    """Deterministic Optimization port."""

    def __init__(self, result: dict[str, str] | None = None) -> None:
        self.result = RESULT if result is None else result
        self.calls: list[str] = []

    def run_sweep(self, request):
        self.calls.append("sweep")
        del request
        return self.result

    def robustness_score(self, search_id):
        self.calls.append(f"robustness:{search_id}")
        return ROBUSTNESS

    def parameter_stability(self, search_id):
        self.calls.append(f"stability:{search_id}")
        return STABILITY

    def overfit_evidence(self, search_id):
        self.calls.append(f"overfit:{search_id}")
        return OVERFIT


class _Runtime:
    """Deterministic runtime satisfying the AdkRuntime port."""

    def __init__(self) -> None:
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": dict(OUTPUTS[node_id]),
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 700,
                "latency_ms": 60,
                "cost": Decimal("0.04"),
            },
        )


def _profile():
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


def _task():
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
            "objective": "Declare and run a bounded search.",
            "input_refs": ("agentic.experiment_spec:overlap",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-sweep-integration",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _spec():
    return build_experiment_spec(
        {
            "spec_id": derive_stable_id("id", "spec-sweep-integration"),
            "task_id": TASK_ID,
            "thesis_id": derive_stable_id("id", "thesis-sweep-integration"),
            "hypothesis_ids": (derive_stable_id("id", "hyp-sweep-integration"),),
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


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-15",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (SWEEP_ROLE_ID,),
            "scope": dict(SCOPE),
            "idempotent": True,
            "requires_approval": False,
            "max_input_bytes": 8_192,
            "max_output_bytes": 1_048_576,
            "timeout_seconds": 30,
            "max_calls_per_task": 8,
            "enabled": True,
        },
    )


def _policy():
    return build_agent_policy(
        {
            "role_id": SWEEP_ROLE_ID,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def _control_plane():
    """Validate the mandate, roster, and policy registry for this role."""
    mandate = build_sweep_mandate()
    registry = get_role_registry(mandate, (build_sweep_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    return mandate, registry, tools, policies


def _design(registry, spec, store, **overrides):
    """Declare one bounded sweep through the public API."""
    data = {
        "registry": registry,
        "task": _task(),
        "runtime": _Runtime(),
        "profile": _profile(),
        "spec": spec,
        "parameter_space": dict(SPACE),
        "objective": OBJECTIVE,
        "method": "grid",
        "trial_budget": BUDGET,
        "seed": SEED,
        "store": store,
        "at_time": NOW,
    }
    data.update(overrides)
    return design_sweep(**data)


def test_bounded_optimization_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, policies = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, SWEEP_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())
    assert set(tools) == set(get_registered_tool_names())

    # 2. The plan is declared in full against a pre-registered protocol.
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    designed = _design(registry, spec, store)
    assert designed.status == "ok"
    plan = designed.payload
    assert plan is not None
    assert plan.trial_budget == BUDGET

    # 3. The search and every evidence operation traverse the governed path.
    port, runtime = _Port(), _Runtime()
    audit = build_in_memory_memory_store()
    coordinated = coordinate_optimization(
        registry,
        _task(),
        mandate,
        policies[SWEEP_ROLE_ID],
        tools,
        port,
        runtime,
        _profile(),
        plan,
        dict(REQUEST),
        store=store,
        request_scope=dict(SCOPE),
        audit_store=audit,
        at_time=NOW,
    )

    assert coordinated.status == "ok"
    verdict = coordinated.payload
    assert verdict is not None
    assert verdict.plan_hash == plan.plan_hash
    assert verdict.search_id == RESULT["search_id"]
    assert verdict.receiver_decision == "research_only"

    # 4. Every trial is accounted for, and the failures are preserved.
    assert verdict.trials.attempted == 12
    assert verdict.trials.completed == 10
    assert verdict.trials.failed == 2
    assert set(verdict.trials.failure_reasons) == {"t04", "t09"}
    assert any("2 of 12 trials failed" in item for item in verdict.unresolved_risk)

    # 5. Robustness evidence came from the receiver, not the rank.
    assert "50.0" in verdict.robustness_evidence
    assert "33.3" in verdict.instability_evidence
    assert "0.41" in verdict.overfit_evidence
    assert port.calls == [
        "sweep",
        f"robustness:{RESULT['search_id']}",
        f"stability:{RESULT['search_id']}",
        f"overfit:{RESULT['search_id']}",
    ]
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 4
    assert coordinated.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_optimization_coordinator_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_sweep_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_holdout_is_one_look_shared_with_the_experiment_designer() -> None:
    # An experiment spends the thesis's single look; the sweep cannot have it.
    mandate, registry, tools, policies = _control_plane()
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    assert store.reserve_holdout(spec.spec_hash, TASK_ID, "run-experiment", NOW) is True

    runtime = _Runtime()
    refused = _design(
        registry,
        spec,
        store,
        holdout_consumption="consumes",
        runtime=runtime,
    )
    assert refused.status == "refused"
    assert refused.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    assert runtime.nodes == []

    # And coordination refuses too, before the receiver is reached.
    plan = _design(registry, spec, store).payload
    assert plan is not None
    consuming = plan.model_copy(update={"holdout_consumption": "consumes"})
    port = _Port()
    coordinated = coordinate_optimization(
        registry,
        _task(),
        mandate,
        policies[SWEEP_ROLE_ID],
        tools,
        port,
        _Runtime(),
        _profile(),
        consuming,
        dict(REQUEST),
        store=store,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert coordinated.status == "refused"
    assert coordinated.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    assert port.calls == []


def test_a_search_that_hides_failures_never_reaches_the_verdict_model() -> None:
    mandate, registry, tools, policies = _control_plane()
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    plan = _design(registry, spec, store).payload
    assert plan is not None

    # The receiver claims every trial completed while still listing failures.
    hidden = {**RESULT, "trials_completed": "12"}
    runtime = _Runtime()
    result = coordinate_optimization(
        registry,
        _task(),
        mandate,
        policies[SWEEP_ROLE_ID],
        tools,
        _Port(result=hidden),
        runtime,
        _profile(),
        plan,
        dict(REQUEST),
        store=store,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("TRIALS_NOT_RECONCILED",)
    assert runtime.nodes == []
