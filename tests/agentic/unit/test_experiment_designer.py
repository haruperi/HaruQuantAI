"""Unit tests for FEAT-AGT-14 Experiment and Simulation Coordination.

Covers FR-AGENTIC-040 (protocols specify immutable inputs, time splits,
embargo, costs, seeds, baselines, metrics, stop rules, and falsification
outcomes), FR-AGENTIC-041 (coordination uses only the public Simulation
request and result contracts and never invents or alters a result), and
FR-AGENTIC-042 (verdicts bind every conclusion to run identifiers and
distinguish discovery, validation, holdout, and null-data evidence).
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
from app.agentic.agents.experimentation.experiment_designer import (
    ExperimentSpec,
    build_experiment_spec,
    build_experiment_verdict,
    coordinate_simulation,
    design_experiment,
)
from app.agentic.agents.experimentation.experiment_designer.agent import PROMPT_PATH
from app.agentic.agents.experimentation.experiment_designer.repository import (
    build_in_memory_experiment_store,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import (
    SplitWindow,
    derive_spec_hash,
    validate_split_windows,
)
from app.agentic.agents.experimentation.experiment_designer.tools import (
    BACKTEST_TOOL,
    RUN_LOOKUP_TOOL,
    get_registered_tool_names,
    verify_result_binding,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst import (
    build_hypothesis,
    build_strategy_thesis,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    build_designer_mandate,
    build_designer_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-experiment")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

BASELINE = "analytics.baseline:buy_and_hold_v1"
COST_MODEL = "simulator.execution_profile:retail_fx_v1"
INPUT_REFS = ("data.market_dataset:EURUSD-H1@v3",)
METRICS = ("sharpe_ratio", "max_drawdown")
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
EMBARGO = 7 * 24 * 3600

DESIGN_OUTPUT = {
    "falsification_outcome": (
        "The holdout Sharpe is at or below the baseline's over the same window."
    ),
    "stop_rules": (
        "Stop if the discovery split yields no effect above the baseline.\n"
        "Stop if data quality is warned on more than one session."
    ),
    "leakage_controls": (
        "Indicator warm-up is contained inside each split.\n"
        "Positions are closed before the embargo begins."
    ),
}

REQUEST = {
    "schema_id": "simulation.backtest_request.v1",
    "config_hash": "sha256:config-a",
    "data_hash": "sha256:data-a",
    "strategy_id": "strategy-under-test",
    "seed": str(SEED),
}

RESULT = {
    "schema_id": "simulation.result.v1",
    "status": "completed",
    "run_id": "run-2026-07-29-a",
    "request_hash": "sha256:request-a",
    "config_hash": "sha256:config-a",
    "data_hash": "sha256:data-a",
    "engine_version": "simulator-4.2.0",
    "journal_ref": "simulator.journal:run-2026-07-29-a",
    "artifact_manifest_ref": "simulator.artifacts:run-2026-07-29-a",
}

VERDICT_OUTPUT = {
    "outcome": "not_refuted",
    "conclusion": (
        "The declared refuting outcome did not occur on the evaluated split."
    ),
    "limitations": (
        "One split cannot establish stability across regimes.\n"
        "No transaction-cost sensitivity was explored."
    ),
    "conflicts": "The discovery and validation readings disagree on persistence.",
}


class StubPort:
    """Deterministic Simulation port."""

    def __init__(self, result=None) -> None:
        self.result = RESULT if result is None else result
        self.calls: list[str] = []
        self.requests: list[dict[str, str]] = []

    def submit_backtest(self, request):
        self.calls.append("backtest")
        self.requests.append(dict(request))
        return self.result

    def resolve_run(self, run_id):
        self.calls.append(f"resolve:{run_id}")
        return self.result


class StubRuntime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, outputs=None, status="ok", reasons=()) -> None:
        self.outputs = outputs or {}
        self.status = status
        self.reasons = reasons
        self.invocations: list[object] = []
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.outputs.get(node_id),
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 800,
                "latency_ms": 70,
                "cost": Decimal("0.05"),
            },
        )


def _runtime(**overrides: object):
    outputs = {
        "design_experiment": dict(DESIGN_OUTPUT),
        "coordinate_simulation": dict(VERDICT_OUTPUT),
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
            "workflow_name": "design_experiment",
            "workflow_version": "1.0.0",
            "objective": "Specify a protocol that could refute the thesis.",
            "input_refs": INPUT_REFS,
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": "idem-experiment",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _hypothesis(**overrides: object):
    fields: dict[str, object] = {
        "hypothesis_id": derive_stable_id("id", "hyp-momentum"),
        "task_id": TASK_ID,
        "statement": "London-session momentum persists into the New York open.",
        "asset_scope": ("EURUSD",),
        "horizon": "intraday",
        "mechanism": "Order flow from the London fix carries into the overlap.",
        "prerequisites": ("Liquid session overlap", "No scheduled high-impact news"),
        "confounders": ("Month-end rebalancing flows",),
        "rejection_criterion": (
            "Overlap moves show no positive relationship to London-session moves."
        ),
        "evidence_refs": INPUT_REFS,
    }
    fields.update(overrides)
    return build_hypothesis(fields)


def _thesis():
    return build_strategy_thesis(
        {
            "thesis_id": derive_stable_id("id", "thesis-momentum"),
            "task_id": TASK_ID,
            "title": "Session-overlap momentum continuation",
            "summary": "Momentum formed in London may continue into the overlap.",
            "stance": "contested",
            "hypothesis_ids": (_hypothesis().hypothesis_id,),
            "signals": {"momentum": "Sign and magnitude of the London-session move."},
            "intended_behaviour": {
                "momentum": "Participate while the overlap trend persists.",
            },
            "supporting_evidence": INPUT_REFS,
            "retained_conflicts": ("Mean-reversion evidence disagrees.",),
            "assumptions": ("Session boundaries are stable.",),
            "uncertainty": "One venue, one instrument, one year of observations.",
            "next_test": "Evaluate the overlap relationship on a held-out year of data.",
        },
    )


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-14",
        "receiver_domain": name.split(".", maxsplit=1)[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("experiment_designer",),
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
        "role_id": "experiment_designer",
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
        build_designer_mandate(),
        (build_designer_role_manifest(**overrides),),
        NOW,
    )


def _design(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "runtime": _runtime(),
        "profile": _profile(),
        "thesis": _thesis(),
        "hypotheses": (_hypothesis(),),
        "input_refs": INPUT_REFS,
        "splits": SPLITS,
        "embargo_seconds": EMBARGO,
        "baseline_ref": BASELINE,
        "cost_model_ref": COST_MODEL,
        "metrics": METRICS,
        "seed": SEED,
        "at_time": NOW,
    }
    defaults.update(overrides)
    return design_experiment(**defaults)  # type: ignore[arg-type]


def _spec(**overrides: object) -> ExperimentSpec:
    payload = _design(**overrides).payload
    assert payload is not None
    return payload


def _coordinate(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_designer_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "port": StubPort(),
        "runtime": _runtime(),
        "profile": _profile(),
        "spec": _spec(),
        "request": dict(REQUEST),
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return coordinate_simulation(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_designer_role_manifest(), PROMPT_PATH)
    assert "Experiment Designer" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("Holdout may be reused freely.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _design(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Experiment Designer" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-040 - a protocol is complete or it does not exist
# --------------------------------------------------------------------------


def test_the_protocol_carries_every_required_element() -> None:
    spec = _spec()
    assert spec.input_refs == INPUT_REFS
    assert spec.baseline_ref == BASELINE
    assert spec.cost_model_ref == COST_MODEL
    assert spec.metrics == METRICS
    assert spec.seed == SEED
    assert spec.embargo_seconds == EMBARGO
    assert spec.stop_rules
    assert spec.leakage_controls
    assert spec.falsification_outcome
    assert {window.label for window in spec.splits} == {
        "discovery",
        "validation",
        "holdout",
    }


def test_configuration_comes_from_the_caller_not_the_model() -> None:
    poisoned = dict(DESIGN_OUTPUT)
    poisoned["seed"] = "99"
    poisoned["baseline_ref"] = "analytics.baseline:whatever_i_like"
    spec = _spec(runtime=_runtime(design_experiment=poisoned))
    assert spec.seed == SEED
    assert spec.baseline_ref == BASELINE


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stop_rules", ()),
        ("leakage_controls", ()),
        ("metrics", ()),
        ("input_refs", ()),
        ("hypothesis_ids", ()),
    ],
)
def test_an_incomplete_protocol_is_unrepresentable(field, value) -> None:
    spec = _spec()
    with pytest.raises(ValidationError, match="is required"):
        build_experiment_spec({**spec.model_dump(), field: value})


def test_a_thesis_that_could_not_fail_cannot_reach_the_designer() -> None:
    # `FEAT-AGT-13` makes a hypothesis without a rejection criterion
    # unrepresentable, so the designer needs no runtime check for it.
    with pytest.raises(ValidationError, match="non-empty trimmed text"):
        _hypothesis(rejection_criterion=" ")


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"hypotheses": ()}, "HYPOTHESES_ABSENT"),
        ({"input_refs": ()}, "INPUTS_ABSENT"),
        ({"baseline_ref": ""}, "BASELINE_ABSENT"),
    ],
)
def test_an_ineligible_design_refuses_before_the_model(override, reason) -> None:
    runtime = _runtime()
    result = _design(runtime=runtime, **override)
    assert result.status == "refused"
    assert result.reasons == (reason,)
    assert runtime.invocations == []


def test_overlapping_splits_are_refused_before_the_model() -> None:
    overlapping = (
        SPLITS[0],
        SplitWindow.model_validate(
            {
                "label": "validation",
                "start": datetime(2022, 6, 1, tzinfo=UTC),
                "end": datetime(2024, 1, 1, tzinfo=UTC),
            },
        ),
        SPLITS[2],
    )
    runtime = _runtime()
    result = _design(splits=overlapping, embargo_seconds=0, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SPLITS_INVALID",)
    assert "overlaps" in (result.detail or "")
    assert runtime.invocations == []


def test_a_gap_narrower_than_the_embargo_is_refused() -> None:
    result = _design(embargo_seconds=90 * 24 * 3600)
    assert result.status == "refused"
    assert result.reasons == ("SPLITS_INVALID",)
    assert "embargo" in (result.detail or "")


def test_a_missing_split_is_refused() -> None:
    result = _design(splits=SPLITS[:2])
    assert result.status == "refused"
    assert result.reasons == ("SPLITS_INVALID",)


def test_an_inverted_window_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must start before it ends"):
        SplitWindow.model_validate(
            {
                "label": "holdout",
                "start": datetime(2025, 1, 1, tzinfo=UTC),
                "end": datetime(2024, 1, 1, tzinfo=UTC),
            },
        )


def test_a_naive_window_bound_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        SplitWindow.model_validate(
            {
                "label": "holdout",
                "start": datetime(2024, 1, 1),  # noqa: DTZ001 - the rejected case.
                "end": datetime(2025, 1, 1, tzinfo=UTC),
            },
        )


def test_the_protocol_digest_covers_the_falsification_criterion() -> None:
    # Rewriting the criterion after the fact produces a different protocol, so
    # a verdict cannot be matched to a criterion that was never registered.
    spec = _spec()
    rewritten = {
        **spec.model_dump(),
        "falsification_outcome": "Anything short of spectacular refutes it.",
    }
    assert derive_spec_hash(rewritten) != spec.spec_hash


def test_split_validation_has_one_source_of_truth() -> None:
    # The agent's early refusal and the schema's structural guard call the same
    # helper, so the two can never disagree.
    assert validate_split_windows(SPLITS, EMBARGO) is None
    assert validate_split_windows(SPLITS[:1], 0) is not None


def test_the_spec_is_frozen() -> None:
    spec = _spec()
    with pytest.raises(ValidationError):
        spec.seed = 1


# --------------------------------------------------------------------------
# FR-AGENTIC-041 - the receiver owns its request and its result
# --------------------------------------------------------------------------


def test_the_request_is_passed_through_unchanged() -> None:
    port = StubPort()
    result = _coordinate(port=port)
    assert result.status == "ok"
    assert port.requests == [dict(REQUEST)]


def test_the_package_constructs_no_simulation_request_or_result() -> None:
    # There is no site at which Agentic could author either contract.
    for module in ("agent.py", "tools.py", "schemas.py", "repository.py"):
        source = (PROMPT_PATH.parent / module).read_text(encoding="utf-8")
        assert "SimulationBacktestRequest" not in source, module
        assert "SimulationResult" not in source, module
        assert "run_backtest(" not in source, module


def test_a_denied_tool_stops_the_run_before_the_receiver() -> None:
    port = StubPort()
    result = _coordinate(port=port, tool_policies=_tool_policies(enabled=False))
    assert result.status == "refused"
    assert result.reasons == ("SIMULATION_TOOL_DENIED",)
    assert port.calls == []


def test_an_unregistered_backtest_tool_is_refused() -> None:
    policies = _tool_policies()
    del policies[BACKTEST_TOOL]
    result = _coordinate(tool_policies=policies)
    assert result.status == "refused"
    assert result.reasons == ("SIMULATION_TOOL_DENIED",)


def test_a_role_without_the_permission_class_is_denied() -> None:
    narrow = _policy(permission_classes=("compute_deterministic",))
    result = _coordinate(policy=narrow)
    assert result.status == "refused"
    assert result.reasons == ("SIMULATION_TOOL_DENIED",)


def test_a_result_for_a_different_request_is_refused() -> None:
    tampered = {**RESULT, "config_hash": "sha256:some-other-config"}
    runtime = _runtime()
    result = _coordinate(port=StubPort(result=tampered), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_REQUEST",)
    assert "does not match" in (result.detail or "")
    # The verdict node was never reached: a non-binding result is a fault, not
    # something to hand to a model for reconciliation.
    assert runtime.nodes == []


@pytest.mark.parametrize("dropped", ["run_id", "journal_ref", "engine_version"])
def test_a_result_missing_lineage_is_refused(dropped) -> None:
    incomplete = {key: value for key, value in RESULT.items() if key != dropped}
    result = _coordinate(port=StubPort(result=incomplete))
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_REQUEST",)
    assert dropped in (result.detail or "")


def test_an_incomplete_run_is_refused() -> None:
    failed = {**RESULT, "status": "failed"}
    result = _coordinate(port=StubPort(result=failed))
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_REQUEST",)


def test_result_binding_accepts_a_corresponding_result() -> None:
    assert verify_result_binding(dict(REQUEST), dict(RESULT)) is None


def test_tool_calls_are_audited_when_a_store_is_injected() -> None:
    store = build_in_memory_memory_store()
    _coordinate(audit_store=store)
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 1


def test_registered_tool_names_are_stable() -> None:
    assert get_registered_tool_names() == (BACKTEST_TOOL, RUN_LOOKUP_TOOL)


# --------------------------------------------------------------------------
# FR-AGENTIC-042 - every conclusion names its run
# --------------------------------------------------------------------------


def test_conclusions_are_keyed_by_the_returned_run_identifier() -> None:
    verdict = _coordinate().payload
    assert set(verdict.conclusions) == {RESULT["run_id"]}
    assert set(verdict.evidence_classes) == set(verdict.conclusions)
    assert verdict.evidence_classes[RESULT["run_id"]] == "discovery"


def test_a_model_supplied_run_identifier_is_ignored() -> None:
    poisoned = {**VERDICT_OUTPUT, "run_id": "run-that-never-executed"}
    verdict = _coordinate(runtime=_runtime(coordinate_simulation=poisoned)).payload
    assert set(verdict.conclusions) == {RESULT["run_id"]}


def test_a_conclusion_without_an_evidence_class_is_unrepresentable() -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError, match="every conclusion requires"):
        build_experiment_verdict(
            {**verdict.model_dump(), "evidence_classes": {"another-run": "discovery"}},
        )


def test_an_evidence_class_naming_an_unknown_run_is_rejected() -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError, match="reached no conclusion"):
        build_experiment_verdict(
            {
                **verdict.model_dump(),
                "evidence_classes": {
                    **dict(verdict.evidence_classes),
                    "ghost-run": "validation",
                },
            },
        )


def test_the_verdict_binds_the_pre_registered_protocol_digest() -> None:
    spec = _spec()
    verdict = _coordinate(spec=spec).payload
    assert verdict.spec_hash == spec.spec_hash
    assert verdict.spec_id == spec.spec_id


@pytest.mark.parametrize(
    "evidence_class",
    ["discovery", "validation", "holdout", "null_data"],
)
def test_each_evidence_class_is_recorded_distinctly(evidence_class) -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    verdict = _coordinate(spec=spec, store=store, evidence_class=evidence_class).payload
    assert verdict.evidence_classes[RESULT["run_id"]] == evidence_class
    assert store.list_runs(spec.spec_hash)[0]["evidence_class"] == evidence_class


def test_an_unrecognized_declared_outcome_falls_back_to_inconclusive() -> None:
    poisoned = {**VERDICT_OUTPUT, "outcome": "definitely_profitable"}
    verdict = _coordinate(runtime=_runtime(coordinate_simulation=poisoned)).payload
    assert verdict.outcome == "inconclusive"


def test_a_verdict_citing_holdout_must_record_consumption() -> None:
    verdict = _coordinate().payload
    with pytest.raises(ValidationError, match="holdout_consumed"):
        build_experiment_verdict(
            {
                **verdict.model_dump(),
                "evidence_classes": {RESULT["run_id"]: "holdout"},
                "holdout_consumed": False,
            },
        )


def test_the_recorded_run_carries_the_receiver_lineage() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    _coordinate(spec=spec, store=store)
    row = store.list_runs(spec.spec_hash)[0]
    assert row["journal_ref"] == RESULT["journal_ref"]
    assert row["artifact_manifest_ref"] == RESULT["artifact_manifest_ref"]
    assert row["engine_version"] == RESULT["engine_version"]


def test_a_model_refusal_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("PROTOCOL_UNSOUND",))
    result = _design(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROTOCOL_UNSOUND",)
    assert result.payload is None


# --------------------------------------------------------------------------
# Holdout is consumed, not borrowed
# --------------------------------------------------------------------------


def test_holdout_is_spent_by_the_first_look() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    assert store.holdout_spent(spec.spec_hash) is False

    first = _coordinate(spec=spec, store=store, evidence_class="holdout")
    assert first.status == "ok"
    assert first.payload.holdout_consumed is True
    assert store.holdout_spent(spec.spec_hash) is True


def test_a_second_holdout_run_is_refused_before_the_receiver() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    _coordinate(spec=spec, store=store, evidence_class="holdout")

    port = StubPort()
    second = _coordinate(
        spec=spec,
        store=store,
        port=port,
        evidence_class="holdout",
    )
    assert second.status == "refused"
    assert second.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    assert port.calls == []


def test_non_holdout_runs_do_not_spend_holdout() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    for index, evidence_class in enumerate(("discovery", "validation", "null_data")):
        port = StubPort(result={**RESULT, "run_id": f"run-{index}"})
        result = _coordinate(
            spec=spec,
            store=store,
            port=port,
            evidence_class=evidence_class,
        )
        assert result.status == "ok"
        assert result.payload.holdout_consumed is False
    assert store.holdout_spent(spec.spec_hash) is False


def test_a_protocol_that_was_never_registered_is_refused() -> None:
    store = build_in_memory_experiment_store()
    port = StubPort()
    result = _coordinate(store=store, port=port)
    assert result.status == "refused"
    assert result.reasons == ("PROTOCOL_NOT_REGISTERED",)
    assert port.calls == []


def test_designing_records_the_protocol_when_a_store_is_injected() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec(store=store)
    assert store.load_spec(spec.spec_hash) is not None


def test_a_verdict_cannot_be_recorded_twice() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    _coordinate(spec=spec, store=store)
    with pytest.raises(ValueError, match="already exists"):
        _coordinate(spec=spec, store=store)


def test_holdout_without_a_store_is_still_reported_as_consumed() -> None:
    # With no ledger injected there is nothing to record against, but the
    # verdict must still say the look happened.
    result = _coordinate(evidence_class="holdout")
    assert result.status == "ok"
    assert result.payload.holdout_consumed is True


def test_a_model_refusal_during_coordination_is_propagated() -> None:
    # The default spec is designed by its own runtime; this one only serves
    # the verdict node, where it declines.
    runtime = StubRuntime(status="refused", reasons=("RUN_UNINTERPRETABLE",))
    result = _coordinate(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("RUN_UNINTERPRETABLE",)
    assert result.payload is None


def test_the_store_refuses_a_second_holdout_claim_directly() -> None:
    # Defence in depth: even if the eligibility check were bypassed, the
    # ledger itself grants the claim exactly once.
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    assert store.reserve_holdout(spec.spec_hash, TASK_ID, "run-a", NOW) is True
    assert store.reserve_holdout(spec.spec_hash, TASK_ID, "run-b", NOW) is False


def test_the_store_rejects_a_conflicting_protocol_digest() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    impostor = build_experiment_spec(
        {
            **{k: v for k, v in spec.model_dump().items() if k != "spec_hash"},
            "spec_id": derive_stable_id("id", "spec-impostor"),
            "splits": SPLITS,
        },
    )
    with pytest.raises(ValueError, match="already recorded"):
        store.save_spec(impostor.model_copy(update={"spec_hash": spec.spec_hash}))


def test_saving_the_same_protocol_twice_is_accepted() -> None:
    store = build_in_memory_experiment_store()
    spec = _spec()
    store.save_spec(spec)
    assert store.save_spec(spec) is spec
