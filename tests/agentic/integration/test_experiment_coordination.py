"""Integration evidence for FEAT-AGT-14 across the governed control plane.

Exercises the full path a role-bearing feature with persistence must traverse:
mandate and roster validation, policy-registry validation, deny-by-default tool
authorization, pre-registration in the experiment ledger, a receiver-owned run
through the governed tool path, result binding, and a run-bound verdict.

This covers `WF-AGT-003` steps 3 through 5. Steps 1 and 2 need `FEAT-AGT-09`,
which is blocked on `FEAT-DATA-16`, so the workflow itself is not yet complete.

The Simulation receiver arrives as an injected port bound to deterministic
doubles, so no backtest executes. What is exercised is the governance path,
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
from app.agentic.agents.experimentation.experiment_designer import (
    coordinate_simulation,
    design_experiment,
)
from app.agentic.agents.experimentation.experiment_designer.migrations import (
    build_experiment_migration_request,
    get_experiment_migration_statements,
)
from app.agentic.agents.experimentation.experiment_designer.repository import (
    build_in_memory_experiment_store,
)
from app.agentic.agents.experimentation.experiment_designer.schemas import SplitWindow
from app.agentic.agents.experimentation.experiment_designer.tools import (
    get_registered_tool_names,
)
from app.agentic.agents.strategy_desk.strategy_thesis_analyst import (
    build_hypothesis,
    build_strategy_thesis,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    DESIGNER_ROLE_ID,
    NOW,
    build_designer_mandate,
    build_designer_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-experiment-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

BASELINE = "analytics.baseline:buy_and_hold_v1"
COST_MODEL = "simulator.execution_profile:retail_fx_v1"
INPUT_REFS = ("data.market_dataset:EURUSD-H1@v3",)
EMBARGO = 7 * 24 * 3600
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
    "schema_id": "simulation.backtest_request.v1",
    "config_hash": "sha256:config-a",
    "data_hash": "sha256:data-a",
    "seed": str(SEED),
}

RESULT = {
    "schema_id": "simulation.result.v1",
    "status": "completed",
    "run_id": "run-integration-a",
    "request_hash": "sha256:request-a",
    "config_hash": "sha256:config-a",
    "engine_version": "simulator-4.2.0",
    "journal_ref": "simulator.journal:run-integration-a",
    "artifact_manifest_ref": "simulator.artifacts:run-integration-a",
}

OUTPUTS = {
    "design_experiment": {
        "falsification_outcome": (
            "The holdout Sharpe is at or below the baseline's over the window."
        ),
        "stop_rules": "Stop if discovery yields no effect above the baseline.",
        "leakage_controls": "Indicator warm-up is contained inside each split.",
    },
    "coordinate_simulation": {
        "outcome": "refuted",
        "conclusion": "The declared refuting outcome occurred on the holdout split.",
        "limitations": "One protocol cannot establish stability across regimes.",
    },
}


class _Port:
    """Deterministic Simulation port."""

    def __init__(self, result: dict[str, str] | None = None) -> None:
        self.result = RESULT if result is None else result
        self.calls: list[str] = []

    def submit_backtest(self, request):
        self.calls.append("backtest")
        del request
        return self.result

    def resolve_run(self, run_id):
        self.calls.append(f"resolve:{run_id}")
        return self.result


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
                "tokens_used": 640,
                "latency_ms": 50,
                "cost": Decimal("0.03"),
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
            "workflow_name": "design_experiment",
            "workflow_version": "1.0.0",
            "objective": "Specify and run a protocol that could refute the thesis.",
            "input_refs": INPUT_REFS,
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": "idem-experiment-integration",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _hypothesis():
    return build_hypothesis(
        {
            "hypothesis_id": derive_stable_id("id", "hyp-integration"),
            "task_id": TASK_ID,
            "statement": "London-session momentum persists into the overlap.",
            "asset_scope": ("EURUSD",),
            "horizon": "intraday",
            "mechanism": "Order flow from the London fix carries into the overlap.",
            "prerequisites": ("Liquid session overlap",),
            "confounders": ("Month-end rebalancing flows",),
            "rejection_criterion": (
                "Overlap moves show no positive relationship to London-session moves."
            ),
            "evidence_refs": INPUT_REFS,
        },
    )


def _thesis():
    return build_strategy_thesis(
        {
            "thesis_id": derive_stable_id("id", "thesis-integration"),
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


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-14",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (DESIGNER_ROLE_ID,),
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
            "role_id": DESIGNER_ROLE_ID,
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
    mandate = build_designer_mandate()
    registry = get_role_registry(mandate, (build_designer_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    return mandate, registry, tools, policies


def _design(registry, store):
    """Design and pre-register one protocol through the public API."""
    return design_experiment(
        registry,
        _task(),
        _Runtime(),
        _profile(),
        _thesis(),
        (_hypothesis(),),
        INPUT_REFS,
        SPLITS,
        EMBARGO,
        BASELINE,
        COST_MODEL,
        ("sharpe_ratio",),
        SEED,
        store=store,
        at_time=NOW,
    )


def test_experiment_designer_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, policies = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, DESIGNER_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())
    assert set(tools) == set(get_registered_tool_names())

    # 2. The protocol is pre-registered before any run exists.
    store = build_in_memory_experiment_store()
    designed = _design(registry, store)
    assert designed.status == "ok"
    spec = designed.payload
    assert spec is not None
    assert store.load_spec(spec.spec_hash) is not None

    # 3. The run traverses the governed tool path and binds to its request.
    port, runtime = _Port(), _Runtime()
    audit = build_in_memory_memory_store()
    coordinated = coordinate_simulation(
        registry,
        _task(),
        mandate,
        policies[DESIGNER_ROLE_ID],
        tools,
        port,
        runtime,
        _profile(),
        spec,
        dict(REQUEST),
        evidence_class="holdout",
        store=store,
        request_scope=dict(SCOPE),
        audit_store=audit,
        at_time=NOW,
    )

    assert coordinated.status == "ok"
    verdict = coordinated.payload
    assert verdict is not None
    assert verdict.spec_hash == spec.spec_hash
    assert set(verdict.conclusions) == {RESULT["run_id"]}
    assert verdict.evidence_classes[RESULT["run_id"]] == "holdout"
    assert verdict.outcome == "refuted"
    assert verdict.holdout_consumed is True

    # 4. The run, its lineage, and the holdout claim are all recorded.
    assert port.calls == ["backtest"]
    assert store.list_runs(spec.spec_hash)[0]["journal_ref"] == RESULT["journal_ref"]
    assert store.holdout_spent(spec.spec_hash) is True
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 1
    assert coordinated.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_experiment_designer_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_designer_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_holdout_scarcity_survives_across_the_control_plane() -> None:
    mandate, registry, tools, policies = _control_plane()
    store = build_in_memory_experiment_store()
    spec = _design(registry, store).payload
    assert spec is not None

    for _ in range(2):
        coordinate_simulation(
            registry,
            _task(),
            mandate,
            policies[DESIGNER_ROLE_ID],
            tools,
            _Port(),
            _Runtime(),
            _profile(),
            spec,
            dict(REQUEST),
            evidence_class="holdout",
            store=store,
            request_scope=dict(SCOPE),
            at_time=NOW,
        )

    port = _Port()
    third = coordinate_simulation(
        registry,
        _task(),
        mandate,
        policies[DESIGNER_ROLE_ID],
        tools,
        port,
        _Runtime(),
        _profile(),
        spec,
        dict(REQUEST),
        evidence_class="holdout",
        store=store,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert third.status == "refused"
    assert third.reasons == ("HOLDOUT_ALREADY_CONSUMED",)
    # Refused before the receiver: the second look never happens.
    assert port.calls == []


def test_a_tampered_result_never_reaches_the_verdict_model() -> None:
    mandate, registry, tools, policies = _control_plane()
    store = build_in_memory_experiment_store()
    spec = _design(registry, store).payload
    assert spec is not None

    runtime = _Runtime()
    result = coordinate_simulation(
        registry,
        _task(),
        mandate,
        policies[DESIGNER_ROLE_ID],
        tools,
        _Port(result={**RESULT, "config_hash": "sha256:not-the-submitted-config"}),
        runtime,
        _profile(),
        spec,
        dict(REQUEST),
        store=store,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("RESULT_NOT_FOR_REQUEST",)
    assert runtime.nodes == []
    assert store.list_runs(spec.spec_hash) == ()


def test_the_experiment_ledger_declares_schema_without_executing_it() -> None:
    statements = get_experiment_migration_statements()
    assert any("agentic_experiment_specs" in statement for statement in statements)
    assert any(
        "agentic_experiment_holdout_use" in statement for statement in statements
    )
    # The holdout table's primary key is what makes scarcity durable.
    holdout = next(s for s in statements if "agentic_experiment_holdout_use" in s)
    assert "spec_hash TEXT PRIMARY KEY" in holdout

    request = build_experiment_migration_request(generate_id("req"))
    assert request is not None
