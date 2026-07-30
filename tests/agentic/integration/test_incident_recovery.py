"""Integration evidence for `WF-AGT-010` — incident and recovery.

Exercises the path an incident must traverse: a real submitted run, audit
records written through the governed `FEAT-AGT-06` memory store and redacted at
that boundary, a correlated trace assembled from them, deterministic
containment through the normal `FEAT-AGT-04` cancellation path, evidence and
checkpoint preserved rather than discarded, and a replay that is validated
against immutable references and executes nothing.

The orchestration and memory stores are the real in-memory doubles those
features ship, not stand-ins written here: the run really transitions, the
audit records are really redacted, and a terminal run really refuses to resume.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_task,
    build_in_memory_memory_store,
    retrieve_memory,
    store_memory,
)
from app.agentic.operations import (
    REQUIRED_SPAN_KINDS,
    build_in_memory_operations_store,
    build_replay_request,
    get_quarantined_roles,
    get_run_incidents,
    get_run_trace,
    quarantine_agent,
    replay_run,
    required_containment,
)
from app.agentic.operations.service import SPAN_KEY
from app.agentic.orchestration import (
    build_in_memory_workflow_store,
    build_workflow_definition,
    is_terminal_state,
    resume_task,
    submit_task,
)
from app.utils import derive_stable_id, generate_id

from tests.agentic.fixtures import NOW

WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"
TASK_ID = derive_stable_id("id", "task-incident-recovery")
ROLE_ID = "technical_analyst"


def _definition():
    return build_workflow_definition(
        {
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
        },
    )


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
        "idempotency_key": "idem-incident-recovery",
        "budgets": {"cost": Decimal("5.00")},
    }
    data.update(overrides)
    return build_agent_task(data)


def _emit_full_run(memory, *, poisoned: bool = False):
    """Write one audit record per required span, as the firm's emitters do."""
    for kind in sorted(REQUIRED_SPAN_KINDS):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span was emitted"}
        if kind == "cost":
            content["cost"] = "0.40"
        if poisoned and kind == "tool":
            # A real emitter would carry the credential through; the memory
            # boundary is what stops it reaching the store.
            content["api_key"] = "super-secret-value"  # pragma: allowlist secret
        store_memory(
            memory,
            "audit",
            TASK_ID,
            ROLE_ID,
            content,
            {"environment": "sandbox"},
            "audit-730d",
            at_time=NOW,
        )
    return memory


def test_an_incident_traverses_the_full_governed_path() -> None:
    # 1. A real run is submitted through the normal orchestration path.
    workflow_store = build_in_memory_workflow_store()
    task = _task()
    run = submit_task(workflow_store, _definition(), task, at_time=NOW)
    assert not is_terminal_state(run.state)

    # 2. The firm's emitters write audit records through the governed store,
    #    and the memory boundary redacts before anything is persisted.
    memory = _emit_full_run(build_in_memory_memory_store(), poisoned=True)
    records = retrieve_memory(memory, "audit", TASK_ID, NOW)
    assert len(records) == len(REQUIRED_SPAN_KINDS)
    assert "super-secret-value" not in str([r.content for r in records])

    # 3. A correlated trace assembles from exactly those records.
    operations = build_in_memory_operations_store()
    trace = get_run_trace(
        memory,
        TASK_ID,
        run.run_id,
        task.correlation_id,
        operations_store=operations,
        at_time=NOW,
    )
    assert set(trace.spans) == REQUIRED_SPAN_KINDS
    assert trace.redacted_paths
    assert trace.observed_cost == Decimal("0.40")
    assert operations.load_trace(trace.trace_hash) is not None

    # 4. Containment is derived from the kind and applied through the normal
    #    cancellation path; evidence and checkpoint are preserved.
    incident = quarantine_agent(
        operations,
        workflow_store,
        run.run_id,
        task,
        "injection",
        "A retrieved document asked the role to ignore its rules.",
        ROLE_ID,
        tuple(record.record_id for record in records[:2]),
        f"agentic.checkpoint:{run.run_id}:{run.sequence}",
        correlation_id=task.correlation_id,
        at_time=NOW,
    )
    assert incident.containment_action == required_containment("injection")
    assert incident.contained_state == "cancelled"
    assert incident.quarantined_role_id == ROLE_ID
    assert len(incident.preserved_evidence_refs) == 2
    assert incident.checkpoint_ref.startswith("agentic.checkpoint:")

    # 5. The run really is terminal, and terminal work cannot resume.
    contained = workflow_store.load_run(run.run_id)
    assert is_terminal_state(contained.state)
    with pytest.raises(ValueError, match="cannot resume under the same task identity"):
        resume_task(workflow_store, run.run_id, task, at_time=NOW)

    # 6. Replay is validated against the preserved references and runs nothing.
    request = build_replay_request(
        {
            "replay_id": f"replay:{run.run_id}",
            "run_id": run.run_id,
            "task_id": TASK_ID,
            "environment": "sandbox",
            "reference_hashes": {
                record.record_id: record.content_hash for record in records[:2]
            },
            "requested_by": "operator-owner",
            "requested_at": NOW.isoformat(),
        },
    )
    outcome = replay_run(operations, memory, request, NOW)
    assert outcome.executed is False
    assert outcome.side_effects_attempted == 0
    assert len(outcome.verified_references) == 2


