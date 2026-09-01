"""Integration evidence for FEAT-AGT-17 across the governed control plane.

Exercises the full path an evaluation must traverse: mandate and roster
validation, policy-registry validation, deny-by-default tool authorization,
complete evaluation coverage read from the evidence port, and a binding
acceptance verdict computed from the gates and the baseline margin.

It also exercises the critique path against real `FEAT-AGT-14`, `-15`, and
`-16` evidence, so the grounded challenges are derived from contracts those
features actually produce rather than from stand-ins.

The evaluation evidence arrives as an injected port bound to deterministic
doubles, so no grader runs and no evaluation set is authored. What is exercised
is the governance path and the acceptance arithmetic, both of which are real.
"""

from __future__ import annotations

from datetime import timedelta
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
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    build_experiment_verdict,
)
from app.agentic.agents.experimentation.optimization_coordinator.schemas import (
    build_sweep_verdict,
    build_trial_ledger,
)
from app.agentic.agents.operations.evaluation_manager import (
    critique_candidate,
    evaluate_agent,
)
from app.agentic.agents.operations.evaluation_manager.evaluator import (
    REQUIRED_CHALLENGE_KINDS,
    REQUIRED_SET_KINDS,
)
from app.agentic.agents.operations.evaluation_manager.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    EVALUATION_ROLE_ID,
    NOW,
    build_evaluation_mandate,
    build_evaluation_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-evaluation-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
SUBJECT = "technical_analyst"

SETS = {kind: f"evalset.{kind}:v3" for kind in sorted(REQUIRED_SET_KINDS)}
GRADERS_PAYLOAD = {
    **{f"grader:{kind}": f"grader.{kind}:v2" for kind in sorted(REQUIRED_SET_KINDS)},
    **{
        f"calibration:{kind}": f"calibration.{kind}:2026-07"
        for kind in sorted(REQUIRED_SET_KINDS)
    },
}
GATES = {"adversarial": "passed", "poisoning": "passed", "reliability": "passed"}
COMPARISON = {
    "candidate_score": "1.40",
    "baseline_score": "1.00",
    "uncertainty_halfwidth": "0.15",
    "cost_delta": "0.05",
    "metric": "sharpe_ratio",
}

OUTPUTS = {
    "evaluate_agent": {
        "rationale": "The margin exceeds the hurdle and no gate failed.",
        "uncertainty_statement": "One instrument over one year; no regime change.",
    },
    "critique_candidate": {
        **{
            f"challenge:{kind}": (
                f"The {kind} challenge was examined and this specific weakness "
                "remains open for a human to resolve."
            )
            for kind in sorted(REQUIRED_CHALLENGE_KINDS)
        },
        "blocking_concerns": "The counterfactual baseline has not been ruled out.",
    },
}


