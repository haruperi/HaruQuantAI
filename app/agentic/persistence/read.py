"""Read operations for Agentic-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.agentic.persistence.create import _execute, _require_store
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)
_MAX_READ_ROWS = 1_000


def _bounded_limit(limit: int) -> int:
    """Return one safe relational read limit.

    Raises:
        ValueError: If the limit is outside the Agentic persistence bound.
    """
    if isinstance(limit, bool) or not 1 <= limit <= _MAX_READ_ROWS:
        raise ValueError("Agentic persistence limit must be between 1 and 1000")
    return limit


def _one_row(
    statement: str, parameters: tuple[object, ...]
) -> Mapping[str, object] | None:
    """Read at most one normalized relational row.

    Returns:
        Stored row or ``None``.
    """
    rows = _execute((statement,), (parameters,), max_rows=1).rows
    return None if not rows else rows[0]


def _rows(
    statement: str, parameters: tuple[object, ...], limit: int
) -> tuple[Mapping[str, object], ...]:
    """Read a bounded ordered row collection.

    Returns:
        Ordered normalized rows.
    """
    return _execute(
        (statement,),
        (parameters,),
        max_rows=_bounded_limit(limit),
    ).rows


def _nested(value: object) -> object:
    """Decode one stored canonical JSON field.

    Returns:
        Decoded JSON value.
    """
    return json.loads(str(value))


def _without(row: Mapping[str, object], *names: str) -> dict[str, object]:
    """Copy one row without relational JSON carrier columns.

    Returns:
        Filtered row mapping.
    """
    return {name: value for name, value in row.items() if name not in names}


def _decode(store: object, kind: str, payload: Mapping[str, object]) -> object:
    """Decode one reconstructed model through its allowlisted codec.

    Returns:
        Validated decoded model.

    Raises:
        TypeError: If the record kind is not registered.
    """
    codec = _require_store(store).codecs.get(kind)
    if codec is None:
        message = f"Unknown Agentic record kind: {kind}"
        raise TypeError(message)
    return codec[1](canonical_json(dict(payload), max_items=None))


def _workflow_run(row: Mapping[str, object]) -> dict[str, object]:
    """Reconstruct one workflow-run payload.

    Returns:
        Workflow-run model fields.
    """
    return {
        name: row.get(name)
        for name in (
            "run_id",
            "task_id",
            "workflow_name",
            "workflow_version",
            "state",
            "current_node",
            "sequence",
            "revision",
            "attempts",
            "idempotency_key",
            "created_at",
            "updated_at",
            "deadline_at",
            "terminal_reason",
        )
    }


def read_memory_records(
    store: object,
    store_class: str,
    task_id: str,
    limit: int,
) -> tuple[object, ...]:
    """Read ordered Agentic memory records for one governed scope.

    Returns:
        Validated memory records.
    """
    logger.debug("Reading Agentic memory persistence records")
    rows = _rows(
        "SELECT record_id, store_class, task_id, author_role_id, content_json, "
        "scope_json, source_evidence_refs_json, created_at, expires_at, "
        "retention_class, sensitivity, injection_status, redacted_paths_json, "
        "content_hash, supersedes FROM agentic_memory_records "
        "WHERE store_class=? AND task_id=? ORDER BY created_at, record_id LIMIT ?",
        (store_class, task_id, _bounded_limit(limit)),
        limit,
    )
    return tuple(
        _decode(
            store,
            "memory",
            {
                **_without(
                    row,
                    "content_json",
                    "scope_json",
                    "source_evidence_refs_json",
                    "redacted_paths_json",
                ),
                "content": _nested(row["content_json"]),
                "scope": _nested(row["scope_json"]),
                "source_evidence_refs": _nested(row["source_evidence_refs_json"]),
                "redacted_paths": _nested(row["redacted_paths_json"]),
            },
        )
        for row in rows
    )


def read_lifecycle_records(
    store: object, artifact_hash: str, limit: int
) -> tuple[object, ...]:
    """Read ordered Agentic lifecycle transitions for one artifact.

    Returns:
        Validated lifecycle records.
    """
    logger.debug("Reading Agentic lifecycle persistence records")
    rows = _rows(
        "SELECT record_id, artifact_hash, artifact_id, sequence, previous_state, "
        "state, actor_id, rationale, recorded_at, packet_hash, termination_reason, "
        "unresolved_concerns_json FROM agentic_lifecycle_transitions "
        "WHERE artifact_hash=? ORDER BY sequence LIMIT ?",
        (artifact_hash, _bounded_limit(limit)),
        limit,
    )
    return tuple(
        _decode(
            store,
            "lifecycle",
            {
                **_without(row, "unresolved_concerns_json"),
                "unresolved_concerns": _nested(row["unresolved_concerns_json"]),
            },
        )
        for row in rows
    )


def read_lifecycle_packet_record(store: object, packet_hash: str) -> object | None:
    """Read one Agentic promotion-evidence packet.

    Returns:
        Validated packet or ``None``.
    """
    logger.debug("Reading Agentic lifecycle packet persistence record")
    row = _one_row(
        "SELECT packet_hash, packet_id, task_id, artifact_json, "
        "experiment_verdict_json, sweep_verdict_json, critique_json, "
        "simulation_manifest_ref, lifetime_trial_ceiling, approver_id, "
        "approval_environment, assembled_at FROM agentic_promotion_packets "
        "WHERE packet_hash=?",
        (packet_hash,),
    )
    if row is None:
        return None
    return _decode(
        store,
        "packet",
        {
            **_without(
                row,
                "artifact_json",
                "experiment_verdict_json",
                "sweep_verdict_json",
                "critique_json",
            ),
            "artifact": _nested(row["artifact_json"]),
            "experiment_verdict": _nested(row["experiment_verdict_json"]),
            "sweep_verdict": _nested(row["sweep_verdict_json"]),
            "critique": _nested(row["critique_json"]),
        },
    )


def read_operation_trace_record(store: object, trace_hash: str) -> object | None:
    """Read one Agentic operation trace.

    Returns:
        Validated trace or ``None``.
    """
    logger.debug("Reading Agentic operation trace persistence record")
    row = _one_row(
        "SELECT trace_hash, trace_id, correlation_id, task_id, run_id, spans_json, "
        "redacted_paths_json, record_count, observed_cost, assembled_at "
        "FROM agentic_operations_traces WHERE trace_hash=?",
        (trace_hash,),
    )
    if row is None:
        return None
    return _decode(
        store,
        "trace",
        {
            **_without(row, "spans_json", "redacted_paths_json"),
            "spans": _nested(row["spans_json"]),
            "redacted_paths": _nested(row["redacted_paths_json"]),
        },
    )


def read_incident_records(
    store: object, partition: str, limit: int
) -> tuple[object, ...]:
    """Read the bounded ordered Agentic incident ledger.

    Returns:
        Validated incident records.
    """
    del partition
    logger.debug("Reading Agentic incident persistence records")
    rows = _rows(
        "SELECT incident_id, task_id, run_id, correlation_id, kind, trigger, "
        "containment_action, contained_state, quarantined_role_id, checkpoint_ref, "
        "preserved_evidence_refs_json, detected_at FROM agentic_operations_incidents "
        "ORDER BY detected_at, incident_id LIMIT ?",
        (_bounded_limit(limit),),
        limit,
    )
    return tuple(
        _decode(
            store,
            "incident",
            {
                **_without(row, "preserved_evidence_refs_json"),
                "preserved_evidence_refs": _nested(row["preserved_evidence_refs_json"]),
            },
        )
        for row in rows
    )


def read_workflow_idempotency_record(store: object, key: str) -> object | None:
    """Read one workflow run by its idempotency identity.

    Returns:
        Validated workflow run or ``None``.
    """
    logger.debug("Reading Agentic workflow idempotency persistence record")
    row = _one_row(
        "SELECT run_id, task_id, workflow_name, workflow_version, state, "
        "current_node, sequence, revision, attempts, idempotency_key, created_at, "
        "updated_at, deadline_at, terminal_reason FROM agentic_workflow_runs "
        "WHERE idempotency_key=?",
        (key,),
    )
    return None if row is None else _decode(store, "workflow-run", _workflow_run(row))


def read_workflow_run_record(store: object, key: str) -> object | None:
    """Read one Agentic workflow run by identity.

    Returns:
        Validated workflow run or ``None``.
    """
    logger.debug("Reading Agentic workflow run persistence record")
    row = _one_row(
        "SELECT run_id, task_id, workflow_name, workflow_version, state, "
        "current_node, sequence, revision, attempts, idempotency_key, created_at, "
        "updated_at, deadline_at, terminal_reason FROM agentic_workflow_runs "
        "WHERE run_id=?",
        (key,),
    )
    return None if row is None else _decode(store, "workflow-run", _workflow_run(row))


def read_workflow_checkpoint_records(
    store: object, task_id: str, limit: int
) -> tuple[object, ...]:
    """Read ordered Agentic workflow checkpoints for one task.

    Returns:
        Validated workflow checkpoints.
    """
    logger.debug("Reading Agentic workflow checkpoint persistence records")
    rows = _rows(
        "SELECT contract_version, created_at, request_id, workflow_id, "
        "correlation_id, causation_id, canonical_hash, schema_id, checkpoint_id, "
        "task_id, workflow_name, workflow_version, node_id, sequence, state, "
        "expected_version, state_payload_hash FROM agentic_workflow_checkpoints "
        "WHERE task_id=? ORDER BY sequence LIMIT ?",
        (task_id, _bounded_limit(limit)),
        limit,
    )
    return tuple(_decode(store, "checkpoint", dict(row)) for row in rows)


__all__ = [
    "read_incident_records",
    "read_lifecycle_packet_record",
    "read_lifecycle_records",
    "read_memory_records",
    "read_operation_trace_record",
    "read_workflow_checkpoint_records",
    "read_workflow_idempotency_record",
    "read_workflow_run_record",
]
