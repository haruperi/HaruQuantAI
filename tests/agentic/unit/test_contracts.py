"""Unit tests for FEAT-AGT-01 canonical Agentic contracts.

Covers FR-AGENTIC-001 (immutable, versioned, finite, strict, JSON-safe),
FR-AGENTIC-002 (ok/refused/failed separation and prohibited execution fields),
and FR-AGENTIC-003 (identity, UTC time, schema/version, lineage, and hash).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest
from app.agentic.contracts import (
    AgentArtifact,
    AgentMessage,
    AgentProvenance,
    AgentResult,
    AgentTask,
    BudgetUsage,
    WorkflowCheckpoint,
)
from app.kernel.identity import derive_stable_id, generate_id
from app.kernel.serialization import canonical_digest
from pydantic import ValidationError

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def _identity(material: str) -> str:
    return derive_stable_id("id", material)


def _envelope(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "created_at": NOW,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "causation_id": None,
        "canonical_hash": HASH_A,
    }
    data.update(overrides)
    return data


def _task_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(),
        "task_id": _identity("task-alpha"),
        "workflow_name": "firm_research_council",
        "workflow_version": "1.0.0",
        "objective": "Assess EURUSD H1 trend evidence for the current session.",
        "input_refs": ("evidence-market-1", "evidence-indicator-1"),
        "principal_id": "operator-owner",
        "scope": {"environment": "sandbox", "asset_class": "fx"},
        "deadline_at": NOW + timedelta(minutes=30),
        "idempotency_key": "idem-research-0001",
        "budgets": {
            "cost": Decimal("5.00"),
            "model_calls": Decimal(12),
            "tokens": Decimal(40000),
        },
    }
    data.update(overrides)
    return data


def _usage_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(canonical_hash=HASH_B),
        "usage_id": _identity("usage-alpha"),
        "task_id": _identity("task-alpha"),
        "tokens": 1200,
        "model_calls": 3,
        "tool_calls": 2,
        "cost": Decimal("0.42"),
        "compute_seconds": Decimal("3.5"),
        "storage_bytes": 0,
        "search_trials": 0,
    }
    data.update(overrides)
    return data


def _provenance_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(canonical_hash=HASH_C),
        "provenance_id": _identity("provenance-alpha"),
        "task_id": _identity("task-alpha"),
        "role_id": "technical_analyst",
        "role_version": "1.0.0",
        "model_profile_id": "profile-analysis-a",
        "model_provider": "gemini",
        "model_identifier": "gemini-3.0-pro-002",
        "base_prompt_hash": HASH_A,
        "manifest_hash": HASH_B,
        "composite_instruction_hash": HASH_C,
        "tool_refs": ("data.get_market_data",),
        "evidence_refs": ("evidence-market-1",),
        "mandate_id": "mandate-sandbox",
        "mandate_version": "1.0.0",
        "policy_version": "1.0.0",
        "limits_profile_id": "limits-sandbox-v1",
        "seed": 7,
    }
    data.update(overrides)
    return data


def _message_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(),
        "message_id": _identity("message-alpha"),
        "task_id": _identity("task-alpha"),
        "sender_role_id": "technical_analyst",
        "sender_role_version": "1.0.0",
        "recipient_role_id": "strategy_thesis_analyst",
        "message_type": "brief",
        "round_index": 0,
        "content": {"summary": "Trend is up on H1 with confirmed higher lows."},
        "evidence_refs": ("evidence-market-1",),
    }
    data.update(overrides)
    return data


def _artifact_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(),
        "artifact_id": _identity("artifact-alpha"),
        "task_id": _identity("task-alpha"),
        "artifact_type": "code_artifact",
        "content_ref": "staging/artifacts/alpha",
        "content_schema_id": "agentic.code_artifact.v1",
        "content_hash": HASH_B,
        "size_bytes": 2048,
        "provenance_id": _identity("provenance-alpha"),
    }
    data.update(overrides)
    return data


def _checkpoint_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(),
        "checkpoint_id": _identity("checkpoint-alpha"),
        "task_id": _identity("task-alpha"),
        "workflow_name": "firm_research_council",
        "workflow_version": "1.0.0",
        "node_id": "collect_briefs",
        "sequence": 2,
        "state": "running",
        "expected_version": 2,
        "state_payload_hash": HASH_C,
    }
    data.update(overrides)
    return data


def _result_data(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        **_envelope(),
        "result_id": _identity("result-alpha"),
        "task_id": _identity("task-alpha"),
        "status": "ok",
        "payload": {"conclusion": "trend_up"},
        "reasons": (),
        "detail": "Two independent briefs agreed; one dissent recorded.",
        "provenance": AgentProvenance(**_provenance_data()),
        "budget_usage": BudgetUsage(**_usage_data()),
    }
    data.update(overrides)
    return data


ALL_BUILDERS = (
    (AgentTask, _task_data),
    (BudgetUsage, _usage_data),
    (AgentProvenance, _provenance_data),
    (AgentMessage, _message_data),
    (AgentArtifact, _artifact_data),
    (WorkflowCheckpoint, _checkpoint_data),
    (AgentResult, _result_data),
)


# --------------------------------------------------------------------------
# FR-AGENTIC-001 - immutable, versioned, finite, strictly validated, JSON-safe
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_are_frozen(contract, builder) -> None:
    instance = contract(**builder())
    with pytest.raises(ValidationError):
        instance.task_id = _identity("mutated")


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_reject_unknown_fields(contract, builder) -> None:
    with pytest.raises(ValidationError):
        contract(**builder(unexpected_field="bad"))


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_are_json_safe(contract, builder) -> None:
    instance = contract(**builder())
    encoded = json.dumps(instance.model_dump(mode="json"), sort_keys=True)
    assert json.loads(encoded)["contract_version"] == "v1"


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_declare_distinct_version_and_schema(contract, builder) -> None:
    instance = contract(**builder())
    assert instance.contract_version == "v1"
    assert instance.schema_id.startswith("agentic.")
    assert instance.schema_id.endswith(".v1")
    assert instance.schema_id != instance.contract_version


def test_strict_mode_rejects_coercible_primitives() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(**_message_data(round_index="0"))


def test_non_finite_budget_amount_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(budgets={"cost": Decimal("NaN")}))


def test_negative_budget_amount_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(budgets={"cost": Decimal(-1)}))


def test_unsupported_budget_dimension_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(budgets={"unbounded_spend": Decimal(1)}))


def test_empty_budgets_are_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(budgets={}))


def test_negative_usage_counter_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BudgetUsage(**_usage_data(tokens=-1))


def test_oversized_objective_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(objective="x" * 2001))


def test_untrimmed_text_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(workflow_name=" firm_research_council "))


def test_oversized_reference_tuple_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(input_refs=tuple(f"ref-{n}" for n in range(65))))


def test_scope_is_frozen_and_deterministically_ordered() -> None:
    task = AgentTask(**_task_data(scope={"z_key": "last", "a_key": "first"}))
    assert list(task.scope) == ["a_key", "z_key"]
    with pytest.raises(TypeError):
        task.scope["a_key"] = "mutated"  # type: ignore[index]


def test_budgets_serialize_without_precision_loss() -> None:
    task = AgentTask(**_task_data(budgets={"cost": Decimal("5.10")}))
    assert task.model_dump(mode="json")["budgets"]["cost"] == "5.10"


def test_usage_amounts_serialize_without_precision_loss() -> None:
    usage = BudgetUsage(**_usage_data(cost=Decimal("0.40")))
    assert usage.model_dump(mode="json")["cost"] == "0.40"


# --------------------------------------------------------------------------
# FR-AGENTIC-002 - ok / refused / failed and prohibited execution fields
# --------------------------------------------------------------------------


def test_ok_result_carries_payload_and_no_reasons() -> None:
    result = AgentResult(**_result_data())
    assert result.status == "ok"
    assert result.payload == {"conclusion": "trend_up"}
    assert result.reasons == ()


@pytest.mark.parametrize("status", ["refused", "failed"])
def test_refused_and_failed_results_carry_reasons_without_payload(status) -> None:
    result = AgentResult(
        **_result_data(status=status, payload=None, reasons=("INSUFFICIENT_EVIDENCE",)),
    )
    assert result.status == status
    assert result.payload is None
    assert result.reasons == ("INSUFFICIENT_EVIDENCE",)


def test_unknown_status_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(**_result_data(status="approved"))


def test_ok_result_without_payload_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(**_result_data(payload=None))


def test_ok_result_with_reasons_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(**_result_data(reasons=("INSUFFICIENT_EVIDENCE",)))


def test_refused_result_with_payload_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            **_result_data(status="refused", reasons=("POLICY_DENIED",)),
        )


def test_refused_result_without_reasons_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(**_result_data(status="refused", payload=None, reasons=()))


def test_free_text_reason_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentResult(
            **_result_data(
                status="refused",
                payload=None,
                reasons=("the evidence was not good enough",),
            ),
        )


@pytest.mark.parametrize(
    "prohibited_key",
    [
        "broker_order_id",
        "kill_switch_clear",
        "position_size",
        "approval_token",
        "api_key",
        "account_password",
    ],
)
def test_message_content_rejects_execution_fields(prohibited_key) -> None:
    with pytest.raises(ValidationError):
        AgentMessage(**_message_data(content={prohibited_key: "value"}))


def test_task_scope_rejects_execution_fields() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(scope={"broker_credential": "value"}))


def test_floating_model_alias_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentProvenance(**_provenance_data(model_identifier="gemini-3.0-pro-latest"))


def test_wildcard_model_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentProvenance(**_provenance_data(model_identifier="gemini-3.0-*"))


def test_exact_model_identifier_is_accepted() -> None:
    provenance = AgentProvenance(**_provenance_data(model_identifier="claude-opus-5"))
    assert provenance.model_identifier == "claude-opus-5"


# --------------------------------------------------------------------------
# FR-AGENTIC-003 - identity, UTC time, schema/version, lineage, and hash
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_carry_complete_trace_lineage(contract, builder) -> None:
    instance = contract(**builder())
    assert instance.request_id.startswith("req-")
    assert instance.workflow_id.startswith("wf-")
    assert instance.correlation_id.startswith("cor-")
    assert instance.causation_id is None


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_carry_utc_creation_time(contract, builder) -> None:
    instance = contract(**builder())
    assert instance.created_at.tzinfo is not None
    assert instance.created_at.utcoffset() == timedelta(0)


@pytest.mark.parametrize(("contract", "builder"), ALL_BUILDERS)
def test_contracts_carry_canonical_hash(contract, builder) -> None:
    instance = contract(**builder())
    assert len(instance.canonical_hash) == 64
    assert instance.canonical_hash == instance.canonical_hash.lower()


def test_canonical_digest_output_is_an_accepted_hash() -> None:
    digest = canonical_digest({"objective": "assess trend"})
    task = AgentTask(**_task_data(canonical_hash=digest))
    assert task.canonical_hash == digest


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(created_at=datetime(2026, 7, 29, 12, 0)))  # noqa: DTZ001


def test_non_utc_timestamp_is_rejected() -> None:
    offset = datetime(2026, 7, 29, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(created_at=offset))


def test_malformed_canonical_hash_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(canonical_hash="not-a-digest"))


def test_uppercase_canonical_hash_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(canonical_hash="A" * 64))


def test_non_canonical_entity_identity_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(task_id="task-alpha"))


def test_mismatched_trace_prefix_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(request_id=generate_id("wf")))


def test_non_uuid4_trace_identifier_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(request_id="req-not-a-uuid"))


def test_optional_causation_lineage_is_accepted() -> None:
    causation = generate_id("cau")
    task = AgentTask(**_task_data(causation_id=causation))
    assert task.causation_id == causation


def test_causation_identifier_prefix_is_enforced() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(causation_id=f"evt-{uuid.uuid4()}"))


def test_result_embeds_provenance_and_budget_lineage() -> None:
    result = AgentResult(**_result_data())
    assert result.provenance.composite_instruction_hash == HASH_C
    assert result.budget_usage.task_id == result.task_id


def test_checkpoint_states_cover_durable_state_machine() -> None:
    for state in ("submitted", "running", "waiting_human", "succeeded"):
        checkpoint = WorkflowCheckpoint(**_checkpoint_data(state=state))
        assert checkpoint.state == state


def test_unknown_checkpoint_state_is_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkflowCheckpoint(**_checkpoint_data(state="approved"))


def test_unknown_message_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(**_message_data(message_type="instruction"))


def test_optional_seed_may_be_absent() -> None:
    provenance = AgentProvenance(**_provenance_data(seed=None))
    assert provenance.seed is None


def test_negative_seed_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentProvenance(**_provenance_data(seed=-1))


def test_optional_detail_may_be_absent() -> None:
    result = AgentResult(**_result_data(detail=None))
    assert result.detail is None


def test_empty_scope_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(scope={}))


def test_empty_message_content_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AgentMessage(**_message_data(content={}))


def test_oversized_scope_mapping_is_rejected() -> None:
    oversized = {f"key_{n}": "value" for n in range(33)}
    with pytest.raises(ValidationError):
        AgentTask(**_task_data(scope=oversized))


def test_oversized_reason_tuple_is_rejected() -> None:
    reasons = tuple(f"REASON_{n}" for n in range(65))
    with pytest.raises(ValidationError):
        AgentResult(**_result_data(status="refused", payload=None, reasons=reasons))


def test_non_finite_usage_amount_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BudgetUsage(**_usage_data(cost=Decimal("Infinity")))


def test_negative_usage_amount_is_rejected() -> None:
    with pytest.raises(ValidationError):
        BudgetUsage(**_usage_data(cost=Decimal("-0.01")))


def test_artifact_carries_content_reference_not_inline_bytes() -> None:
    artifact = AgentArtifact(**_artifact_data())
    assert artifact.content_ref == "staging/artifacts/alpha"
    assert not hasattr(artifact, "content")
