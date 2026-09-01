"""Unit tests for FEAT-AGT-04 durable task and workflow orchestration.

Covers FR-AGENTIC-010 (idempotent submission, checkpoint before execution),
FR-AGENTIC-011 (bounded routing, cancellation, expiry, resume), and
FR-AGENTIC-012 (terminal states never resume under the same task identity).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_task,
    build_agentic_migration_request,
    build_in_memory_workflow_store,
    build_workflow_definition,
    cancel_task,
    expire_task,
    get_agentic_migration_statements,
    is_terminal_state,
    resume_task,
    submit_task,
    validate_transition,
)
from app.agentic.orchestration import AgenticWorkflowStore
from app.kernel.identity import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import NOW

WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"


def definition_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "workflow_name": WORKFLOW_NAME,
        "version": WORKFLOW_VERSION,
        "nodes": ("collect_briefs", "challenge", "synthesize"),
        "entry_node": "collect_briefs",
        "limits_profile_id": "agentic-limits-sandbox-v1",
        "max_fan_out": 4,
        "max_rounds": 1,
        "max_retries": 2,
        "deadline_seconds": 1_800,
        "permits_human_wait": True,
    }
    data.update(overrides)
    return data


def task_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "created_at": NOW,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "causation_id": None,
        "task_id": derive_stable_id("id", "task-orchestration"),
        "workflow_name": WORKFLOW_NAME,
        "workflow_version": WORKFLOW_VERSION,
        "objective": "Assess EURUSD H1 trend evidence.",
        "input_refs": ("evidence-market-1",),
        "principal_id": "operator-owner",
        "scope": {"environment": "sandbox"},
        "deadline_at": NOW + timedelta(minutes=30),
        "idempotency_key": "idem-orchestration-0001",
        "budgets": {"cost": Decimal("5.00")},
    }
    data.update(overrides)
    return data


def _fixture() -> tuple[AgenticWorkflowStore, object, object]:
    return (
        build_in_memory_workflow_store(),
        build_workflow_definition(definition_fields()),
        build_agent_task(task_fields()),
    )


# --------------------------------------------------------------------------
# FR-AGENTIC-010 - idempotent submission and checkpoint before execution
# --------------------------------------------------------------------------


def test_submission_persists_an_initial_checkpoint_before_execution() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    assert run.state == "submitted"
    assert run.current_node == "collect_briefs"
    assert run.sequence == 0
    checkpoints = store.list_checkpoints(task.task_id)
    assert len(checkpoints) == 1
    assert checkpoints[0].state == "submitted"


def test_repeated_idempotency_key_returns_the_original_run() -> None:
    store, definition, task = _fixture()
    first = submit_task(store, definition, task, at_time=NOW)
    second = submit_task(store, definition, task, at_time=NOW)
    assert second.run_id == first.run_id
    assert len(store.list_checkpoints(task.task_id)) == 1


def test_distinct_idempotency_keys_create_distinct_runs() -> None:
    store, definition, task = _fixture()
    other = build_agent_task(task_fields(idempotency_key="idem-orchestration-0002"))
    first = submit_task(store, definition, task, at_time=NOW)
    second = submit_task(store, definition, other, at_time=NOW)
    assert first.run_id != second.run_id


def test_workflow_name_mismatch_is_refused() -> None:
    store, definition, _ = _fixture()
    mismatched = build_agent_task(task_fields(workflow_name="other_workflow"))
    with pytest.raises(ValueError, match="task declares workflow"):
        submit_task(store, definition, mismatched, at_time=NOW)


def test_workflow_version_mismatch_is_refused() -> None:
    store, definition, _ = _fixture()
    mismatched = build_agent_task(task_fields(workflow_version="9.9.9"))
    with pytest.raises(ValueError, match="task declares version"):
        submit_task(store, definition, mismatched, at_time=NOW)


def test_already_passed_deadline_is_refused_at_submission() -> None:
    store, definition, task = _fixture()
    with pytest.raises(ValueError, match="deadline has already passed"):
        submit_task(store, definition, task, at_time=NOW + timedelta(hours=2))


def test_policy_port_can_deny_submission() -> None:
    class DenyAll:
        def authorize_task(self, task, action) -> bool:
            del task, action
            return False

    store, definition, task = _fixture()
    with pytest.raises(ValueError, match="policy denied"):
        submit_task(store, definition, task, policy=DenyAll(), at_time=NOW)


def test_context_port_is_assembled_at_submission() -> None:
    calls: list[str] = []

    class RecordingContext:
        def assemble_task_context(self, task):
            calls.append(task.task_id)
            return {"instrument": "EURUSD"}

    store, definition, task = _fixture()
    submit_task(store, definition, task, context=RecordingContext(), at_time=NOW)
    assert calls == [task.task_id]


# --------------------------------------------------------------------------
# FR-AGENTIC-011 - bounded routing, cancellation, expiry, resume
# --------------------------------------------------------------------------


def test_resume_moves_a_submitted_run_to_running() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    resumed = resume_task(store, run.run_id, task, at_time=NOW + timedelta(minutes=1))
    assert resumed.state == "running"
    assert resumed.sequence == 1
    assert resumed.revision == 1
    assert len(store.list_checkpoints(task.task_id)) == 2


def test_cancellation_is_terminal_with_a_reason() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    cancelled = cancel_task(store, run.run_id, task, at_time=NOW)
    assert cancelled.state == "cancelled"
    assert cancelled.terminal_reason == "OPERATOR_CANCELLED"
    assert is_terminal_state(cancelled.state)


def test_expiry_requires_the_deadline_to_have_passed() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    with pytest.raises(ValueError, match="has not reached its deadline"):
        expire_task(store, run.run_id, task, at_time=NOW)


def test_expiry_after_the_deadline_is_terminal() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    expired = expire_task(store, run.run_id, task, at_time=NOW + timedelta(hours=2))
    assert expired.state == "expired"
    assert expired.terminal_reason == "DEADLINE_EXCEEDED"


def test_resume_after_the_deadline_is_refused() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    with pytest.raises(ValueError, match="passed its deadline"):
        resume_task(store, run.run_id, task, at_time=NOW + timedelta(hours=2))


def test_expected_version_guard_detects_concurrent_modification() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    resume_task(store, run.run_id, task, at_time=NOW)
    # The stale handle still carries revision 0 and must not overwrite.
    with pytest.raises(ValueError, match="concurrent modification"):
        store.save_run(run, 0)


def test_unknown_run_is_refused() -> None:
    store, _, task = _fixture()
    with pytest.raises(ValueError, match="unknown Agentic run"):
        resume_task(store, "id-" + "0" * 64, task, at_time=NOW)


def test_saving_an_unknown_run_is_refused() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    orphan = run.model_copy(update={"run_id": "id-" + "1" * 64})
    with pytest.raises(ValueError, match="unknown Agentic run"):
        store.save_run(orphan, 0)


def test_entry_node_must_be_declared() -> None:
    with pytest.raises(ValidationError):
        build_workflow_definition(definition_fields(entry_node="unknown_node"))


def test_duplicate_nodes_are_rejected() -> None:
    with pytest.raises(ValidationError):
        build_workflow_definition(definition_fields(nodes=("a", "a")))


def test_empty_node_set_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_workflow_definition(definition_fields(nodes=(), entry_node="a"))


def test_non_positive_bounds_are_rejected() -> None:
    with pytest.raises(ValidationError):
        build_workflow_definition(definition_fields(max_fan_out=0))


def test_zero_retries_is_a_valid_bound() -> None:
    definition = build_workflow_definition(definition_fields(max_retries=0))
    assert definition.max_retries == 0


def test_negative_retries_are_rejected() -> None:
    with pytest.raises(ValidationError):
        build_workflow_definition(definition_fields(max_retries=-1))


# --------------------------------------------------------------------------
# FR-AGENTIC-012 - terminal states never resume
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state",
    ["succeeded", "refused", "failed", "cancelled", "expired"],
)
def test_terminal_states_are_recognised(state) -> None:
    assert is_terminal_state(state)


@pytest.mark.parametrize("state", ["submitted", "running", "waiting_human"])
def test_live_states_are_not_terminal(state) -> None:
    assert not is_terminal_state(state)


def test_terminal_run_cannot_resume() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    cancel_task(store, run.run_id, task, at_time=NOW)
    with pytest.raises(ValueError, match="cannot resume"):
        resume_task(store, run.run_id, task, at_time=NOW)


def test_terminal_run_cannot_cancel_again() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    cancel_task(store, run.run_id, task, at_time=NOW)
    with pytest.raises(ValueError, match=r"cannot resume|terminal"):
        cancel_task(store, run.run_id, task, at_time=NOW)


@pytest.mark.parametrize("terminal", ["succeeded", "cancelled", "expired"])
def test_transition_from_a_terminal_state_is_rejected(terminal) -> None:
    with pytest.raises(ValueError, match="cannot transition"):
        validate_transition(terminal, "running")


def test_unpermitted_transition_is_rejected() -> None:
    with pytest.raises(ValueError, match="is not permitted"):
        validate_transition("submitted", "waiting_human")


def test_permitted_transition_is_returned() -> None:
    assert validate_transition("running", "waiting_human") == "waiting_human"


def test_terminal_state_requires_a_reason() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    # model_copy skips validation, so re-validate explicitly to exercise the rule.
    invalid = {**run.model_dump(), "state": "cancelled", "terminal_reason": None}
    with pytest.raises(ValidationError):
        type(run).model_validate(invalid)


def test_live_state_must_not_carry_a_terminal_reason() -> None:
    store, definition, task = _fixture()
    run = submit_task(store, definition, task, at_time=NOW)
    invalid = {**run.model_dump(), "state": "running", "terminal_reason": "X"}
    with pytest.raises(ValidationError):
        type(run).model_validate(invalid)


# --------------------------------------------------------------------------
# Migrations - declared, checksummed, and additive
# --------------------------------------------------------------------------


def test_migration_statements_are_additive_and_namespaced() -> None:
    statements = get_agentic_migration_statements()
    assert statements
    for statement in statements:
        assert "IF NOT EXISTS" in statement
        assert "agentic_" in statement
        assert "DROP" not in statement.upper()


def test_migration_request_is_built_for_the_agentic_domain() -> None:
    request = build_agentic_migration_request(generate_id("req"))
    assert request is not None
