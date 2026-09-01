"""Executable FEAT-AGT-04 durable orchestration usage example.

Demonstrates every public operation registered for FEAT-AGT-04 through the
documented function-only `app.agentic` package-root API. The store is the
deterministic in-memory reference implementation: it proves idempotency,
expected-version conflict detection, and checkpoint ordering, but durability
across a process crash is a property of the concrete store a composition root
injects.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.usage._runner import run_feature_usage

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def make_definition():
    """Build one immutable bounded workflow declaration."""
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


def make_task(idempotency_key="idem-research-eurusd-0001"):
    """Build one bounded governed task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": derive_stable_id("id", f"task:{idempotency_key}"),
            "workflow_name": WORKFLOW_NAME,
            "workflow_version": WORKFLOW_VERSION,
            "objective": "Assess EURUSD H1 trend evidence for the London session.",
            "input_refs": ("evidence-market-eurusd-h1",),
            "principal_id": "operator-owner",
            "scope": {"environment": "sandbox", "asset_class": "fx"},
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": idempotency_key,
            "budgets": {"cost": Decimal("5.00")},
        },
    )


def fr_agentic_010() -> None:
    """FR-AGENTIC-010: Submission is idempotent and checkpoints first."""
    _header(
        "FR-AGENTIC-010: Task submission is idempotent and persists the declared "
        "workflow, principal, inputs, budgets, deadline, and initial checkpoint "
        "before execution."
    )

    store = build_in_memory_workflow_store()
    definition = make_definition()
    task = make_task()

    run = submit_task(store, definition, task, at_time=NOW)
    print(f"  run state:       {run.state}")
    print(f"  entry node:      {run.current_node}")
    print(f"  sequence:        {run.sequence}")
    checkpoints = store.list_checkpoints(task.task_id)
    print(f"  checkpoints:     {len(checkpoints)} persisted before execution")
    print(f"  first checkpoint state: {checkpoints[0].state}")

    replay = submit_task(store, definition, task, at_time=NOW)
    print(f"  replayed key returns the original run: {replay.run_id == run.run_id}")
    print(f"  checkpoints after replay: {len(store.list_checkpoints(task.task_id))}")

    try:
        submit_task(store, definition, task, at_time=NOW + timedelta(hours=2))
        outcome = "ERROR: a passed deadline was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Submission after the deadline correctly refused"
    print(f"  {outcome}")


def fr_agentic_011() -> None:
    """FR-AGENTIC-011: Bounded routing, cancellation, expiry, and resume."""
    _header(
        "FR-AGENTIC-011: Workflow runs support deterministic routing, bounded "
        "fan-out, cancellation, expiration, human waits, and crash-safe resume."
    )

    definition = make_definition()
    print(f"  bounds: fan_out={definition.max_fan_out} rounds={definition.max_rounds}")
    print(
        f"          retries={definition.max_retries} human_wait="
        f"{definition.permits_human_wait}"
    )

    store = build_in_memory_workflow_store()
    task = make_task()
    run = submit_task(store, definition, task, at_time=NOW)
    resumed = resume_task(store, run.run_id, task, at_time=NOW + timedelta(minutes=1))
    print(f"  resumed:  {run.state} -> {resumed.state} (revision {resumed.revision})")
    print(
        f"  transition running -> waiting_human: "
        f"{validate_transition('running', 'waiting_human')}"
    )

    try:
        store.save_run(run, 0)
        outcome = "ERROR: a stale revision overwrote a committed transition"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Stale expected-version write correctly refused"
    print(f"  {outcome}")

    cancel_store = build_in_memory_workflow_store()
    cancel_run = submit_task(
        cancel_store, definition, make_task("idem-cancel"), at_time=NOW
    )
    cancelled = cancel_task(
        cancel_store, cancel_run.run_id, make_task("idem-cancel"), at_time=NOW
    )
    print(f"  cancelled: state={cancelled.state} reason={cancelled.terminal_reason}")

    expire_store = build_in_memory_workflow_store()
    expire_task_obj = make_task("idem-expire")
    expire_run = submit_task(expire_store, definition, expire_task_obj, at_time=NOW)
    expired = expire_task(
        expire_store,
        expire_run.run_id,
        expire_task_obj,
        at_time=NOW + timedelta(hours=2),
    )
    print(f"  expired:   state={expired.state} reason={expired.terminal_reason}")


def fr_agentic_012() -> None:
    """FR-AGENTIC-012: Terminal runs never resume."""
    _header(
        "FR-AGENTIC-012: Terminal task states are succeeded, refused, failed, "
        "cancelled, or expired; no terminal run resumes without a new identity."
    )

    for state in ("succeeded", "refused", "failed", "cancelled", "expired"):
        print(f"  {state}: terminal={is_terminal_state(state)}")
    for state in ("submitted", "running", "waiting_human"):
        print(f"  {state}: terminal={is_terminal_state(state)}")

    store = build_in_memory_workflow_store()
    definition = make_definition()
    task = make_task("idem-terminal")
    run = submit_task(store, definition, task, at_time=NOW)
    cancel_task(store, run.run_id, task, at_time=NOW)

    try:
        resume_task(store, run.run_id, task, at_time=NOW)
        outcome = "ERROR: a terminal run resumed"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Terminal run correctly refused resumption under the same identity"
    print(f"  {outcome}")

    try:
        validate_transition("cancelled", "running")
        outcome = "ERROR: a transition out of a terminal state was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Transition out of a terminal state correctly rejected"
    print(f"  {outcome}")


def migrations() -> None:
    """Show the Agentic-owned additive schema executed by Data."""
    _header(
        "Persistence: Agentic declares its additive schema; Data owns migration "
        "execution, the immutable ledger, checksums, and write locks."
    )
    statements = get_agentic_migration_statements()
    for statement in statements:
        head = statement.split("(")[0].strip()
        print(f"  {head}")
    request = build_agentic_migration_request(generate_id("req"))
    print(f"  migration request built for the agentic domain: {request is not None}")
    print("  Agentic executes no migration itself.")


def main() -> None:
    """Run every functional-requirement demonstration for orchestration."""
    fr_agentic_010()
    fr_agentic_011()
    fr_agentic_012()
    migrations()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-04", main)