def test_the_incident_record_survives_the_run_it_contained() -> None:
    workflow_store = build_in_memory_workflow_store()
    task = _task()
    run = submit_task(workflow_store, _definition(), task, at_time=NOW)
    operations = build_in_memory_operations_store()
    memory = _emit_full_run(build_in_memory_memory_store())
    records = retrieve_memory(memory, "audit", TASK_ID, NOW)

    quarantine_agent(
        operations,
        workflow_store,
        run.run_id,
        task,
        "data_poisoning",
        "Retrieved evidence carried an instruction pattern.",
        ROLE_ID,
        (records[0].record_id,),
        f"agentic.checkpoint:{run.run_id}:{run.sequence}",
        at_time=NOW,
    )
    # The run is terminal, but the incident and its evidence remain readable.
    assert is_terminal_state(workflow_store.load_run(run.run_id).state)
    preserved = get_run_incidents(operations, run.run_id)
    assert len(preserved) == 1
    assert preserved[0].preserved_evidence_refs == (records[0].record_id,)
    assert get_quarantined_roles(operations) == (ROLE_ID,)


def test_a_run_whose_emitters_stayed_silent_cannot_be_traced() -> None:
    # Completeness is a property of the assembled trace, not an aspiration:
    # a run that emitted only some spans produces no trace at all.
    memory = build_in_memory_memory_store()
    store_memory(
        memory,
        "audit",
        TASK_ID,
        ROLE_ID,
        {SPAN_KEY: "tool", "detail": "the only span this run emitted"},
        {"environment": "sandbox"},
        "audit-730d",
        at_time=NOW,
    )
    with pytest.raises(ValueError, match="missing"):
        get_run_trace(memory, TASK_ID, "run-a", "cor-a", at_time=NOW)


def test_a_replay_against_evidence_that_changed_is_refused() -> None:
    memory = _emit_full_run(build_in_memory_memory_store())
    records = retrieve_memory(memory, "audit", TASK_ID, NOW)
    request = build_replay_request(
        {
            "replay_id": "replay-mutated",
            "run_id": "run-a",
            "task_id": TASK_ID,
            "environment": "sandbox",
            # The digest a caller believes; the store says otherwise.
            "reference_hashes": {records[0].record_id: "c" * 64},
            "requested_by": "operator-owner",
            "requested_at": NOW.isoformat(),
        },
    )
    with pytest.raises(ValueError, match="no longer carry the digest"):
        replay_run(build_in_memory_operations_store(), memory, request, NOW)


def test_operations_reaches_no_receiver_and_executes_no_replay() -> None:
    from pathlib import Path

    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic/operations").glob("*.py")
    )
    for forbidden in (
        "app.services.risk",
        "app.services.trading",
        "app.services.brokers",
        "app.services.strategy",
        "dispatch_order_intent",
    ):
        assert forbidden not in sources

    # Data's migration builders are the one permitted service import.
    importers = {
        path.name
        for path in Path("app/agentic/operations").glob("*.py")
        if "app.services" in path.read_text(encoding="utf-8")
    }
    assert importers == {"migrations.py"}
