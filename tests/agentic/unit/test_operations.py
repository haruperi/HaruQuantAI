"""Unit tests for FEAT-AGT-21 Observability, Incidents, and Operational Control.

Covers FR-AGENTIC-061 (correlated redacted telemetry across every required
span), FR-AGENTIC-062 (deterministic containment and evidence preservation for
nine incident kinds), and FR-AGENTIC-063 (replay uses immutable references, an
isolated environment, and repeats no external side effect).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_task,
    build_in_memory_memory_store,
    store_memory,
)
from app.agentic.operations import (
    INCIDENT_KINDS,
    REQUIRED_SPAN_KINDS,
    AgenticTrace,
    build_agentic_trace,
    build_in_memory_operations_store,
    build_incident_record,
    build_operations_migration_request,
    build_replay_request,
    get_operations_migration_statements,
    get_quarantined_roles,
    get_run_incidents,
    get_run_trace,
    quarantine_agent,
    replay_run,
    required_containment,
    verify_references,
)
from app.agentic.operations.models import (
    ReplayOutcome,
    build_replay_outcome,
    derive_trace_hash,
    missing_span_kinds,
    unknown_span_kinds,
)
from app.agentic.operations.service import SPAN_KEY
from app.agentic.orchestration import (
    build_in_memory_workflow_store,
    build_workflow_definition,
    cancel_task,
    submit_task,
)
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import NOW

WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"
TASK_ID = derive_stable_id("id", "task-operations")
ROLE_ID = "technical_analyst"


def _definition_fields(**overrides: object) -> dict[str, object]:
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


def _task(**overrides: object):
    data: dict[str, object] = {
        "created_at": NOW,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "causation_id": None,
        "task_id": TASK_ID,
        "workflow_name": WORKFLOW_NAME,
        "workflow_version": WORKFLOW_VERSION,
        "objective": "Assess EURUSD H1 trend evidence.",
        "input_refs": ("evidence-market-1",),
        "principal_id": "operator-owner",
        "scope": {"environment": "sandbox"},
        "deadline_at": NOW + timedelta(minutes=30),
        "idempotency_key": "idem-operations-0001",
        "budgets": {"cost": Decimal("5.00")},
    }
    data.update(overrides)
    return build_agent_task(data)


def _emit(store, kinds=None, task_id: str = TASK_ID, **extra: str):
    """Write one audit record per span kind, as an emitter would."""
    for kind in sorted(REQUIRED_SPAN_KINDS if kinds is None else kinds):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span was emitted"}
        if kind == "cost":
            content["cost"] = extra.get("cost", "0.25")
        store_memory(
            store,
            "audit",
            task_id,
            ROLE_ID,
            content,
            {"environment": "sandbox"},
            "audit-730d",
            at_time=NOW,
        )
    return store


def _memory(**kwargs):
    return _emit(build_in_memory_memory_store(), **kwargs)


def _running_run(store=None, task=None):
    workflow_store = store or build_in_memory_workflow_store()
    return (
        workflow_store,
        submit_task(
            workflow_store,
            build_workflow_definition(_definition_fields()),
            task or _task(),
            at_time=NOW,
        ),
    )


def _trace(**overrides: object):
    defaults: dict[str, object] = {
        "memory_store": _memory(),
        "task_id": TASK_ID,
        "run_id": "run-a",
        "correlation_id": "cor-a",
        "at_time": NOW,
    }
    defaults.update(overrides)
    return get_run_trace(**defaults)  # type: ignore[arg-type]


def _incident_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "incident_id": "incident-a",
        "task_id": TASK_ID,
        "run_id": "run-a",
        "correlation_id": "cor-a",
        "kind": "injection",
        "trigger": "A retrieved document asked the role to ignore its rules.",
        "containment_action": "quarantine_and_cancel",
        "contained_state": "cancelled",
        "quarantined_role_id": ROLE_ID,
        "preserved_evidence_refs": ("agentic.memory:record-a",),
        "checkpoint_ref": "agentic.checkpoint:run-a:3",
        "detected_at": NOW.isoformat(),
    }
    data.update(overrides)
    return data


def _replay_fields(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "replay_id": "replay-a",
        "run_id": "run-a",
        "task_id": TASK_ID,
        "environment": "sandbox",
        "reference_hashes": {"record-a": "a" * 64},
        "requested_by": "operator-owner",
        "requested_at": NOW.isoformat(),
    }
    data.update(overrides)
    return data


# --------------------------------------------------------------------------
# The feature invokes no model and redacts nothing itself
# --------------------------------------------------------------------------


def test_the_package_declares_no_role_and_calls_no_model() -> None:
    from pathlib import Path

    package = Path("app/agentic/operations")
    assert not (package / "prompt.md").exists()
    assert not (package / "agent.py").exists()
    sources = "".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    for forbidden in ("execute_node", "AdkRuntime", "ModelProfile"):
        assert forbidden not in sources


def test_the_package_defines_no_second_redactor() -> None:
    from pathlib import Path

    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic/operations").glob("*.py")
    )
    # Redaction happens once, at the FEAT-AGT-06 memory boundary. A second
    # definition here would be a second answer to what counts as a secret.
    for forbidden in ("redact_mapping_value", "redact_text_value", "RedactionPolicy"):
        assert forbidden not in sources


# --------------------------------------------------------------------------
# FR-AGENTIC-061 - correlated, redacted, complete telemetry
# --------------------------------------------------------------------------


def test_the_required_span_kinds_are_exactly_ten() -> None:
    assert {
        "agent",
        "approval",
        "cost",
        "failure",
        "guardrail",
        "handoff",
        "model",
        "state_transition",
        "tool",
        "workflow",
    } == REQUIRED_SPAN_KINDS


def test_a_complete_run_assembles_a_trace() -> None:
    trace = _trace()
    assert set(trace.spans) == REQUIRED_SPAN_KINDS
    assert trace.record_count == len(REQUIRED_SPAN_KINDS)
    assert trace.correlation_id == "cor-a"
    assert trace.trace_hash


@pytest.mark.parametrize("dropped", sorted(REQUIRED_SPAN_KINDS))
def test_a_run_missing_any_span_cannot_be_traced(dropped) -> None:
    partial = REQUIRED_SPAN_KINDS - {dropped}
    with pytest.raises(ValueError, match=dropped):
        _trace(memory_store=_memory(kinds=partial))


def test_an_unlabelled_record_cannot_be_placed() -> None:
    store = _memory()
    store_memory(
        store,
        "audit",
        TASK_ID,
        ROLE_ID,
        {"detail": "an emitter that never declared its span"},
        {"environment": "sandbox"},
        "audit-730d",
        at_time=NOW,
    )
    trace = _trace(memory_store=store)
    # It is counted, because it happened, but it covers no span.
    assert trace.record_count == len(REQUIRED_SPAN_KINDS) + 1
    assert set(trace.spans) == REQUIRED_SPAN_KINDS


def test_a_span_nobody_agreed_to_does_not_widen_the_trace() -> None:
    store = _memory()
    store_memory(
        store,
        "audit",
        TASK_ID,
        ROLE_ID,
        {SPAN_KEY: "vibes", "detail": "an emitter inventing a span"},
        {"environment": "sandbox"},
        "audit-730d",
        at_time=NOW,
    )
    trace = _trace(memory_store=store)
    assert "vibes" not in trace.spans
    assert set(trace.spans) == REQUIRED_SPAN_KINDS


def test_a_trace_missing_a_span_is_unrepresentable() -> None:
    trace = _trace()
    partial = {k: v for k, v in trace.spans.items() if k != "approval"}
    with pytest.raises(ValidationError, match="every required span kind"):
        build_agentic_trace({**trace.model_dump(), "spans": partial})


def test_a_trace_carrying_an_unknown_span_is_unrepresentable() -> None:
    trace = _trace()
    with pytest.raises(ValidationError, match="unrecognized span kinds"):
        build_agentic_trace(
            {**trace.model_dump(), "spans": {**trace.spans, "vibes": "x"}},
        )


def test_missing_and_unknown_span_kinds_are_reported_separately() -> None:
    assert "approval" in missing_span_kinds({"tool": "x"})
    assert unknown_span_kinds({"vibes": "x"}) == ("vibes",)
    assert unknown_span_kinds(dict.fromkeys(REQUIRED_SPAN_KINDS, "x")) == ()


def test_redaction_is_inherited_from_the_memory_boundary() -> None:
    store = _memory()
    store_memory(
        store,
        "audit",
        TASK_ID,
        ROLE_ID,
        {SPAN_KEY: "tool", "api_key": "super-secret-value"},  # pragma: allowlist secret
        {"environment": "sandbox"},
        "audit-730d",
        at_time=NOW,
    )
    trace = _trace(memory_store=store)
    assert trace.redacted_paths
    assert "super-secret-value" not in str(trace.model_dump())


def test_the_observed_cost_is_summed_from_cost_spans() -> None:
    trace = _trace(memory_store=_memory(cost="1.50"))
    assert trace.observed_cost == Decimal("1.50")


def test_an_unreadable_cost_does_not_fabricate_a_number() -> None:
    store = build_in_memory_memory_store()
    for kind in sorted(REQUIRED_SPAN_KINDS):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span"}
        if kind == "cost":
            content["cost"] = "not-a-number"
        store_memory(
            store,
            "audit",
            TASK_ID,
            ROLE_ID,
            content,
            {"environment": "sandbox"},
            "audit-730d",
            at_time=NOW,
        )
    trace = _trace(memory_store=store)
    assert trace.observed_cost == Decimal(0)
    assert "cost" in trace.spans


def test_a_negative_cost_is_unrepresentable() -> None:
    trace = _trace()
    with pytest.raises(ValidationError, match="negative cost"):
        build_agentic_trace({**trace.model_dump(), "observed_cost": Decimal(-1)})


def test_the_trace_digest_covers_the_whole_trace() -> None:
    trace = _trace()
    altered = {**trace.model_dump(), "record_count": 99}
    assert derive_trace_hash(altered) != trace.trace_hash


def test_an_assembled_trace_can_be_persisted() -> None:
    store = build_in_memory_operations_store()
    trace = _trace(operations_store=store)
    assert store.load_trace(trace.trace_hash) is not None


# --------------------------------------------------------------------------
# FR-AGENTIC-062 - nine kinds, deterministic containment, preserved evidence
# --------------------------------------------------------------------------


def test_the_incident_kinds_are_exactly_nine() -> None:
    assert {
        "cost",
        "data_poisoning",
        "drift",
        "injection",
        "privilege",
        "provider",
        "runaway_loop",
        "sandbox",
        "schema",
    } == INCIDENT_KINDS


@pytest.mark.parametrize(
    ("kind", "action"),
    [
        ("injection", "quarantine_and_cancel"),
        ("privilege", "quarantine_and_cancel"),
        ("data_poisoning", "quarantine_and_cancel"),
        ("sandbox", "quarantine_and_cancel"),
        ("drift", "quarantine"),
        ("cost", "cancel"),
        ("provider", "cancel"),
        ("runaway_loop", "cancel"),
        ("schema", "cancel"),
    ],
)
def test_containment_follows_from_the_kind(kind, action) -> None:
    assert required_containment(kind) == action


def test_every_incident_kind_has_a_containment() -> None:
    for kind in INCIDENT_KINDS:
        assert required_containment(kind)


def test_an_unrecognized_kind_has_no_containment() -> None:
    with pytest.raises(ValueError, match="not a recognized incident kind"):
        required_containment("vibes")


def test_an_injection_incident_cancels_and_quarantines() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    task = _task()
    incident = quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        task,
        "injection",
        "A retrieved document asked the role to ignore its rules.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
        at_time=NOW,
    )
    assert incident.containment_action == "quarantine_and_cancel"
    assert incident.contained_state == "cancelled"
    assert incident.quarantined_role_id == ROLE_ID
    assert workflow_store.load_run(run.run_id).state == "cancelled"


def test_a_drift_incident_quarantines_without_cancelling() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    incident = quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        _task(),
        "drift",
        "The role's outputs diverged from its evaluated baseline.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
        at_time=NOW,
    )
    assert incident.containment_action == "quarantine"
    assert incident.contained_state == "submitted"
    assert workflow_store.load_run(run.run_id).state == "submitted"


def test_a_cost_incident_cancels_without_quarantining() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    incident = quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        _task(),
        "cost",
        "The run exceeded its declared cost ceiling.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
        at_time=NOW,
    )
    assert incident.containment_action == "cancel"
    assert incident.quarantined_role_id is None
    assert get_quarantined_roles(store) == ()


def test_containment_cannot_disagree_with_the_kind() -> None:
    with pytest.raises(ValidationError, match="requires 'cancel' containment"):
        build_incident_record(
            _incident_fields(
                kind="cost",
                containment_action="quarantine_and_cancel",
            ),
        )


def test_a_quarantine_must_name_the_role_it_quarantined() -> None:
    with pytest.raises(ValidationError, match="must name the role"):
        build_incident_record(_incident_fields(quarantined_role_id=None))


def test_a_cancel_only_incident_may_not_name_a_quarantined_role() -> None:
    with pytest.raises(ValidationError, match="quarantines no role"):
        build_incident_record(
            _incident_fields(
                kind="schema",
                containment_action="cancel",
                quarantined_role_id=ROLE_ID,
            ),
        )


def test_containment_without_preserved_evidence_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="is required"):
        build_incident_record(_incident_fields(preserved_evidence_refs=()))


def test_an_incident_preserves_its_checkpoint() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    incident = quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        _task(),
        "schema",
        "The model returned output the schema rejected.",
        ROLE_ID,
        ("agentic.memory:record-a", "agentic.memory:record-b"),
        f"agentic.checkpoint:{run.run_id}:2",
        at_time=NOW,
    )
    assert incident.checkpoint_ref.endswith(":2")
    assert len(incident.preserved_evidence_refs) == 2


def test_the_same_incident_kind_cannot_be_recorded_twice() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    task = _task()
    args = (
        store,
        workflow_store,
        run.run_id,
        task,
        "drift",
        "The role's outputs diverged from its evaluated baseline.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
    )
    quarantine_agent(*args, at_time=NOW)
    with pytest.raises(ValueError, match="not replaceable"):
        quarantine_agent(*args, at_time=NOW)


def test_an_already_terminal_run_is_recorded_against_its_real_state() -> None:
    workflow_store, run = _running_run()
    task = _task()
    cancel_task(workflow_store, run.run_id, task, at_time=NOW)
    store = build_in_memory_operations_store()
    incident = quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        task,
        "provider",
        "The provider returned an unrecoverable error.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
        at_time=NOW,
    )
    assert incident.contained_state == "cancelled"


def test_an_unknown_run_cannot_be_contained() -> None:
    store = build_in_memory_operations_store()
    workflow_store = build_in_memory_workflow_store()
    with pytest.raises(ValueError, match="unknown and cannot be contained"):
        quarantine_agent(
            store,
            workflow_store,
            "run-missing",
            _task(),
            "cost",
            "The run exceeded its declared cost ceiling.",
            ROLE_ID,
            ("agentic.memory:record-a",),
            "agentic.checkpoint:run-missing:1",
            at_time=NOW,
        )


def test_incidents_are_listed_per_run() -> None:
    workflow_store, run = _running_run()
    store = build_in_memory_operations_store()
    quarantine_agent(
        store,
        workflow_store,
        run.run_id,
        _task(),
        "drift",
        "The role's outputs diverged from its evaluated baseline.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run.run_id}:1",
        at_time=NOW,
    )
    assert len(get_run_incidents(store, run.run_id)) == 1
    assert get_run_incidents(store, "run-other") == ()
    assert get_quarantined_roles(store) == (ROLE_ID,)


# --------------------------------------------------------------------------
# FR-AGENTIC-063 - immutable references, isolated environment, no side effects
# --------------------------------------------------------------------------


def test_a_replay_may_only_target_the_sandbox() -> None:
    with pytest.raises(ValidationError):
        build_replay_request(_replay_fields(environment="production"))


def test_a_replay_must_name_its_references() -> None:
    with pytest.raises(ValidationError, match="must name the immutable references"):
        build_replay_request(_replay_fields(reference_hashes={}))


def test_a_replay_against_current_references_is_validated() -> None:
    memory = _memory()
    records = tuple(
        record
        for record in _stored_records(memory)
        if record.content.get(SPAN_KEY) == "tool"
    )
    request = build_replay_request(
        _replay_fields(
            reference_hashes={records[0].record_id: records[0].content_hash},
        ),
    )
    outcome = replay_run(build_in_memory_operations_store(), memory, request, NOW)
    assert outcome.executed is False
    assert outcome.side_effects_attempted == 0
    assert outcome.environment == "sandbox"


def test_a_replay_against_an_unknown_reference_is_refused() -> None:
    memory = _memory()
    request = build_replay_request(_replay_fields())
    with pytest.raises(ValueError, match="not recorded"):
        replay_run(build_in_memory_operations_store(), memory, request, NOW)


def test_a_replay_against_mutated_evidence_is_refused() -> None:
    memory = _memory()
    record = _stored_records(memory)[0]
    request = build_replay_request(
        _replay_fields(reference_hashes={record.record_id: "b" * 64}),
    )
    with pytest.raises(ValueError, match="no longer carry the digest"):
        replay_run(build_in_memory_operations_store(), memory, request, NOW)


def test_verify_references_reports_unknown_and_changed_separately() -> None:
    unknown = verify_references({"a": "1"}, {})
    assert unknown is not None
    assert "not recorded" in unknown
    changed = verify_references({"a": "1"}, {"a": "2"})
    assert changed is not None
    assert "no longer carry the digest" in changed
    assert verify_references({"a": "1"}, {"a": "1"}) is None


def test_an_outcome_reporting_a_side_effect_is_unrepresentable() -> None:
    with pytest.raises(ValidationError, match="attempted an external side effect"):
        build_replay_outcome(
            {
                "replay_id": "replay-a",
                "run_id": "run-a",
                "environment": "sandbox",
                "verified_references": ("record-a",),
                "side_effects_attempted": 1,
                "executed": True,
                "completed_at": NOW.isoformat(),
            },
        )


def test_the_outcome_carries_no_execution_or_write_path() -> None:
    fields = set(ReplayOutcome.model_fields)
    for forbidden in ("tool_port", "receiver", "adapter", "writer", "store"):
        assert forbidden not in fields


def test_the_same_replay_cannot_be_recorded_twice() -> None:
    memory = _memory()
    record = _stored_records(memory)[0]
    store = build_in_memory_operations_store()
    request = build_replay_request(
        _replay_fields(reference_hashes={record.record_id: record.content_hash}),
    )
    replay_run(store, memory, request, NOW)
    with pytest.raises(ValueError, match="already recorded"):
        replay_run(store, memory, request, NOW)


# --------------------------------------------------------------------------
# The durable store carries the same rules
# --------------------------------------------------------------------------


def test_the_incident_table_permits_one_incident_per_kind_per_run() -> None:
    statements = get_operations_migration_statements()
    incidents = next(
        statement
        for statement in statements
        if "agentic_operations_incidents" in statement and "CREATE TABLE" in statement
    )
    assert "UNIQUE (run_id, correlation_id, kind)" in incidents


def test_the_trace_table_is_keyed_on_the_content_digest() -> None:
    statements = get_operations_migration_statements()
    traces = next(
        statement
        for statement in statements
        if "agentic_operations_traces" in statement and "CREATE TABLE" in statement
    )
    assert "trace_hash TEXT PRIMARY KEY" in traces


def test_the_migration_request_is_declared_not_executed() -> None:
    from pathlib import Path

    assert build_operations_migration_request(generate_id("req")) is not None
    source = Path("app/agentic/migrations/operations.py").read_text(encoding="utf-8")
    for forbidden in ("connect(", "execute(", "cursor"):
        assert forbidden not in source


def test_the_trace_contract_is_exported_at_the_package_root() -> None:
    assert AgenticTrace.__name__ == "AgenticTrace"


def _stored_records(memory):
    """Return the audit records a memory store currently holds."""
    from app.agentic import retrieve_memory

    return retrieve_memory(memory, "audit", TASK_ID, NOW)
