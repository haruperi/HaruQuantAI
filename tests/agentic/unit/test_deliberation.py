"""Unit tests for FEAT-AGT-07 dynamic deliberation and synthesis.

Covers FR-AGENTIC-019 (independent briefs first, complete record),
FR-AGENTIC-020 (dissent preserved, insufficient_evidence permitted, consensus
confers no authorization), and FR-AGENTIC-021 (participant selection limited
to enabled roles and deterministic caps that a model cannot raise).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    assemble_context,
    build_agent_task,
    build_evidence_claim,
    build_in_memory_memory_store,
    build_model_profile,
    derive_content_hash,
    get_role_registry,
    reject_authorization_language,
    retrieve_memory,
    run_deliberation,
)
from app.agentic.deliberation import (
    Counterclaim,
    DeliberationRecord,
    DissentRecord,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    QUANT_ROLE_ID,
    TECHNICAL_ROLE_ID,
    build_quant_manifest,
    build_sandbox_mandate,
    build_technical_manifest,
)

TASK_ID = derive_stable_id("id", "task-deliberation")


class RecordingRuntime:
    """Deterministic runtime capturing every invocation it is given."""

    def __init__(self, refuse: tuple[str, ...] = ()) -> None:
        self.invocations: list[object] = []
        self._refuse = refuse

    def execute_node(self, node_id, profile, invocation):
        del node_id
        self.invocations.append(invocation)
        if invocation.role_id in self._refuse:
            return ModelOutcome.model_validate(
                {
                    "invocation_id": invocation.invocation_id,
                    "status": "refused",
                    "output": None,
                    "reasons": ("INSUFFICIENT_EVIDENCE",),
                    "provider": profile.provider,
                    "model_identifier": profile.model_identifier,
                    "tokens_used": 10,
                    "latency_ms": 5,
                    "cost": Decimal("0.001"),
                },
            )
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": {
                    "observation": f"{invocation.role_id} observed higher lows.",
                },
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 100,
                "latency_ms": 20,
                "cost": Decimal("0.01"),
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


def _task(**overrides: object):
    fields: dict[str, object] = {
        "created_at": NOW,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "causation_id": None,
        "task_id": TASK_ID,
        "workflow_name": "firm_research_council",
        "workflow_version": "1.0.0",
        "objective": "Assess EURUSD H1 trend evidence.",
        "input_refs": ("evidence-market-1",),
        "principal_id": "operator-owner",
        "scope": {"environment": "sandbox"},
        "deadline_at": NOW + timedelta(minutes=30),
        "idempotency_key": "idem-deliberation",
        "budgets": {"cost": Decimal("5.00")},
    }
    fields.update(overrides)
    return build_agent_task(fields)


def _context(task):
    claim = build_evidence_claim(
        {
            "claim_id": "claim-0001",
            "task_id": task.task_id,
            "statement": "EURUSD H1 printed three consecutive higher lows.",
            "source_ref": "data.market_dataset:eurusd-h1",
            "source_trust": "authoritative",
            "licence_ref": "internal-market-data",
            "available_at": NOW - timedelta(minutes=5),
            "observed_at": NOW,
            "content_hash": derive_content_hash({"claim": "higher-lows"}),
            "confidence_basis": "Three confirmed swing lows.",
            "falsifier": "A close below the 200-period EMA.",
            "injection_status": "clean",
        },
    )
    return assemble_context(
        task.task_id,
        (claim,),
        NOW,
        trusted_context={"instrument": "EURUSD"},
    )


def _registry():
    return get_role_registry(
        build_sandbox_mandate(),
        (build_technical_manifest(), build_quant_manifest()),
        NOW,
    )


def _run(**overrides: object):
    task = overrides.pop("task", _task())
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": task,
        "context": _context(task),
        "runtime": RecordingRuntime(),
        "profile": _profile(),
        "requested_roles": (TECHNICAL_ROLE_ID, QUANT_ROLE_ID),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return run_deliberation(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# FR-AGENTIC-019 - independent briefs and a complete record
# --------------------------------------------------------------------------


def test_deliberation_produces_a_complete_record() -> None:
    record = _run()
    assert isinstance(record, DeliberationRecord)
    assert record.task_id == TASK_ID
    assert record.plan.participants == (QUANT_ROLE_ID, TECHNICAL_ROLE_ID)
    assert record.plan.topology == "independent_briefs_then_bounded_challenge"
    assert record.participants_used == 2
    assert record.terminal_reason
    assert len(record.content_hash) == 64


def test_briefs_are_collected_before_any_peer_exposure() -> None:
    runtime = RecordingRuntime()
    record = _run(runtime=runtime)
    # Every brief invocation must contain only assembled evidence; no peer
    # statement can appear, because none exists when the brief is built.
    peer_statements = {message.content["observation"] for message in record.messages}
    for invocation in runtime.invocations:
        evidence_text = " ".join(invocation.untrusted_evidence.values())
        assert not any(statement in evidence_text for statement in peer_statements)


def test_every_participant_receives_the_same_independent_context() -> None:
    runtime = RecordingRuntime()
    _run(runtime=runtime)
    evidence_sets = {
        tuple(sorted(invocation.untrusted_evidence.items()))
        for invocation in runtime.invocations
    }
    assert len(evidence_sets) == 1


def test_record_captures_plan_rounds_and_stop_reason() -> None:
    record = _run()
    assert record.plan.max_rounds >= record.rounds_used
    assert record.plan.max_participants >= len(record.plan.participants)
    assert record.plan.budgets
    assert record.plan.deadline_at == NOW + timedelta(minutes=30)


def test_stances_are_assigned_only_to_participants() -> None:
    record = _run()
    assert set(record.plan.stances) <= set(record.plan.participants)
    assert "proposer" in record.plan.stances.values()


def test_refusals_are_recorded_without_failing_the_run() -> None:
    record = _run(runtime=RecordingRuntime(refuse=(QUANT_ROLE_ID,)))
    assert QUANT_ROLE_ID in record.refusals
    assert record.participants_used == 1


def test_all_refusals_produce_insufficient_evidence() -> None:
    runtime = RecordingRuntime(refuse=(TECHNICAL_ROLE_ID, QUANT_ROLE_ID))
    record = _run(runtime=runtime)
    assert record.terminal_reason == "insufficient_evidence"
    assert record.synthesis is None


def test_record_is_persisted_when_a_store_is_injected() -> None:
    store = build_in_memory_memory_store()
    record = _run(memory_store=store)
    assert record.persisted is True
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 1


def test_record_is_not_persisted_without_a_store() -> None:
    assert _run().persisted is False


# --------------------------------------------------------------------------
# FR-AGENTIC-020 - dissent, insufficient evidence, and no authorization
# --------------------------------------------------------------------------


def test_unresolved_challenges_are_preserved_as_dissent() -> None:
    record = _run()
    assert record.counterclaims
    assert record.dissent
    assert all(item.unresolved for item in record.dissent)


def test_consensus_cannot_be_claimed_while_dissent_is_unresolved() -> None:
    record = _run()
    assert record.consensus_reached is False


def test_material_unresolved_conflict_is_a_terminal_reason() -> None:
    assert _run().terminal_reason == "material_unresolved_conflict"


@pytest.mark.parametrize(
    "text",
    [
        "The council approved the trade.",
        "Authorization granted to proceed.",
        "Use a position size of two lots.",
        "Recommended lot size is 0.5.",
        "Place the order at market.",
    ],
)
def test_authorization_language_is_rejected(text) -> None:
    with pytest.raises(ValueError, match="must not carry authorization"):
        reject_authorization_language(text, "synthesis")


def test_advisory_language_is_accepted() -> None:
    advisory = "Evidence supports an upward bias; deterministic review required."
    assert reject_authorization_language(advisory, "synthesis") == advisory


def test_synthesis_may_not_carry_authorization_language() -> None:
    record = _run()
    with pytest.raises(ValidationError):
        record.model_copy(update={}).__class__.model_validate(
            {**record.model_dump(), "synthesis": "The council approved the trade."},
        )


def test_counterclaim_may_not_carry_authorization_language() -> None:
    with pytest.raises(ValidationError):
        Counterclaim.model_validate(
            {
                "counterclaim_id": "cc-1",
                "task_id": TASK_ID,
                "round_index": 0,
                "challenger_role_id": QUANT_ROLE_ID,
                "stance": "adversarial_challenger",
                "targets_claim_id": "msg-1",
                "statement": "I approve a position size of two lots.",
            },
        )


def test_dissent_may_not_carry_authorization_language() -> None:
    with pytest.raises(ValidationError):
        DissentRecord.model_validate(
            {
                "dissent_id": "d-1",
                "task_id": TASK_ID,
                "dissenting_role_id": QUANT_ROLE_ID,
                "statement": "Authorization granted despite the conflict.",
                "basis": "conflicting_evidence",
            },
        )


def test_insufficient_evidence_outcome_carries_no_synthesis() -> None:
    record = _run(runtime=RecordingRuntime(refuse=(TECHNICAL_ROLE_ID, QUANT_ROLE_ID)))
    with pytest.raises(ValidationError):
        type(record).model_validate(
            {
                **record.model_dump(),
                "terminal_reason": "insufficient_evidence",
                "synthesis": "A conclusion was nonetheless reached.",
            },
        )


# --------------------------------------------------------------------------
# FR-AGENTIC-021 - selection limited to enabled roles and deterministic caps
# --------------------------------------------------------------------------


def test_unregistered_roles_are_never_selected() -> None:
    record = _run(
        requested_roles=(TECHNICAL_ROLE_ID, "ghost_role", "sentiment_analyst")
    )
    assert record.plan.participants == (TECHNICAL_ROLE_ID,)


def test_disabled_roles_are_never_selected() -> None:
    registry = get_role_registry(
        build_sandbox_mandate(),
        (build_technical_manifest(enabled=False), build_quant_manifest()),
        NOW,
    )
    record = _run(registry=registry)
    assert record.plan.participants == (QUANT_ROLE_ID,)


def test_no_eligible_participants_is_terminal() -> None:
    record = _run(requested_roles=("ghost_role",))
    assert record.plan.participants == ()
    assert record.terminal_reason == "no_eligible_participants"


def test_participant_selection_is_deterministic() -> None:
    first = _run(requested_roles=(QUANT_ROLE_ID, TECHNICAL_ROLE_ID))
    second = _run(requested_roles=(TECHNICAL_ROLE_ID, QUANT_ROLE_ID))
    assert first.plan.participants == second.plan.participants


def test_caps_come_from_the_limits_profile_not_the_caller() -> None:
    record = _run()
    assert record.plan.max_rounds == 1
    assert record.plan.max_participants == 8
    assert record.plan.max_fan_out == 4
    assert record.plan.limits_profile_id == "agentic-limits-sandbox-v1"


def test_rounds_used_never_exceed_the_cap() -> None:
    record = _run()
    assert record.rounds_used <= record.plan.max_rounds


def test_a_record_claiming_more_rounds_than_its_cap_is_rejected() -> None:
    record = _run()
    with pytest.raises(ValidationError):
        type(record).model_validate({**record.model_dump(), "rounds_used": 99})


def test_a_plan_exceeding_its_participant_cap_is_rejected() -> None:
    record = _run()
    inflated = {
        **record.plan.model_dump(),
        "participants": tuple(f"role_{n}" for n in range(20)),
        "stances": {},
        "max_participants": 2,
    }
    with pytest.raises(ValidationError):
        type(record.plan).model_validate(inflated)


def test_a_plan_naming_stances_for_non_participants_is_rejected() -> None:
    record = _run()
    with pytest.raises(ValidationError):
        type(record.plan).model_validate(
            {**record.plan.model_dump(), "stances": {"ghost_role": "proposer"}},
        )


def test_an_unregistered_limits_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="unregistered"):
        _run(limits_profile_id="agentic-limits-unbounded")
