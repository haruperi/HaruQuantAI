"""Executable FEAT-AGT-21 operations usage example.

Demonstrates every registered public operation through the documented API. The
orchestration and memory stores are the deterministic in-memory doubles those
features ship, so nothing is written to disk, no network call occurs, and
Agentic holds no credential.

The point of the demonstration is that observability and containment are
deterministic. A trace either covers every required span or does not exist,
containment follows from the incident kind through a fixed table, and a replay
proves its references still hold and then executes nothing.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    build_agent_task,
    build_in_memory_memory_store,
    retrieve_memory,
    store_memory,
)
from app.agentic.operations import (
    INCIDENT_KINDS,
    REQUIRED_SPAN_KINDS,
    build_in_memory_operations_store,
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
from app.agentic.operations.models import ReplayOutcome, build_replay_outcome
from app.agentic.operations.service import SPAN_KEY
from app.agentic.orchestration import (
    build_in_memory_workflow_store,
    build_workflow_definition,
    is_terminal_state,
    submit_task,
)
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-operations-usage")
WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"
ROLE_ID = "technical_analyst"

BANNER = "=" * 88


def heading(requirement: str, statement: str) -> None:
    """Print one requirement heading.

    Args:
        requirement: Functional requirement identifier.
        statement: What the requirement obliges.
    """
    print(f"\n{BANNER}\n{requirement}: {statement}\n{BANNER}")


def definition():
    """Build the bounded workflow declaration.

    Returns:
        A validated immutable workflow definition.
    """
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


def task(**overrides: object):
    """Build the bounded governed task.

    Args:
        **overrides: Optional field overrides.

    Returns:
        A validated immutable agent task.
    """
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
        "idempotency_key": "idem-operations-usage",
        "budgets": {"cost": Decimal("5.00")},
    }
    data.update(overrides)
    return build_agent_task(data)


def emit(memory, kinds=None, *, poisoned: bool = False):
    """Write one audit record per span kind, as the firm's emitters do.

    Args:
        memory: Injected governed memory store.
        kinds: Optional subset of span kinds to emit.
        poisoned: Whether one record carries a credential.

    Returns:
        The memory store.
    """
    for kind in sorted(REQUIRED_SPAN_KINDS if kinds is None else kinds):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span was emitted"}
        if kind == "cost":
            content["cost"] = "0.40"
        if poisoned and kind == "tool":
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


def fr_agentic_061() -> None:
    """Demonstrate correlated, redacted, complete telemetry."""
    heading(
        "FR-AGENTIC-061",
        "Every workflow, agent, model, tool, handoff, guardrail, approval, "
        "state transition, cost, and failure emits correlated redacted "
        "telemetry.",
    )

    print(f"  required spans: {sorted(REQUIRED_SPAN_KINDS)}")

    memory = emit(build_in_memory_memory_store(), poisoned=True)
    operations = build_in_memory_operations_store()
    current = task()
    trace = get_run_trace(
        memory,
        TASK_ID,
        "run-usage-a",
        current.correlation_id,
        operations_store=operations,
        at_time=NOW,
    )
    print(f"  spans covered:  {len(trace.spans)}")
    print(f"  records read:   {trace.record_count}")
    print(f"  observed cost:  {trace.observed_cost}")
    print(f"  correlation:    {trace.correlation_id}")
    print(f"  trace digest:   {trace.trace_hash}")

    print("\n  Redaction is inherited from the memory boundary, not redone here:")
    print(f"    redacted paths:      {trace.redacted_paths}")
    print(f"    secret in the trace: {'super-secret-value' in str(trace.model_dump())}")

    print("\n  A run that emitted only some spans produces no trace at all:")
    for dropped in ("approval", "guardrail", "failure"):
        partial = REQUIRED_SPAN_KINDS - {dropped}
        try:
            get_run_trace(
                emit(build_in_memory_memory_store(), partial),
                TASK_ID,
                "run-usage-b",
                "cor-b",
                at_time=NOW,
            )
            verdict = "ERROR: an incomplete trace was assembled"
        except ValueError as error:
            verdict = str(error)
        print(f"    without {dropped:<12} -> {verdict}")

    print("\n  An unlabelled or invented span does not widen the contract:")
    extra = emit(build_in_memory_memory_store())
    for content in (
        {"detail": "an emitter that never declared its span"},
        {SPAN_KEY: "vibes", "detail": "an emitter inventing a span"},
    ):
        store_memory(
            extra,
            "audit",
            TASK_ID,
            ROLE_ID,
            content,
            {"environment": "sandbox"},
            "audit-730d",
            at_time=NOW,
        )
    widened = get_run_trace(extra, TASK_ID, "run-usage-c", "cor-c", at_time=NOW)
    print(f"    records read:  {widened.record_count}")
    print(f"    spans covered: {len(widened.spans)} (still the required ten)")


def fr_agentic_062() -> None:
    """Demonstrate deterministic containment and evidence preservation."""
    heading(
        "FR-AGENTIC-062",
        "Injection, privilege, data-poisoning, schema, drift, cost, "
        "runaway-loop, provider, or sandbox incidents trigger deterministic "
        "containment and evidence preservation.",
    )

    print(f"  incident kinds: {sorted(INCIDENT_KINDS)}")
    print("\n  Containment is a property of the kind, not a judgement:")
    for kind in sorted(INCIDENT_KINDS):
        print(f"    {kind:<16} -> {required_containment(kind)}")

    print("\n  Each kind applied to a real run:")
    for kind in sorted(INCIDENT_KINDS):
        workflow_store = build_in_memory_workflow_store()
        current = task(idempotency_key=f"idem-{kind}")
        run = submit_task(workflow_store, definition(), current, at_time=NOW)
        memory = emit(build_in_memory_memory_store())
        records = retrieve_memory(memory, "audit", TASK_ID, NOW)
        operations = build_in_memory_operations_store()
        incident = quarantine_agent(
            operations,
            workflow_store,
            run.run_id,
            current,
            kind,
            f"A {kind} condition was observed during the run.",
            ROLE_ID,
            (records[0].record_id,),
            f"agentic.checkpoint:{run.run_id}:{run.sequence}",
            at_time=NOW,
        )
        state = workflow_store.load_run(run.run_id).state
        print(
            f"    {kind:<16} action={incident.containment_action:<22} "
            f"run={state:<10} terminal={is_terminal_state(state)} "
            f"quarantined={incident.quarantined_role_id or 'none'}"
        )

    print("\n  Evidence and the checkpoint are preserved, never discarded:")
    workflow_store = build_in_memory_workflow_store()
    current = task(idempotency_key="idem-preserve")
    run = submit_task(workflow_store, definition(), current, at_time=NOW)
    memory = emit(build_in_memory_memory_store())
    records = retrieve_memory(memory, "audit", TASK_ID, NOW)
    operations = build_in_memory_operations_store()
    incident = quarantine_agent(
        operations,
        workflow_store,
        run.run_id,
        current,
        "injection",
        "A retrieved document asked the role to ignore its rules.",
        ROLE_ID,
        tuple(record.record_id for record in records[:3]),
        f"agentic.checkpoint:{run.run_id}:{run.sequence}",
        at_time=NOW,
    )
    print(f"    preserved evidence: {len(incident.preserved_evidence_refs)} references")
    print(f"    checkpoint:         {incident.checkpoint_ref}")
    print(f"    readable after:     {len(get_run_incidents(operations, run.run_id))}")
    print(f"    quarantined roles:  {get_quarantined_roles(operations)}")

    print("\n  The same incident kind cannot be recorded twice for one run:")
    try:
        quarantine_agent(
            operations,
            workflow_store,
            run.run_id,
            current,
            "injection",
            "A second report of the same incident.",
            ROLE_ID,
            ("agentic.memory:other",),
            "agentic.checkpoint:other",
            at_time=NOW,
        )
        verdict = "ERROR: the original evidence was replaced"
    except ValueError as error:
        verdict = str(error)
    print(f"    {verdict}")


def fr_agentic_063() -> None:
    """Demonstrate immutable references, isolation, and no side effects."""
    heading(
        "FR-AGENTIC-063",
        "Replay uses immutable references and an isolated environment and "
        "never repeats external side effects.",
    )

    memory = emit(build_in_memory_memory_store())
    records = retrieve_memory(memory, "audit", TASK_ID, NOW)
    operations = build_in_memory_operations_store()
    request = build_replay_request(
        {
            "replay_id": "replay-usage-a",
            "run_id": "run-usage-a",
            "task_id": TASK_ID,
            "environment": "sandbox",
            "reference_hashes": {
                record.record_id: record.content_hash for record in records[:3]
            },
            "requested_by": "operator-owner",
            "requested_at": NOW.isoformat(),
        },
    )
    outcome = replay_run(operations, memory, request, NOW)
    print(f"  environment:            {outcome.environment}")
    print(f"  verified references:    {len(outcome.verified_references)}")
    print(f"  side effects attempted: {outcome.side_effects_attempted}")
    print(f"  executed:               {outcome.executed}")

    print("\n  A replay outside the sandbox cannot be constructed:")
    try:
        build_replay_request(
            {
                "replay_id": "replay-usage-b",
                "run_id": "run-usage-a",
                "task_id": TASK_ID,
                "environment": "production",
                "reference_hashes": {records[0].record_id: records[0].content_hash},
                "requested_by": "operator-owner",
                "requested_at": NOW.isoformat(),
            },
        )
        verdict = "ERROR: a production replay was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        verdict = "unbuildable"
    print(f"    {verdict}")

    print("\n  References are checked against what the store actually holds:")
    cases = (
        ("a reference that never existed", {"record-missing": "a" * 64}),
        ("a digest that no longer matches", {records[0].record_id: "b" * 64}),
        (
            "references that still hold",
            {records[0].record_id: records[0].content_hash},
        ),
    )
    recorded = {record.record_id: record.content_hash for record in records}
    for label, declared in cases:
        failure = verify_references(declared, recorded)
        print(f"    {label:<32} -> {failure or 'verified'}")

    print("\n  An outcome reporting a side effect cannot be built:")
    try:
        build_replay_outcome(
            {
                "replay_id": "replay-usage-c",
                "run_id": "run-usage-a",
                "environment": "sandbox",
                "verified_references": (records[0].record_id,),
                "side_effects_attempted": 1,
                "executed": True,
                "completed_at": NOW.isoformat(),
            },
        )
        verdict = "ERROR: a side-effecting replay was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        verdict = "unbuildable"
    print(f"    {verdict}")
    print(f"    outcome fields: {sorted(ReplayOutcome.model_fields)}")

    print("\n  The durable ledger backs the same rules:")
    for statement in get_operations_migration_statements():
        print(f"    {statement[:92]}")
    request_object = build_operations_migration_request(generate_id("req"))
    print(f"    migration request built: {type(request_object).__name__}")

    print(
        "\n  Note: this feature validates a replay; it does not run one. "
        "Executing a\n  workflow again needs the orchestration executor and a "
        "bound runtime, which a\n  composition root owns. Nothing here exposes "
        "a tool port, a receiver, or a\n  write path a replay could reach, and "
        "quarantine records a decision: changing\n  a role's registered state "
        "is a governance manifest re-issue."
    )


def main() -> None:
    """Run every functional-requirement demonstration for operations."""
    fr_agentic_061()
    fr_agentic_062()
    fr_agentic_063()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-21", main)
