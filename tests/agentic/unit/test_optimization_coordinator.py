"""Unit tests for FEAT-AGT-15 Optimization Coordination.

Covers FR-AGENTIC-043 (plans declare bounded spaces, objectives, trial
budgets, early-stop policy, search method, and holdout consumption before
execution), FR-AGENTIC-044 (coordination invokes only public Optimization
operations and preserves every attempted trial and failure), and
FR-AGENTIC-045 (verdicts report robustness, instability, overfit evidence,
economic effect, and unresolved risk, not only the winning parameters).
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
    PROMPT_PATH,
)
from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
    build_trial_ledger,
    derive_plan_hash,
)
from app.agentic.agents.experimentation.optimization_coordinator.tools import (
    OVERFIT_TOOL,
    ROBUSTNESS_TOOL,
    STABILITY_TOOL,
    SWEEP_TOOL,
    get_registered_tool_names,
    verify_result_binding,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    build_sweep_mandate,
    build_sweep_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-sweep")
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
    "objective": OBJECTIVE,
    "seed": str(SEED),
}

RESULT = {
    "schema_id": "optimization.result.v1",
    "search_id": "search-2026-07-29-a",
    "reproducibility_hash": "sha256:evidence-a",
    "final_decision": "validation_needed",
    "seed": str(SEED),
    "trials_attempted": "24",
    "trials_completed": "21",
    "failed_trial:t07": "timed out after the runtime bound",
    "failed_trial:t11": "objective was not finite",
    "failed_trial:t19": "adapter raised on an empty window",
    "selected:period": "20",
    "selected:threshold": "1.0",
    "candidate:top": "period=20 threshold=1.0",
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


class StubPort:
    """Deterministic Optimization port."""

    def __init__(self, result=None, robustness=None, stability=None, overfit=None):
        self.result = RESULT if result is None else result
        self.robustness = ROBUSTNESS if robustness is None else robustness
        self.stability = STABILITY if stability is None else stability
        self.overfit = OVERFIT if overfit is None else overfit
        self.calls: list[str] = []
        self.requests: list[dict[str, str]] = []

    def run_sweep(self, request):
        self.calls.append("sweep")
        self.requests.append(dict(request))
        return self.result

    def robustness_score(self, search_id):
        self.calls.append(f"robustness:{search_id}")
        return self.robustness

    def parameter_stability(self, search_id):
        self.calls.append(f"stability:{search_id}")
        return self.stability

    def overfit_evidence(self, search_id):
        self.calls.append(f"overfit:{search_id}")
        return self.overfit


class StubRuntime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, outputs=None, status="ok", reasons=()) -> None:
        self.outputs = {} if status != "ok" else (outputs or {})
        self.status = status
        self.reasons = reasons
        self.nodes: list[str] = []
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.outputs.get(node_id) if self.status == "ok" else None,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 900,
                "latency_ms": 80,
                "cost": Decimal("0.06"),
            },
        )


def _runtime(**overrides: object):
    outputs = {
        "design_sweep": dict(DESIGN_OUTPUT),
        "coordinate_optimization": dict(VERDICT_OUTPUT),
    }
    outputs.update(overrides)
    return StubRuntime(outputs=outputs)


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
            "objective": "Declare and run a bounded search for the protocol.",
            "input_refs": ("agentic.experiment_spec:overlap",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-sweep",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _spec():
    return build_experiment_spec(
        {
            "spec_id": derive_stable_id("id", "spec-sweep"),
            "task_id": TASK_ID,
            "thesis_id": derive_stable_id("id", "thesis-sweep"),
            "hypothesis_ids": (derive_stable_id("id", "hyp-sweep"),),
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


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-15",
        "receiver_domain": name.split(".", maxsplit=1)[0],
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
    fields.update(overrides)
    return build_tool_policy(fields)


def _tool_policies(**overrides: object):
    return {name: _tool(name, **overrides) for name in get_registered_tool_names()}


def _policy(**overrides: object):
    fields: dict[str, object] = {
        "role_id": "optimization_coordinator",
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence",),
        "allowed_tools": get_registered_tool_names(),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    fields.update(overrides)
    return build_agent_policy(fields)


def _registry(**overrides: object):
    return get_role_registry(
        build_sweep_mandate(),
        (build_sweep_role_manifest(**overrides),),
        NOW,
    )


def _design(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "runtime": _runtime(),
        "profile": _profile(),
        "spec": _spec(),
        "parameter_space": dict(SPACE),
        "objective": OBJECTIVE,
        "method": "grid",
        "trial_budget": BUDGET,
        "seed": SEED,
        "at_time": NOW,
    }
    defaults.update(overrides)
    return design_sweep(**defaults)  # type: ignore[arg-type]


def _plan(**overrides: object):
    payload = _design(**overrides).payload
    assert payload is not None
    return payload


def _coordinate(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_sweep_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "port": StubPort(),
        "runtime": _runtime(),
        "profile": _profile(),
        "plan": _plan(),
        "request": dict(REQUEST),
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return coordinate_optimization(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_sweep_role_manifest(), PROMPT_PATH)
    assert "Optimization Coordinator" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("Budgets may be raised freely.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _design(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Optimization Coordinator" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-043 - the plan is declared in full before anything runs
# --------------------------------------------------------------------------


def test_the_plan_declares_every_required_element() -> None:
    plan = _plan()
    assert dict(plan.parameter_space) == SPACE
    assert plan.objective == OBJECTIVE
    assert plan.method == "grid"
    assert plan.trial_budget == BUDGET
    assert plan.seed == SEED
    assert plan.holdout_consumption == "none"
    assert plan.early_stop_policy
    assert plan.justification
    assert plan.plan_hash


def test_the_budget_comes_from_the_caller_not_the_model() -> None:
    poisoned = {**DESIGN_OUTPUT, "trial_budget": "100000", "seed": "1"}
    plan = _plan(runtime=_runtime(design_sweep=poisoned))
    assert plan.trial_budget == BUDGET
    assert plan.seed == SEED


def test_the_plan_digest_covers_the_budget() -> None:
    # Raising a budget after the fact produces a different plan, so a verdict
    # cannot be matched to a budget that was never declared.
    plan = _plan()
    widened = {**plan.model_dump(), "trial_budget": 10_000}
    assert derive_plan_hash(widened) != plan.plan_hash


def test_an_unbounded_space_is_refused_before_the_model() -> None:
    runtime = _runtime()
    result = _design(parameter_space={}, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SPACE_NOT_BOUNDED",)
    assert runtime.invocations == []


def test_a_non_positive_budget_is_refused_before_the_model() -> None:
    runtime = _runtime()
    result = _design(trial_budget=0, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("BUDGET_NOT_DECLARED",)
    assert runtime.invocations == []


def test_an_unbounded_budget_is_unrepresentable() -> None:
    plan = _plan()
    with pytest.raises(ValidationError, match="must be positive"):
        build_sweep_plan({**plan.model_dump(), "trial_budget": 0})


def test_an_empty_space_is_unrepresentable() -> None:
    plan = _plan()
    with pytest.raises(ValidationError, match="bounded parameter space"):
        build_sweep_plan({**plan.model_dump(), "parameter_space": {}})


def test_a_protocol_that_was_never_registered_is_refused() -> None:
    store = build_in_memory_experiment_store()
    runtime = _runtime()
    result = _design(store=store, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROTOCOL_NOT_REGISTERED",)
    assert runtime.invocations == []


def test_the_lifetime_budget_accumulates() -> None:
    plan = _plan(prior_trials_consumed=100)
    assert plan.lifetime_trials == 100 + BUDGET


def test_the_plan_is_frozen() -> None:
    plan = _plan()
    with pytest.raises(ValidationError):
        plan.trial_budget = 1


def test_a_model_refusal_during_design_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("SPACE_UNJUSTIFIED",))
    result = _design(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SPACE_UNJUSTIFIED",)
    assert result.payload is None


# --------------------------------------------------------------------------
# FR-AGENTIC-044 - only public operations, and every trial counts
# --------------------------------------------------------------------------


def test_every_deterministic_evidence_operation_is_called() -> None:
    port = StubPort()
    result = _coordinate(port=port)
    assert result.status == "ok"
    assert port.calls == [
        "sweep",
        f"robustness:{RESULT['search_id']}",
        f"stability:{RESULT['search_id']}",
        f"overfit:{RESULT['search_id']}",
    ]
    assert result.budget_usage.tool_calls == 4


def test_the_request_is_passed_through_unchanged() -> None:
    port = StubPort()
    _coordinate(port=port)
    assert port.requests == [dict(REQUEST)]


def test_the_package_constructs_no_optimization_contract() -> None:
    # Naming a contract in prose is fine; importing or constructing one is not.
    for module in ("agent.py", "tools.py", "schemas.py"):
        source = (PROMPT_PATH.parent / module).read_text(encoding="utf-8")
        assert "app.services.optimization" not in source, module
        assert "SearchRequest(" not in source, module
        assert "OptimizationResult(" not in source, module


def test_the_trial_ledger_accounts_for_every_attempt() -> None:
    verdict = _coordinate().payload
    assert verdict.trials.attempted == 24
    assert verdict.trials.completed == 21
    assert verdict.trials.failed == 3
    assert set(verdict.trials.failure_reasons) == {"t07", "t11", "t19"}


def test_a_ledger_that_does_not_reconcile_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="does not reconcile"):
        build_trial_ledger(
            {
                "attempted": 24,
                "completed": 21,
                "failed": 0,
                "failure_reasons": {},
                "budget": 24,
            },
        )


def test_a_failed_trial_without_a_reason_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="requires a reason"):
        build_trial_ledger(
            {
                "attempted": 24,
                "completed": 21,
                "failed": 3,
                "failure_reasons": {"t07": "timed out"},
                "budget": 24,
            },
        )


def test_a_search_exceeding_its_budget_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="against a budget"):
        build_trial_ledger(
            {
                "attempted": 40,
                "completed": 40,
                "failed": 0,
                "failure_reasons": {},
                "budget": 24,
            },
        )


def test_a_receiver_report_that_hides_failures_is_refused() -> None:
    # The receiver reports 24 attempted and 24 completed while also listing
    # failures; the arithmetic cannot be satisfied, so the run is refused.
    inconsistent = {**RESULT, "trials_completed": "24"}
    result = _coordinate(port=StubPort(result=inconsistent))
    assert result.status == "refused"
    assert result.reasons == ("TRIALS_NOT_RECONCILED",)


def test_a_search_over_budget_is_refused() -> None:
    over = {**RESULT, "trials_attempted": "40", "trials_completed": "37"}
    result = _coordinate(port=StubPort(result=over))
    assert result.status == "refused"
    assert result.reasons == ("TRIALS_NOT_RECONCILED",)
    assert "budget" in (result.detail or "")


@pytest.mark.parametrize(
    "dropped",
    ["search_id", "reproducibility_hash", "final_decision"],
)
def test_a_result_missing_evidence_is_refused(dropped) -> None:
    incomplete = {key: value for key, value in RESULT.items() if key != dropped}
    result = _coordinate(port=StubPort(result=incomplete))
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_PLAN",)
    assert dropped in (result.detail or "")


def test_a_result_from_a_different_seed_is_refused() -> None:
    other = {**RESULT, "seed": "999"}
    runtime = _runtime()
    result = _coordinate(port=StubPort(result=other), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_PLAN",)
    assert runtime.nodes == []


def test_result_binding_accepts_a_corresponding_result() -> None:
    assert verify_result_binding(SEED, dict(RESULT)) is None


def test_a_denied_tool_stops_the_run_before_the_receiver() -> None:
    port = StubPort()
    result = _coordinate(port=port, tool_policies=_tool_policies(enabled=False))
    assert result.status == "refused"
    assert result.reasons == ("OPTIMIZATION_TOOL_DENIED",)
    assert port.calls == []


def test_an_unregistered_tool_is_refused_before_the_receiver() -> None:
    policies = _tool_policies()
    del policies[ROBUSTNESS_TOOL]
    port = StubPort()
    result = _coordinate(tool_policies=policies, port=port)
    assert result.status == "refused"
    assert result.reasons == ("OPTIMIZATION_TOOL_DENIED",)
    assert ROBUSTNESS_TOOL in (result.detail or "")
    assert port.calls == []


def test_missing_robustness_evidence_is_refused() -> None:
    runtime = _runtime()
    result = _coordinate(port=StubPort(robustness={}), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("ROBUSTNESS_EVIDENCE_UNAVAILABLE",)
    assert runtime.nodes == []


def test_tool_calls_are_audited_when_a_store_is_injected() -> None:
    store = build_in_memory_memory_store()
    _coordinate(audit_store=store)
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 4


def test_registered_tool_names_are_stable() -> None:
    assert get_registered_tool_names() == (
        OVERFIT_TOOL,
        ROBUSTNESS_TOOL,
        STABILITY_TOOL,
        SWEEP_TOOL,
    )


# --------------------------------------------------------------------------
# FR-AGENTIC-045 - robustness over rank
# --------------------------------------------------------------------------


def test_the_verdict_reports_more_than_the_winning_parameters() -> None:
    verdict = _coordinate().payload
    assert dict(verdict.selected_parameters) == {"period": "20", "threshold": "1.0"}
    assert "62.5" in verdict.robustness_evidence
    assert "41.7" in verdict.instability_evidence
    assert "0.34" in verdict.overfit_evidence
    assert verdict.economic_effect
    assert verdict.unresolved_risk


def test_robustness_evidence_comes_from_the_receiver_not_the_model() -> None:
    poisoned = {**VERDICT_OUTPUT, "robustness_evidence": "robustness: score=99.9"}
    verdict = _coordinate(runtime=_runtime(coordinate_optimization=poisoned)).payload
    assert "62.5" in verdict.robustness_evidence
    assert "99.9" not in verdict.robustness_evidence


def test_the_search_identity_comes_from_the_receiver() -> None:
    poisoned = {**VERDICT_OUTPUT, "search_id": "search-that-never-ran"}
    verdict = _coordinate(runtime=_runtime(coordinate_optimization=poisoned)).payload
    assert verdict.search_id == RESULT["search_id"]
    assert verdict.reproducibility_hash == RESULT["reproducibility_hash"]


def test_the_receiver_decision_is_carried_verbatim() -> None:
    verdict = _coordinate().payload
    assert verdict.receiver_decision == "validation_needed"


@pytest.mark.parametrize(
    "field",
    [
        "robustness_evidence",
        "instability_evidence",
        "overfit_evidence",
        "economic_effect",
    ],
)
def test_a_verdict_missing_a_disclosure_is_unrepresentable(field) -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError):
        build_sweep_verdict({**verdict.model_dump(), field: ""})


def test_a_verdict_with_no_unresolved_risk_is_unrepresentable() -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError, match="is required"):
        build_sweep_verdict({**verdict.model_dump(), "unresolved_risk": ()})


def test_failed_trials_are_stated_as_unresolved_risk() -> None:
    verdict = _coordinate().payload
    assert any("3 of 24 trials failed" in item for item in verdict.unresolved_risk)


def test_a_large_lifetime_search_is_stated_as_unresolved_risk() -> None:
    verdict = _coordinate(
        plan=_plan(prior_trials_consumed=LIFETIME_TRIAL_WARNING),
    ).payload
    assert any("Cumulative search reached" in item for item in verdict.unresolved_risk)
    assert verdict.lifetime_trials == LIFETIME_TRIAL_WARNING + 24


def test_receiver_warnings_are_preserved() -> None:
    verdict = _coordinate().payload
    assert verdict.warnings == ("the objective surface is flat near the optimum",)


def test_parameters_cannot_be_selected_from_an_empty_search() -> None:
    verdict = _coordinate().payload
    empty = build_trial_ledger(
        {
            "attempted": 3,
            "completed": 0,
            "failed": 3,
            "failure_reasons": {"a": "x", "b": "y", "c": "z"},
            "budget": 24,
        },
    )
    with pytest.raises(ValidationError, match="no trial completed"):
        build_sweep_verdict(
            {**verdict.model_dump(), "trials": empty.model_dump()},
        )


def test_lifetime_trials_cannot_understate_this_search() -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError, match="cannot be smaller"):
        build_sweep_verdict({**verdict.model_dump(), "lifetime_trials": 1})


@pytest.mark.parametrize(
    "text",
    [
        "The parameter set is approved for deployment.",
        "Use a position size of two lots.",
        "Deploy to live once validated.",
    ],
)
def test_execution_language_is_rejected(text) -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError):
        build_sweep_verdict({**verdict.model_dump(), "economic_effect": text})


def test_a_model_refusal_during_coordination_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("SEARCH_UNINTERPRETABLE",))
    result = _coordinate(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SEARCH_UNINTERPRETABLE",)
    assert result.payload is None


def test_search_trials_are_reported_as_usage() -> None:
    result = _coordinate()
    assert result.budget_usage.search_trials == 24


# --------------------------------------------------------------------------
# Holdout is shared with FEAT-AGT-14
# --------------------------------------------------------------------------


def test_a_sweep_consuming_holdout_spends_the_thesis_look() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    plan = _plan(spec=spec, holdout_consumption="consumes", store=store)
    assert store.holdout_spent(spec.spec_hash) is False

    result = _coordinate(plan=plan, store=store)
    assert result.status == "ok"
    assert result.payload.holdout_consumed is True
    assert store.holdout_spent(spec.spec_hash) is True


def test_a_sweep_cannot_spend_holdout_an_experiment_already_used() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    # An experiment consumed the thesis's single look first.
    store.reserve_holdout(spec.spec_hash, TASK_ID, "run-from-experiment", NOW)

    runtime = _runtime()
    refused = _design(
        spec=spec,
        holdout_consumption="consumes",
        store=store,
        runtime=runtime,
    )
    assert refused.status == "refused"
    assert refused.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    assert runtime.invocations == []


def test_coordination_refuses_a_spent_holdout_before_the_receiver() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    plan = _plan(spec=spec, holdout_consumption="consumes", store=store)
    store.reserve_holdout(spec.spec_hash, TASK_ID, "run-from-experiment", NOW)

    port = StubPort()
    result = _coordinate(plan=plan, store=store, port=port)
    assert result.status == "refused"
    assert result.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    assert port.calls == []


def test_a_sweep_not_consuming_holdout_leaves_it_unspent() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    plan = _plan(spec=spec, store=store)
    result = _coordinate(plan=plan, store=store)
    assert result.status == "ok"
    assert result.payload.holdout_consumed is False
    assert store.holdout_spent(spec.spec_hash) is False


def test_holdout_without_a_store_is_still_reported_as_consumed() -> None:
    # With no ledger injected there is nothing to reserve against, but the
    # verdict must still say the look happened.
    plan = _plan(holdout_consumption="consumes")
    result = _coordinate(plan=plan)
    assert result.status == "ok"
    assert result.payload.holdout_consumed is True


def test_a_verdict_with_no_stated_risk_still_carries_one() -> None:
    # The model stated nothing and no trial failed, so the fallback applies
    # rather than leaving the field empty.
    clean = {
        key: value
        for key, value in RESULT.items()
        if not key.startswith("failed_trial:")
    }
    clean["trials_completed"] = "24"
    verdict = _coordinate(
        port=StubPort(result=clean),
        runtime=_runtime(coordinate_optimization={"economic_effect": "Marginal."}),
    ).payload
    assert verdict.trials.failed == 0
    assert verdict.unresolved_risk == ("No unresolved risk was stated.",)
