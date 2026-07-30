"""Trace inspection, deterministic containment, and isolated replay.

Three operations, and none invokes a model. Classifying an incident and
containing it must be deterministic; a model here would be a place to argue
that an incident was not one.

`get_run_trace` assembles from audit records `FEAT-AGT-06` already wrote and
already redacted. There is no second redactor in this package: what reaches a
trace was redacted at the memory boundary, and the trace carries the union of
the paths that were redacted so an operator can see that it happened.

`quarantine_agent` performs `WF-AGT-010` steps 2 through 4 in one governed
operation: it derives containment from the incident kind, cancels the run
through the normal orchestration path when the kind requires it, and records
the incident with the evidence preserved rather than discarded.

`replay_run` validates. It proves every declared reference still carries the
digest it was recorded under and that the target is the sandbox, then returns
an outcome reporting that nothing was executed. Actually re-running a workflow
needs the orchestration executor and a bound runtime, which a composition root
owns; this package exposes no tool port, no receiver, and no write path a
replay could reach.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING

from app.agentic.context_memory.repository import retrieve_memory
from app.agentic.operations.models import (
    REQUIRED_SPAN_KINDS,
    build_agentic_trace,
    build_incident_record,
    build_replay_outcome,
    missing_span_kinds,
    required_containment,
)
from app.agentic.orchestration.models import is_terminal_state
from app.agentic.orchestration.service import cancel_task
from app.utils import derive_stable_id, get_logger, utc_now

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from app.agentic.context_memory.models import MemoryRecord
    from app.agentic.context_memory.repository import AgenticMemoryStore
    from app.agentic.contracts.models import AgentTask
    from app.agentic.operations.models import (
        AgenticTrace,
        IncidentKind,
        IncidentRecord,
        ReplayOutcome,
        ReplayRequest,
    )
    from app.agentic.operations.repository import AgenticOperationsStore
    from app.agentic.orchestration.repository import AgenticWorkflowStore

logger = get_logger(__name__)

# The content key an emitter tags a record with so its span is a fact rather
# than a guess. A record without one cannot be placed, and a trace missing a
# required span cannot be assembled — which is the point: unlabelled telemetry
# is not observability.
SPAN_KEY = "span"

# The content key a cost span reports its consumption under.
COST_KEY = "cost"

# The audit store class every governed tool call already writes to.
AUDIT_STORE_CLASS = "audit"


def _span_of(record: MemoryRecord) -> str | None:
    """Return the span kind one audit record declares.

    Args:
        record: Governed audit record.

    Returns:
        The declared span kind, or None when the record carries no label.
    """
    declared = record.content.get(SPAN_KEY)
    if declared is None:
        return None
    return str(declared)


def _observed_cost(records: tuple[MemoryRecord, ...]) -> Decimal:
    """Sum the cost every cost span reported.

    An unreadable cost is not silently treated as zero; it is skipped and the
    span still counts as covered, because a cost span that reported nothing
    readable is a defect in the emitter rather than an absent span.

    Args:
        records: Governed audit records.

    Returns:
        The total observed cost.
    """
    total = Decimal(0)
    for record in records:
        if _span_of(record) != "cost":
            continue
        raw = record.content.get(COST_KEY)
        if raw is None:
            continue
        try:
            total += Decimal(str(raw))
        except InvalidOperation:
            logger.warning("A cost span reported an unreadable cost; skipping it")
    return total


def _summaries(records: tuple[MemoryRecord, ...]) -> dict[str, str]:
    """Summarize the covered spans, one bounded line per kind.

    Args:
        records: Governed audit records.

    Returns:
        Span kind to bounded summary.
    """
    counts: dict[str, int] = {}
    for record in records:
        kind = _span_of(record)
        if kind is None:
            continue
        counts[kind] = counts.get(kind, 0) + 1
    return {
        kind: f"{count} record{'s' if count != 1 else ''} recorded"
        for kind, count in sorted(counts.items())
    }


def _redacted_paths(records: tuple[MemoryRecord, ...]) -> tuple[str, ...]:
    """Return the union of paths redacted before persistence.

    Args:
        records: Governed audit records.

    Returns:
        Ordered unique redacted paths.
    """
    paths: set[str] = set()
    for record in records:
        paths.update(record.redacted_paths)
    return tuple(sorted(paths))


def get_run_trace(
    memory_store: AgenticMemoryStore,
    task_id: str,
    run_id: str,
    correlation_id: str,
    operations_store: AgenticOperationsStore | None = None,
    at_time: datetime | None = None,
) -> AgenticTrace:
    """Assemble one correlated redacted trace for a run.

    Args:
        memory_store: Injected governed audit store.
        task_id: Owning task identity.
        run_id: Run to trace.
        correlation_id: Identifier every span of the run shares.
        operations_store: Optional store the assembled trace is saved to.
        at_time: Optional assembly time; current UTC when omitted.

    Returns:
        A validated immutable trace carrying its content digest.

    Raises:
        ValueError: If any required span kind has no labelled record.
    """
    now = at_time if at_time is not None else utc_now()
    records = retrieve_memory(memory_store, AUDIT_STORE_CLASS, task_id, now)
    logger.info(
        "Assembling a trace for run %s from %d audit records",
        run_id,
        len(records),
    )

    spans = _summaries(records)
    missing = missing_span_kinds(spans)
    if missing:
        message = (
            "the run emitted no record for every required span; missing: "
            f"{', '.join(missing)}"
        )
        raise ValueError(message)

    trace = build_agentic_trace(
        {
            "trace_id": derive_stable_id("id", f"trace:{run_id}:{correlation_id}"),
            "correlation_id": correlation_id,
            "task_id": task_id,
            "run_id": run_id,
            # Only the required kinds reach the trace; an emitter labelling a
            # span nobody agreed to does not widen the contract.
            "spans": {
                kind: summary
                for kind, summary in spans.items()
                if kind in REQUIRED_SPAN_KINDS
            },
            "record_count": len(records),
            # Inherited from the memory boundary, never recomputed here.
            "redacted_paths": _redacted_paths(records),
            "observed_cost": _observed_cost(records),
            "assembled_at": now.isoformat(),
        },
    )
    if operations_store is not None:
        operations_store.save_trace(trace)
    return trace


def quarantine_agent(
    operations_store: AgenticOperationsStore,
    workflow_store: AgenticWorkflowStore,
    run_id: str,
    task: AgentTask,
    kind: IncidentKind,
    trigger: str,
    role_id: str,
    preserved_evidence_refs: tuple[str, ...],
    checkpoint_ref: str,
    correlation_id: str | None = None,
    at_time: datetime | None = None,
) -> IncidentRecord:
    """Classify, contain, and record one incident.

    Containment follows from the kind through a fixed table, so the same
    incident contains the same way whoever reports it. The run is cancelled
    through the normal orchestration path when the kind requires it, and the
    checkpoint and evidence are recorded rather than discarded.

    Args:
        operations_store: Injected durable operations store.
        workflow_store: Injected durable workflow store.
        run_id: Run the incident occurred in.
        task: Owning governed task.
        kind: Enumerated incident classification.
        trigger: Bounded description of what was observed.
        role_id: Role implicated by the incident.
        preserved_evidence_refs: Evidence kept for investigation.
        checkpoint_ref: Checkpoint preserved rather than dropped.
        correlation_id: Optional flow identifier; the task's when omitted.
        at_time: Optional detection time; current UTC when omitted.

    Returns:
        The recorded immutable incident.

    Raises:
        ValueError: If the kind is unrecognized, the run is unknown, or this
            kind is already recorded for the run.
    """
    now = at_time if at_time is not None else utc_now()
    action = required_containment(kind)
    logger.info(
        "Containing a %s incident on run %s with %s",
        kind,
        run_id,
        action,
    )

    contained_state = _contain(
        workflow_store,
        run_id,
        task,
        kind,
        action,
        now,
    )
    quarantines = action in {"quarantine", "quarantine_and_cancel"}
    incident = build_incident_record(
        {
            "incident_id": derive_stable_id("id", f"incident:{run_id}:{kind}"),
            "task_id": task.task_id,
            "run_id": run_id,
            "correlation_id": correlation_id or task.correlation_id,
            "kind": kind,
            "trigger": trigger,
            # Derived from the kind, never supplied by the caller.
            "containment_action": action,
            "contained_state": contained_state,
            "quarantined_role_id": role_id if quarantines else None,
            "preserved_evidence_refs": preserved_evidence_refs,
            "checkpoint_ref": checkpoint_ref,
            "detected_at": now.isoformat(),
        },
    )
    return operations_store.record_incident(incident)


def _contain(
    workflow_store: AgenticWorkflowStore,
    run_id: str,
    task: AgentTask,
    kind: str,
    action: str,
    at_time: datetime,
) -> str:
    """Apply the containment one incident kind requires to a run.

    Args:
        workflow_store: Injected durable workflow store.
        run_id: Run the incident occurred in.
        task: Owning governed task.
        kind: Enumerated incident classification.
        action: Containment action the kind requires.
        at_time: Containment time.

    Returns:
        The durable run state after containment.

    Raises:
        ValueError: If the run is unknown.
    """
    run = workflow_store.load_run(run_id)
    if run is None:
        message = f"run {run_id} is unknown and cannot be contained"
        raise ValueError(message)
    if "cancel" not in action:
        return run.state
    if is_terminal_state(run.state):
        # A run that already stopped needs no cancelling, and cancelling it
        # would rewrite a terminal outcome that is not this feature's to
        # change. The incident is still recorded against its real state.
        logger.info(
            "Run %s is already %s; the incident is recorded against that state",
            run_id,
            run.state,
        )
        return run.state
    cancelled = cancel_task(
        workflow_store,
        run_id,
        task,
        reason=f"INCIDENT_{kind.upper()}",
        at_time=at_time,
    )
    return cancelled.state


def replay_run(
    operations_store: AgenticOperationsStore,
    memory_store: AgenticMemoryStore,
    request: ReplayRequest,
    at_time: datetime | None = None,
) -> ReplayOutcome:
    """Validate one replay against immutable references and record it.

    Every declared reference must still carry the digest it was recorded
    under. Replaying against mutated evidence is not a replay, so a digest
    that no longer matches refuses rather than degrades.

    Args:
        operations_store: Injected durable operations store.
        memory_store: Injected governed audit store.
        request: Validated immutable replay request.
        at_time: Optional outcome time; current UTC when omitted.

    Returns:
        A validated immutable outcome reporting no attempted side effect.

    Raises:
        ValueError: If a reference is unknown or its digest no longer matches.
    """
    now = at_time if at_time is not None else utc_now()
    records = retrieve_memory(memory_store, AUDIT_STORE_CLASS, request.task_id, now)
    digests = {record.record_id: record.content_hash for record in records}
    logger.info(
        "Validating replay %s against %d immutable references",
        request.replay_id,
        len(request.reference_hashes),
    )

    failure = verify_references(request.reference_hashes, digests)
    if failure is not None:
        raise ValueError(failure)

    outcome = build_replay_outcome(
        {
            "replay_id": request.replay_id,
            "run_id": request.run_id,
            "environment": request.environment,
            "verified_references": tuple(sorted(request.reference_hashes)),
            # This package executes nothing. The count is zero because there
            # is no path here that could make it anything else.
            "side_effects_attempted": 0,
            "executed": False,
            "completed_at": now.isoformat(),
        },
    )
    return operations_store.record_replay(request, outcome)


def verify_references(
    declared: Mapping[str, str],
    recorded: Mapping[str, str],
) -> str | None:
    """Report whether every declared reference still holds its digest.

    Args:
        declared: Reference identity to the digest a replay expects.
        recorded: Reference identity to the digest currently recorded.

    Returns:
        The failing condition, or None when every reference holds.
    """
    unknown = tuple(sorted(set(declared) - set(recorded)))
    if unknown:
        return f"replay references are not recorded: {', '.join(unknown)}"
    changed = tuple(
        sorted(name for name, digest in declared.items() if recorded[name] != digest)
    )
    if changed:
        return (
            "replay references no longer carry the digest they were recorded "
            f"under: {', '.join(changed)}"
        )
    return None


def get_quarantined_roles(store: AgenticOperationsStore) -> tuple[str, ...]:
    """Return every role an incident has quarantined.

    Args:
        store: Injected durable operations store.

    Returns:
        Ordered unique quarantined role identities.
    """
    return store.quarantined_roles()


def get_run_incidents(
    store: AgenticOperationsStore,
    run_id: str,
) -> tuple[IncidentRecord, ...]:
    """Return every incident recorded against one run.

    Args:
        store: Injected durable operations store.
        run_id: Run identity.

    Returns:
        Ordered incident records, empty when none.
    """
    return store.list_incidents(run_id)