class _Port:
    """Deterministic evaluation-evidence port."""

    def __init__(self, gates=None, comparison=None) -> None:
        self.gates = GATES if gates is None else gates
        self.comparison = COMPARISON if comparison is None else comparison
        self.calls: list[str] = []

    def list_versioned_sets(self, role_id):
        self.calls.append("sets")
        del role_id
        return SETS

    def get_grader_calibrations(self, role_id):
        self.calls.append("graders")
        del role_id
        return GRADERS_PAYLOAD

    def get_gate_outcomes(self, role_id):
        self.calls.append("gates")
        del role_id
        return self.gates

    def get_baseline_comparison(self, role_id):
        self.calls.append("comparison")
        del role_id
        return self.comparison


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
                "tokens_used": 950,
                "latency_ms": 90,
                "cost": Decimal("0.05"),
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
            "workflow_name": "evaluate_agent",
            "workflow_version": "1.0.0",
            "objective": "Decide whether the technical analyst continues.",
            "input_refs": ("evalset.gold:v3",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-evaluation-integration",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-17",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (EVALUATION_ROLE_ID,),
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
            "role_id": EVALUATION_ROLE_ID,
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
    mandate = build_evaluation_mandate()
    registry = get_role_registry(mandate, (build_evaluation_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    return mandate, registry, tools, policies


def _evaluate(port=None, **overrides):
    """Evaluate one role through the full governed path."""
    mandate, registry, tools, policies = _control_plane()
    data = {
        "registry": registry,
        "task": _task(),
        "mandate": mandate,
        "policy": policies[EVALUATION_ROLE_ID],
        "tool_policies": tools,
        "port": port or _Port(),
        "runtime": _Runtime(),
        "profile": _profile(),
        "subject_role_id": SUBJECT,
        "subject_role_version": "1.0.0",
        "baseline_ref": "baseline.deterministic_indicators:v1",
        "sample_size": "512",
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return evaluate_agent(**data)


def _sweep_verdict(failed: int = 2):
    """Build a real FEAT-AGT-15 sweep verdict as candidate evidence."""
    return build_sweep_verdict(
        {
            "verdict_id": derive_stable_id("id", "sweep-verdict-eval"),
            "task_id": TASK_ID,
            "plan_id": "plan-a",
            "plan_hash": "sha256:plan-a",
            "search_id": "search-a",
            "reproducibility_hash": "sha256:evidence-a",
            "receiver_decision": "validation_needed",
            "trials": build_trial_ledger(
                {
                    "attempted": 24,
                    "completed": 24 - failed,
                    "failed": failed,
                    "failure_reasons": {
                        f"t{index:02d}": "the trial did not converge"
                        for index in range(failed)
                    },
                    "budget": 24,
                },
            ),
            "selected_parameters": {"period": "20"},
            "robustness_evidence": "robustness: score=62.5",
            "instability_evidence": "stability: stability_percentage=41.7",
            "overfit_evidence": "overfit: degradation=0.34",
            "economic_effect": "The gain is smaller than the modelled spread.",
            "unresolved_risk": ("The optimum sits on a narrow ridge.",),
            "holdout_consumed": False,
            "lifetime_trials": 24,
        },
    )


def _experiment_verdict(*, holdout_consumed: bool = True):
    """Build a real FEAT-AGT-14 experiment verdict as candidate evidence."""
    return build_experiment_verdict(
        {
            "verdict_id": derive_stable_id("id", "experiment-verdict-eval"),
            "task_id": TASK_ID,
            "spec_id": "spec-a",
            "spec_hash": "sha256:spec-a",
            "conclusions": {"run-a": "The refuting outcome did not occur."},
            "evidence_classes": {
                "run-a": "holdout" if holdout_consumed else "discovery"
            },
            "outcome": "not_refuted",
            "holdout_consumed": holdout_consumed,
            "limitations": ("One split cannot establish stability.",),
        },
    )


def test_evaluation_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, _ = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, EVALUATION_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())
    assert set(tools) == set(get_registered_tool_names())

    # 2. Every piece of evidence traverses the governed path.
    port = _Port()
    audit = build_in_memory_memory_store()
    result = _evaluate(port=port, audit_store=audit)

    assert result.status == "ok"
    verdict = result.payload
    assert verdict is not None
    assert port.calls == ["sets", "graders", "gates", "comparison"]
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 4

    # 3. The verdict is bound to a complete plan and a surviving margin.
    assert verdict.subject_role_id == SUBJECT
    assert verdict.comparison.margin == Decimal("0.40")
    assert verdict.comparison.hurdle == Decimal("0.20")
    assert verdict.required_action == "continue"
    assert result.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_evaluation_manager_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_evaluation_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_a_margin_swallowed_by_uncertainty_disables_the_role() -> None:
    wide = {**COMPARISON, "uncertainty_halfwidth": "0.60"}
    verdict = _evaluate(port=_Port(comparison=wide)).payload
    assert verdict is not None
    assert verdict.comparison.survives is False
    assert verdict.required_action == "disable"


def test_a_failed_gate_disables_across_the_control_plane() -> None:
    failing = {**GATES, "poisoning": "failed"}
    verdict = _evaluate(port=_Port(gates=failing)).payload
    assert verdict is not None
    assert verdict.required_action == "disable"
    # The margin was fine; the gate is what ended it.
    assert verdict.comparison.survives is True


def test_a_critique_grounds_itself_in_real_candidate_evidence() -> None:
    _, registry, _, _ = _control_plane()
    result = critique_candidate(
        registry,
        _task(),
        _Runtime(),
        _profile(),
        "agentic.sweep_verdict:search-a",
        sweep_verdict=_sweep_verdict(failed=2),
        experiment_verdict=_experiment_verdict(holdout_consumed=True),
        at_time=NOW,
    )
    assert result.status == "ok"
    memo = result.payload
    assert memo is not None
    assert set(memo.challenges) == REQUIRED_CHALLENGE_KINDS
    # Both grounded challenges came from the real contracts, not the model.
    assert "2 of 24 search trials failed" in memo.challenges["robustness"]
    assert "consumed its thesis's holdout" in memo.challenges["causality"]
    assert memo.blocking_concerns
