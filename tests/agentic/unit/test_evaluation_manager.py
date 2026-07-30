"""Unit tests for FEAT-AGT-17 Evaluation, Critique, and Economic Acceptance.

Covers FR-AGENTIC-049 (versioned gold, adversarial, poisoning, refusal,
regression, and economic-ablation sets with calibrated graders),
FR-AGENTIC-050 (critiques include leakage, causality, robustness, cost,
operational, security, and counterfactual challenges), and FR-AGENTIC-051 (a
role is disabled or retired when it fails a gate or does not beat its simpler
baseline after uncertainty and cost).
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
    retrieve_memory,
)
from app.agentic.agents.operations.evaluation_manager import (
    build_economic_acceptance_verdict,
    build_evaluation_plan,
    critique_candidate,
    evaluate_agent,
)
from app.agentic.agents.operations.evaluation_manager.agent import PROMPT_PATH
from app.agentic.agents.operations.evaluation_manager.evaluator import (
    REQUIRED_CHALLENGE_KINDS,
    REQUIRED_SET_KINDS,
    required_action,
    survives_baseline,
)
from app.agentic.agents.operations.evaluation_manager.schemas import (
    build_baseline_comparison,
)
from app.agentic.agents.operations.evaluation_manager.tools import (
    BASELINE_TOOL,
    EVALUATION_SET_TOOL,
    GATE_OUTCOME_TOOL,
    GRADER_CALIBRATION_TOOL,
    get_registered_tool_names,
    verify_comparison,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    build_evaluation_mandate,
    build_evaluation_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-evaluation")
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
GATES = {
    "adversarial": "passed",
    "poisoning": "passed",
    "refusal": "passed",
    "reliability": "passed",
}
COMPARISON = {
    "candidate_score": "1.40",
    "baseline_score": "1.00",
    "uncertainty_halfwidth": "0.15",
    "cost_delta": "0.05",
    "metric": "sharpe_ratio",
}

CHALLENGES = {
    f"challenge:{kind}": (
        f"The {kind} challenge was examined against the supplied evidence and "
        "the following specific weakness remains open for review."
    )
    for kind in sorted(REQUIRED_CHALLENGE_KINDS)
}

CRITIQUE_OUTPUT = {
    **CHALLENGES,
    "blocking_concerns": "The counterfactual baseline has not been ruled out.",
    "evidence_refs": "agentic.sweep_verdict:search-a",
}

EVALUATE_OUTPUT = {
    "rationale": (
        "The margin of 0.40 exceeds the 0.20 hurdle formed by the interval and "
        "the extra cost, and no gate failed."
    ),
    "uncertainty_statement": (
        "The evaluation covers one instrument over one year and cannot speak to "
        "regime change."
    ),
}


class StubPort:
    """Deterministic evaluation-evidence port."""

    def __init__(self, sets=None, graders=None, gates=None, comparison=None) -> None:
        self.sets = SETS if sets is None else sets
        self.graders = GRADERS_PAYLOAD if graders is None else graders
        self.gates = GATES if gates is None else gates
        self.comparison = COMPARISON if comparison is None else comparison
        self.calls: list[str] = []

    def list_versioned_sets(self, role_id):
        self.calls.append(f"sets:{role_id}")
        return self.sets

    def get_grader_calibrations(self, role_id):
        self.calls.append(f"graders:{role_id}")
        return self.graders

    def get_gate_outcomes(self, role_id):
        self.calls.append(f"gates:{role_id}")
        return self.gates

    def get_baseline_comparison(self, role_id):
        self.calls.append(f"comparison:{role_id}")
        return self.comparison


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
                "tokens_used": 1_100,
                "latency_ms": 120,
                "cost": Decimal("0.07"),
            },
        )


def _runtime(**overrides: object):
    outputs = {
        "evaluate_agent": dict(EVALUATE_OUTPUT),
        "critique_candidate": dict(CRITIQUE_OUTPUT),
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
            "workflow_name": "evaluate_agent",
            "workflow_version": "1.0.0",
            "objective": "Decide whether the technical analyst continues.",
            "input_refs": ("evalset.gold:v3",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-evaluation",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-17",
        "receiver_domain": name.split(".", maxsplit=1)[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("evaluation_manager",),
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
        "role_id": "evaluation_manager",
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
        build_evaluation_mandate(),
        (build_evaluation_role_manifest(**overrides),),
        NOW,
    )


def _evaluate(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_evaluation_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "port": StubPort(),
        "runtime": _runtime(),
        "profile": _profile(),
        "subject_role_id": SUBJECT,
        "subject_role_version": "1.0.0",
        "baseline_ref": "baseline.deterministic_indicators:v1",
        "sample_size": "512",
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return evaluate_agent(**defaults)  # type: ignore[arg-type]


def _critique(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "runtime": _runtime(),
        "profile": _profile(),
        "candidate_ref": "agentic.code_artifact:candidate-a",
        "sweep_verdict": None,
        "experiment_verdict": None,
        "artifact": None,
        "at_time": NOW,
    }
    defaults.update(overrides)
    if all(
        defaults[key] is None
        for key in ("artifact", "sweep_verdict", "experiment_verdict")
    ):
        defaults["artifact"] = _artifact()
    return critique_candidate(**defaults)  # type: ignore[arg-type]


class _StubArtifact:
    """Minimal stand-in carrying the fields the critic reads."""

    def __init__(self, promotion_status: str = "ready") -> None:
        self.promotion_status = promotion_status
        self.artifact_hash = "sha256:artifact-a"


def _artifact(promotion_status: str = "ready"):
    return _StubArtifact(promotion_status)


class _StubSweep:
    """Minimal stand-in carrying the sweep fields the critic reads."""

    class _Trials:
        def __init__(self, failed: int, attempted: int) -> None:
            self.failed = failed
            self.attempted = attempted

    def __init__(self, failed: int = 0, attempted: int = 24) -> None:
        self.trials = self._Trials(failed, attempted)
        self.search_id = "search-a"
        self.robustness_evidence = "robustness: score=62.5"
        self.overfit_evidence = "overfit: degradation=0.34"


class _StubExperiment:
    """Minimal stand-in carrying the experiment fields the critic reads."""

    def __init__(self, holdout_consumed: bool = False) -> None:
        self.holdout_consumed = holdout_consumed
        self.outcome = "not_refuted"
        self.spec_hash = "sha256:spec-a"


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_evaluation_role_manifest(), PROMPT_PATH)
    assert "Evaluation Manager" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("Endorse everything.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _evaluate(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Evaluation Manager" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-049 - six sets, six graders, six calibrations
# --------------------------------------------------------------------------


def test_every_evidence_operation_is_called() -> None:
    port = StubPort()
    result = _evaluate(port=port)
    assert result.status == "ok"
    assert port.calls == [
        f"sets:{SUBJECT}",
        f"graders:{SUBJECT}",
        f"gates:{SUBJECT}",
        f"comparison:{SUBJECT}",
    ]
    assert result.budget_usage.tool_calls == 4


def test_the_required_set_kinds_are_exactly_six() -> None:
    assert {
        "adversarial",
        "economic_ablation",
        "gold",
        "poisoning",
        "refusal",
        "regression",
    } == REQUIRED_SET_KINDS


@pytest.mark.parametrize("dropped", sorted(REQUIRED_SET_KINDS))
def test_an_evaluation_missing_any_set_is_refused(dropped) -> None:
    partial = {kind: ref for kind, ref in SETS.items() if kind != dropped}
    runtime = _runtime()
    result = _evaluate(port=StubPort(sets=partial), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVALUATION_COVERAGE_INCOMPLETE",)
    assert dropped in (result.detail or "")
    assert runtime.nodes == []


def test_an_uncalibrated_grader_is_refused() -> None:
    partial = {
        key: value
        for key, value in GRADERS_PAYLOAD.items()
        if key != "calibration:poisoning"
    }
    result = _evaluate(port=StubPort(graders=partial))
    assert result.status == "refused"
    assert result.reasons == ("EVALUATION_COVERAGE_INCOMPLETE",)
    assert "poisoning" in (result.detail or "")


def test_an_unrecognized_set_kind_is_rejected() -> None:
    extra = {**SETS, "vibes": "evalset.vibes:v1"}
    result = _evaluate(port=StubPort(sets=extra))
    assert result.status == "refused"
    assert result.reasons == ("EVALUATION_COVERAGE_INCOMPLETE",)
    assert "vibes" in (result.detail or "")


def test_an_incomplete_plan_is_unrepresentable() -> None:
    plan = _evaluate().payload
    assert plan is not None
    with pytest.raises(ValidationError, match="every required set kind"):
        build_evaluation_plan(
            {
                "plan_id": "plan-a",
                "task_id": TASK_ID,
                "subject_role_id": SUBJECT,
                "subject_role_version": "1.0.0",
                "evaluation_sets": {"gold": "evalset.gold:v3"},
                "graders": dict(SETS),
                "grader_calibrations": dict(SETS),
                "baseline_ref": "baseline:v1",
                "sample_size": "512",
            },
        )


def test_a_denied_tool_stops_the_run_before_the_receiver() -> None:
    port = StubPort()
    result = _evaluate(port=port, tool_policies=_tool_policies(enabled=False))
    assert result.status == "refused"
    assert result.reasons == ("EVALUATION_TOOL_DENIED",)
    assert port.calls == []


def test_an_unregistered_tool_is_refused_before_the_receiver() -> None:
    policies = _tool_policies()
    del policies[BASELINE_TOOL]
    port = StubPort()
    result = _evaluate(tool_policies=policies, port=port)
    assert result.status == "refused"
    assert result.reasons == ("EVALUATION_TOOL_DENIED",)
    assert BASELINE_TOOL in (result.detail or "")
    assert port.calls == []


def test_tool_calls_are_audited_when_a_store_is_injected() -> None:
    store = build_in_memory_memory_store()
    _evaluate(audit_store=store)
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 4


def test_registered_tool_names_are_stable() -> None:
    assert get_registered_tool_names() == (
        BASELINE_TOOL,
        EVALUATION_SET_TOOL,
        GATE_OUTCOME_TOOL,
        GRADER_CALIBRATION_TOOL,
    )


# --------------------------------------------------------------------------
# FR-AGENTIC-050 - all seven challenges
# --------------------------------------------------------------------------


def test_the_required_challenge_kinds_are_exactly_seven() -> None:
    assert {
        "causality",
        "cost",
        "counterfactual",
        "leakage",
        "operational",
        "robustness",
        "security",
    } == REQUIRED_CHALLENGE_KINDS


def test_a_critique_addresses_every_challenge() -> None:
    memo = _critique().payload
    assert set(memo.challenges) == REQUIRED_CHALLENGE_KINDS
    assert memo.blocking_concerns


@pytest.mark.parametrize("dropped", sorted(REQUIRED_CHALLENGE_KINDS))
def test_a_critique_missing_any_challenge_is_refused(dropped) -> None:
    partial = {
        key: value
        for key, value in CRITIQUE_OUTPUT.items()
        if key != f"challenge:{dropped}"
    }
    result = _critique(runtime=_runtime(critique_candidate=partial))
    assert result.status == "refused"
    assert result.reasons == ("CRITIQUE_COVERAGE_INCOMPLETE",)
    assert dropped in (result.detail or "")


def test_an_unrecognized_challenge_is_refused() -> None:
    extra = {**CRITIQUE_OUTPUT, "challenge:vibes": "This looks fine to me overall."}
    result = _critique(runtime=_runtime(critique_candidate=extra))
    assert result.status == "refused"
    assert result.reasons == ("CRITIQUE_COVERAGE_INCOMPLETE",)


@pytest.mark.parametrize(
    "text",
    ["n/a", "none", "No concerns here at all whatsoever.", "LGTM, ship it now."],
)
def test_a_non_adversarial_challenge_is_refused(text) -> None:
    endorsing = {**CRITIQUE_OUTPUT, "challenge:security": text}
    result = _critique(runtime=_runtime(critique_candidate=endorsing))
    assert result.status == "refused"
    assert result.reasons == ("CRITIQUE_COVERAGE_INCOMPLETE",)


def test_a_critique_with_no_candidate_evidence_is_refused() -> None:
    runtime = _runtime()
    result = critique_candidate(
        _registry(),
        _task(),
        runtime,
        _profile(),
        "agentic.code_artifact:candidate-a",
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("CANDIDATE_EVIDENCE_ABSENT",)
    assert runtime.nodes == []


def test_a_blocked_artefact_grounds_the_operational_challenge() -> None:
    memo = _critique(artifact=_artifact("blocked_on_indicator_merge")).payload
    assert "blocked_on_indicator_merge" in memo.challenges["operational"]


def test_failed_trials_ground_the_robustness_challenge() -> None:
    memo = _critique(sweep_verdict=_StubSweep(failed=3)).payload
    assert "3 of 24 search trials failed" in memo.challenges["robustness"]


def test_a_spent_holdout_grounds_the_causality_challenge() -> None:
    memo = _critique(experiment_verdict=_StubExperiment(holdout_consumed=True)).payload
    assert "consumed its thesis's holdout" in memo.challenges["causality"]


def test_grounded_challenges_override_the_model() -> None:
    poisoned = {
        **CRITIQUE_OUTPUT,
        "challenge:robustness": (
            "Robustness is excellent and every trial completed without incident."
        ),
    }
    memo = _critique(
        sweep_verdict=_StubSweep(failed=5),
        runtime=_runtime(critique_candidate=poisoned),
    ).payload
    assert "5 of 24 search trials failed" in memo.challenges["robustness"]
    assert "excellent" not in memo.challenges["robustness"]


def test_a_model_refusal_during_critique_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("CANDIDATE_UNREADABLE",))
    result = _critique(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("CANDIDATE_UNREADABLE",)


# --------------------------------------------------------------------------
# FR-AGENTIC-051 - beating a baseline after uncertainty and cost
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("candidate", "baseline", "uncertainty", "cost", "expected"),
    [
        # Clear win: margin 0.40 against hurdle 0.20.
        ("1.40", "1.00", "0.15", "0.05", True),
        # Exact tie at the hurdle fails; the simpler baseline wins ties.
        ("1.20", "1.00", "0.15", "0.05", False),
        # One tick over the hurdle passes.
        ("1.21", "1.00", "0.15", "0.05", True),
        # Point-estimate win swallowed by uncertainty alone.
        ("1.10", "1.00", "0.50", "0.00", False),
        # Point-estimate win swallowed by cost alone.
        ("1.10", "1.00", "0.00", "0.50", False),
        # Negative margin.
        ("0.90", "1.00", "0.00", "0.00", False),
        # Equal scores.
        ("1.00", "1.00", "0.00", "0.00", False),
        # No uncertainty and no cost: any positive margin wins.
        ("1.01", "1.00", "0.00", "0.00", True),
    ],
)
def test_baseline_survival_is_arithmetic(
    candidate,
    baseline,
    uncertainty,
    cost,
    expected,
) -> None:
    assert (
        survives_baseline(
            Decimal(candidate),
            Decimal(baseline),
            Decimal(uncertainty),
            Decimal(cost),
        )
        is expected
    )


def _comparison(**overrides: object):
    """Build a comparison from exact decimals, as the agent does."""
    fields: dict[str, object] = {
        key: (Decimal(value) if key != "metric" else value)
        for key, value in COMPARISON.items()
    }
    fields.update(overrides)
    return build_baseline_comparison(fields)


def test_the_comparison_exposes_its_margin_and_hurdle() -> None:
    comparison = _comparison()
    assert comparison.margin == Decimal("0.40")
    assert comparison.hurdle == Decimal("0.20")
    assert comparison.survives is True


def test_negative_uncertainty_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="must not be negative"):
        _comparison(uncertainty_halfwidth=Decimal("-0.1"))


def test_a_surviving_candidate_continues() -> None:
    verdict = _evaluate().payload
    assert verdict.required_action == "continue"
    assert verdict.comparison.survives is True


def test_a_candidate_that_does_not_beat_its_baseline_is_disabled() -> None:
    narrow = {**COMPARISON, "candidate_score": "1.10", "uncertainty_halfwidth": "0.50"}
    verdict = _evaluate(port=StubPort(comparison=narrow)).payload
    assert verdict.required_action == "disable"


@pytest.mark.parametrize("gate", ["adversarial", "poisoning", "refusal", "reliability"])
def test_a_failed_gate_disables_regardless_of_margin(gate) -> None:
    failing = {**GATES, gate: "failed"}
    verdict = _evaluate(port=StubPort(gates=failing)).payload
    assert verdict.required_action == "disable"
    assert verdict.comparison.survives is True


def test_a_gate_that_was_not_run_counts_as_a_failure() -> None:
    unrun = {**GATES, "poisoning": "not_run"}
    verdict = _evaluate(port=StubPort(gates=unrun)).payload
    assert verdict.required_action == "disable"


def test_a_repeat_failure_retires_rather_than_disabling() -> None:
    failing = {**GATES, "reliability": "failed"}
    verdict = _evaluate(port=StubPort(gates=failing), consecutive_failures=1).payload
    assert verdict.required_action == "retire"


def test_the_model_cannot_change_the_required_action() -> None:
    poisoned = {**EVALUATE_OUTPUT, "required_action": "continue"}
    failing = {**GATES, "adversarial": "failed"}
    verdict = _evaluate(
        port=StubPort(gates=failing),
        runtime=_runtime(evaluate_agent=poisoned),
    ).payload
    assert verdict.required_action == "disable"


def test_a_verdict_disagreeing_with_its_evidence_is_unrepresentable() -> None:
    verdict = _evaluate().payload
    with pytest.raises(ValidationError, match="disagrees with the evidence"):
        build_economic_acceptance_verdict(
            {**verdict.model_dump(), "required_action": "retire"},
        )


def test_a_failed_role_cannot_be_recorded_as_continuing() -> None:
    failing = {**GATES, "poisoning": "failed"}
    verdict = _evaluate(port=StubPort(gates=failing)).payload
    with pytest.raises(ValidationError, match="disagrees with the evidence"):
        build_economic_acceptance_verdict(
            {**verdict.model_dump(), "required_action": "continue"},
        )


@pytest.mark.parametrize(
    ("failed", "survives", "prior", "expected"),
    [
        ((), True, 0, "continue"),
        ((), False, 0, "disable"),
        (("poisoning",), True, 0, "disable"),
        ((), False, 1, "retire"),
        (("poisoning",), True, 2, "retire"),
    ],
)
def test_required_action_is_deterministic(failed, survives, prior, expected) -> None:
    assert required_action(failed, survives, prior) == expected


@pytest.mark.parametrize("dropped", sorted(COMPARISON))
def test_an_incomplete_comparison_is_refused(dropped) -> None:
    partial = {key: value for key, value in COMPARISON.items() if key != dropped}
    runtime = _runtime()
    result = _evaluate(port=StubPort(comparison=partial), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("BASELINE_COMPARISON_UNAVAILABLE",)
    assert runtime.nodes == []


def test_an_unreadable_comparison_is_refused() -> None:
    unreadable = {**COMPARISON, "candidate_score": "not-a-number"}
    result = _evaluate(port=StubPort(comparison=unreadable))
    assert result.status == "refused"
    assert result.reasons == ("BASELINE_COMPARISON_UNAVAILABLE",)


def test_comparison_verification_accepts_a_complete_comparison() -> None:
    assert verify_comparison(dict(COMPARISON)) is None


def test_the_verdict_records_the_gates_and_the_plan() -> None:
    verdict = _evaluate().payload
    assert dict(verdict.gate_outcomes) == GATES
    assert verdict.subject_role_id == SUBJECT
    assert verdict.plan_hash
    assert verdict.rationale
    assert verdict.uncertainty_statement


def test_a_verdict_with_no_gates_is_unrepresentable() -> None:
    verdict = _evaluate().payload
    with pytest.raises(ValidationError, match="must record the gates"):
        build_economic_acceptance_verdict(
            {**verdict.model_dump(), "gate_outcomes": {}},
        )


def test_a_model_refusal_during_evaluation_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("EVIDENCE_UNREADABLE",))
    result = _evaluate(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_UNREADABLE",)


@pytest.mark.parametrize(
    "text",
    ["The role is approved to continue.", "Deploy to live immediately."],
)
def test_execution_language_is_rejected(text) -> None:
    verdict = _evaluate().payload
    with pytest.raises(ValidationError):
        build_economic_acceptance_verdict(
            {**verdict.model_dump(), "rationale": text},
        )


def test_the_decision_is_computed_before_the_model_is_invoked() -> None:
    runtime = _runtime()
    _evaluate(runtime=runtime)
    invocation = runtime.invocations[0]
    assert invocation.trusted_context["required_action"] == "continue"
    assert invocation.trusted_context["margin"] == "0.40"
    assert invocation.trusted_context["hurdle"] == "0.20"


def test_a_critique_memo_is_frozen() -> None:
    memo = _critique().payload
    with pytest.raises(ValidationError):
        memo.candidate_ref = "other"
