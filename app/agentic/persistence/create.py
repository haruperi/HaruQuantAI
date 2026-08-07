"""Create operations for Agentic-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import canonical_digest, canonical_json, generate_id, get_logger

logger = get_logger(__name__)
type _Codec = tuple[Callable[[object], str], Callable[[str], object]]


class _TransactionResult:
    """Structural transaction result returned by Data."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


@dataclass(frozen=True, slots=True)
class _AgenticPersistenceStore:
    """Opaque allowlisted codec registry for Agentic relational records."""

    codecs: Mapping[str, _Codec]


def _require_store(store: object) -> _AgenticPersistenceStore:
    """Return a validated Agentic persistence handle.

    Raises:
        TypeError: If the handle did not originate from this package.
    """
    if not isinstance(store, _AgenticPersistenceStore):
        raise TypeError("Invalid Agentic persistence store")
    return store


def _execute(
    statements: Sequence[str],
    parameter_sets: Sequence[Sequence[object]],
    *,
    request_id: str | None = None,
    max_rows: int = 1_000,
) -> _TransactionResult:
    """Execute one Agentic statement plan through Data's public boundary.

    Returns:
        Confirmed normalized transaction result.

    Raises:
        ValueError: If Data cannot confirm the transaction.
    """
    operation_id = request_id or generate_id("req")
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=tuple(statements),
                parameter_sets=tuple(tuple(items) for items in parameter_sets),
                max_rows=max_rows,
            ),
            request_id=operation_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValueError("Agentic persistence transaction failed")
    return cast("_TransactionResult", response.data)


def _model_value(store: object, kind: str, value: object) -> Mapping[str, object]:
    """Encode one allowlisted model into a JSON-safe mapping.

    Returns:
        Encoded model mapping.

    Raises:
        TypeError: If the codec or encoded material is invalid.
    """
    registry = _require_store(store).codecs
    codec = registry.get(kind)
    if codec is None:
        message = f"Unknown Agentic record kind: {kind}"
        raise TypeError(message)
    decoded = json.loads(codec[0](value))
    if not isinstance(decoded, dict):
        raise TypeError("Agentic record codec must encode a JSON object")
    return decoded


def _json(value: object) -> str:
    """Serialize one nested contract value canonically.

    Returns:
        Canonical JSON text.
    """
    return canonical_json(value, max_items=None)


def _field(value: Mapping[str, object], name: str) -> object:
    """Return one required model field.

    Returns:
        Required field value.

    Raises:
        TypeError: If the field is absent.
    """
    if name not in value:
        message = f"Agentic record field {name} is required"
        raise TypeError(message)
    return value[name]


def create_agentic_persistence_store(codecs: Mapping[str, _Codec]) -> object:
    """Create an opaque Agentic relational-store handle.

    Args:
        codecs: Explicit allowlisted encoders and decoders by record kind.

    Returns:
        Opaque Agentic persistence handle.

    Raises:
        ValueError: If codec names are empty or missing.
    """
    if not codecs or any(not isinstance(name, str) or not name for name in codecs):
        raise ValueError("Agentic persistence codecs must be explicitly named")
    logger.debug("Creating Agentic relational persistence handle")
    return _AgenticPersistenceStore(dict(codecs))


def create_memory_record(
    store: object,
    *,
    key: str,
    partition: str,
    sequence: int,
    value: object,
) -> None:
    """Append one immutable Agentic memory record."""
    del key, partition, sequence
    record = _model_value(store, "memory", value)
    _execute(
        (
            "INSERT INTO agentic_memory_records "
            "(record_id, store_class, task_id, author_role_id, content_json, "
            "scope_json, source_evidence_refs_json, created_at, expires_at, "
            "retention_class, sensitivity, injection_status, redacted_paths_json, "
            "content_hash, supersedes) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(record, "record_id"),
                _field(record, "store_class"),
                _field(record, "task_id"),
                _field(record, "author_role_id"),
                _json(_field(record, "content")),
                _json(_field(record, "scope")),
                _json(_field(record, "source_evidence_refs")),
                _field(record, "created_at"),
                record.get("expires_at"),
                _field(record, "retention_class"),
                _field(record, "sensitivity"),
                _field(record, "injection_status"),
                _json(_field(record, "redacted_paths")),
                _field(record, "content_hash"),
                record.get("supersedes"),
            ),
        ),
    )


def create_evidence_claim(store: object, value: object) -> None:
    """Append one immutable governed evidence claim."""
    claim = _model_value(store, "evidence", value)
    _execute(
        (
            "INSERT INTO agentic_evidence_claims "
            "(claim_id, task_id, statement, source_ref, source_trust, licence_ref, "
            "available_at, observed_at, content_hash, confidence_basis, falsifier, "
            "injection_status, request_id, correlation_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(claim, "claim_id"),
                _field(claim, "task_id"),
                _field(claim, "statement"),
                _field(claim, "source_ref"),
                _field(claim, "source_trust"),
                _field(claim, "licence_ref"),
                _field(claim, "available_at"),
                _field(claim, "observed_at"),
                _field(claim, "content_hash"),
                _field(claim, "confidence_basis"),
                _field(claim, "falsifier"),
                _field(claim, "injection_status"),
                claim.get("request_id", ""),
                claim.get("correlation_id", ""),
            ),
        ),
    )


def create_experiment_spec(store: object, value: object) -> None:
    """Create one immutable pre-registered experiment specification."""
    spec = _model_value(store, "experiment-spec", value)
    _execute(
        (
            "INSERT INTO agentic_experiment_specs "
            "(spec_id, task_id, thesis_id, spec_hash, seed, embargo_seconds, "
            "baseline_ref, cost_model_ref, falsification_outcome, spec_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(spec, "spec_id"),
                _field(spec, "task_id"),
                _field(spec, "thesis_id"),
                _field(spec, "spec_hash"),
                _field(spec, "seed"),
                _field(spec, "embargo_seconds"),
                _field(spec, "baseline_ref"),
                _field(spec, "cost_model_ref"),
                _field(spec, "falsification_outcome"),
                _json(spec),
            ),
        ),
    )


def create_experiment_run(
    *,
    spec_hash: str,
    run_id: str,
    evidence_class: str,
    lineage: Mapping[str, str],
    at_time: datetime,
) -> None:
    """Record one immutable receiver-returned experiment run."""
    _execute(
        (
            "INSERT INTO agentic_experiment_runs "
            "(run_id, spec_hash, task_id, evidence_class, request_hash, "
            "config_hash, engine_version, journal_ref, artifact_manifest_ref, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                run_id,
                spec_hash,
                lineage["task_id"],
                evidence_class,
                lineage["request_hash"],
                lineage["config_hash"],
                lineage["engine_version"],
                lineage["journal_ref"],
                lineage["artifact_manifest_ref"],
                at_time.isoformat(),
            ),
        ),
    )


def create_experiment_holdout_use(
    *,
    spec_hash: str,
    task_id: str,
    run_id: str,
    consumed_at: datetime,
) -> bool:
    """Atomically reserve the single permitted holdout use.

    Returns:
        Whether this call inserted the unique reservation.
    """
    result = _execute(
        (
            "INSERT OR IGNORE INTO agentic_experiment_holdout_use "
            "(spec_hash, task_id, run_id, consumed_at) VALUES (?, ?, ?, ?)",
        ),
        ((spec_hash, task_id, run_id, consumed_at.isoformat()),),
    )
    return result.affected_rows == 1


def create_experiment_verdict(store: object, value: object) -> None:
    """Create one immutable run-bound experiment verdict."""
    verdict = _model_value(store, "experiment-verdict", value)
    _execute(
        (
            "INSERT INTO agentic_experiment_verdicts "
            "(verdict_id, spec_id, spec_hash, task_id, outcome, "
            "holdout_consumed, canonical_hash, verdict_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(verdict, "verdict_id"),
                _field(verdict, "spec_id"),
                _field(verdict, "spec_hash"),
                _field(verdict, "task_id"),
                _field(verdict, "outcome"),
                int(bool(_field(verdict, "holdout_consumed"))),
                canonical_digest(verdict),
                _json(verdict),
            ),
        ),
    )


def create_lifecycle_record(
    store: object,
    *,
    key: str,
    partition: str,
    sequence: int,
    value: object,
) -> None:
    """Append one immutable Agentic lifecycle transition.

    Raises:
        ValueError: If the declared and model sequence differ.
    """
    del key, partition
    record = _model_value(store, "lifecycle", value)
    if _field(record, "sequence") != sequence:
        raise ValueError("Agentic lifecycle sequence is inconsistent")
    _execute(
        (
            "INSERT INTO agentic_lifecycle_transitions "
            "(artifact_hash, sequence, record_id, artifact_id, previous_state, state, "
            "packet_hash, termination_reason, unresolved_concerns_json, actor_id, "
            "rationale, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(record, "artifact_hash"),
                sequence,
                _field(record, "record_id"),
                _field(record, "artifact_id"),
                record.get("previous_state"),
                _field(record, "state"),
                record.get("packet_hash"),
                record.get("termination_reason"),
                _json(_field(record, "unresolved_concerns")),
                _field(record, "actor_id"),
                _field(record, "rationale"),
                _field(record, "recorded_at"),
            ),
        ),
    )


def create_lifecycle_packet_record(store: object, key: str, value: object) -> None:
    """Create one immutable Agentic promotion-evidence packet.

    Raises:
        TypeError: If the packet artifact is not a validated mapping.
    """
    del key
    packet = _model_value(store, "packet", value)
    artifact = _field(packet, "artifact")
    if not isinstance(artifact, Mapping):
        raise TypeError("Agentic packet artifact must be a mapping")
    _execute(
        (
            "INSERT INTO agentic_promotion_packets "
            "(packet_hash, packet_id, task_id, artifact_hash, artifact_json, "
            "experiment_verdict_json, sweep_verdict_json, critique_json, "
            "simulation_manifest_ref, lifetime_trial_ceiling, approver_id, "
            "approval_environment, assembled_at) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(packet, "packet_hash"),
                _field(packet, "packet_id"),
                _field(packet, "task_id"),
                _field(artifact, "artifact_hash"),
                _json(artifact),
                _json(_field(packet, "experiment_verdict")),
                _json(_field(packet, "sweep_verdict")),
                _json(_field(packet, "critique")),
                _field(packet, "simulation_manifest_ref"),
                _field(packet, "lifetime_trial_ceiling"),
                _field(packet, "approver_id"),
                _field(packet, "approval_environment"),
                _field(packet, "assembled_at"),
            ),
        ),
    )


def create_operation_trace_record(store: object, key: str, value: object) -> None:
    """Create one immutable Agentic operation trace."""
    del key
    trace = _model_value(store, "trace", value)
    _execute(
        (
            "INSERT INTO agentic_operations_traces "
            "(trace_hash, trace_id, correlation_id, task_id, run_id, spans_json, "
            "redacted_paths_json, record_count, observed_cost, assembled_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(trace, "trace_hash"),
                _field(trace, "trace_id"),
                _field(trace, "correlation_id"),
                _field(trace, "task_id"),
                _field(trace, "run_id"),
                _json(_field(trace, "spans")),
                _json(_field(trace, "redacted_paths")),
                _field(trace, "record_count"),
                str(_field(trace, "observed_cost")),
                _field(trace, "assembled_at"),
            ),
        ),
    )


def create_incident_record(
    store: object,
    *,
    guard_key: str,
    incident_key: str,
    sequence: int,
    value: object,
) -> bool:
    """Atomically enforce incident uniqueness and append its evidence.

    Returns:
        Whether the unique incident row was inserted.
    """
    del guard_key, incident_key, sequence
    incident = _model_value(store, "incident", value)
    result = _execute(
        (
            "INSERT OR IGNORE INTO agentic_operations_incidents "
            "(incident_id, task_id, run_id, correlation_id, kind, trigger, "
            "containment_action, contained_state, quarantined_role_id, "
            "checkpoint_ref, preserved_evidence_refs_json, detected_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(incident, "incident_id"),
                _field(incident, "task_id"),
                _field(incident, "run_id"),
                _field(incident, "correlation_id"),
                _field(incident, "kind"),
                _field(incident, "trigger"),
                _field(incident, "containment_action"),
                _field(incident, "contained_state"),
                incident.get("quarantined_role_id"),
                _field(incident, "checkpoint_ref"),
                _json(_field(incident, "preserved_evidence_refs")),
                _field(incident, "detected_at"),
            ),
        ),
    )
    return result.affected_rows == 1


def create_replay_record(
    store: object,
    key: str,
    request: object,
    value: object,
) -> None:
    """Create one immutable Agentic replay request and outcome."""
    del key
    request_record = _model_value(store, "replay-request", request)
    outcome = _model_value(store, "replay", value)
    _execute(
        (
            "INSERT INTO agentic_operations_replays "
            "(replay_id, run_id, task_id, environment, requested_by, requested_at, "
            "verified_references_json, side_effects_attempted, executed, completed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(outcome, "replay_id"),
                _field(outcome, "run_id"),
                _field(request_record, "task_id"),
                _field(outcome, "environment"),
                _field(request_record, "requested_by"),
                _field(request_record, "requested_at"),
                _json(_field(outcome, "verified_references")),
                _field(outcome, "side_effects_attempted"),
                int(bool(_field(outcome, "executed"))),
                _field(outcome, "completed_at"),
            ),
        ),
    )


def create_workflow_run_reservation(
    store: object,
    *,
    idempotency_key: str,
    run_key: str,
    sequence: int,
    value: object,
) -> bool:
    """Atomically reserve idempotency identity and create a workflow run.

    Returns:
        Whether the unique workflow row was inserted.
    """
    del idempotency_key, run_key, sequence
    run = _model_value(store, "workflow-run", value)
    result = _execute(
        (
            "INSERT OR IGNORE INTO agentic_workflow_runs "
            "(run_id, task_id, workflow_name, workflow_version, state, "
            "current_node, sequence, revision, attempts, idempotency_key, "
            "created_at, updated_at, deadline_at, terminal_reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(run, "run_id"),
                _field(run, "task_id"),
                _field(run, "workflow_name"),
                _field(run, "workflow_version"),
                _field(run, "state"),
                _field(run, "current_node"),
                _field(run, "sequence"),
                _field(run, "revision"),
                _field(run, "attempts"),
                _field(run, "idempotency_key"),
                _field(run, "created_at"),
                _field(run, "updated_at"),
                _field(run, "deadline_at"),
                run.get("terminal_reason"),
            ),
        ),
    )
    return result.affected_rows == 1


def create_workflow_checkpoint_record(
    store: object,
    *,
    key: str,
    partition: str,
    sequence: int,
    value: object,
) -> None:
    """Append one immutable Agentic workflow checkpoint.

    Raises:
        TypeError: If the contract sequence is not an integer.
        ValueError: If the storage and contract sequence differ.
    """
    del key, partition
    checkpoint = _model_value(store, "checkpoint", value)
    checkpoint_sequence = _field(checkpoint, "sequence")
    if isinstance(checkpoint_sequence, bool) or not isinstance(
        checkpoint_sequence, int
    ):
        raise TypeError("Agentic checkpoint sequence must be an integer")
    if checkpoint_sequence + 1 != sequence:
        raise ValueError("Agentic checkpoint sequence is inconsistent")
    _execute(
        (
            "INSERT INTO agentic_workflow_checkpoints "
            "(checkpoint_id, task_id, workflow_name, workflow_version, node_id, "
            "sequence, state, expected_version, state_payload_hash, canonical_hash, "
            "contract_version, request_id, workflow_id, causation_id, schema_id, "
            "created_at, correlation_id) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _field(checkpoint, "checkpoint_id"),
                _field(checkpoint, "task_id"),
                _field(checkpoint, "workflow_name"),
                _field(checkpoint, "workflow_version"),
                _field(checkpoint, "node_id"),
                _field(checkpoint, "sequence"),
                _field(checkpoint, "state"),
                _field(checkpoint, "expected_version"),
                _field(checkpoint, "state_payload_hash"),
                _field(checkpoint, "canonical_hash"),
                _field(checkpoint, "contract_version"),
                _field(checkpoint, "request_id"),
                _field(checkpoint, "workflow_id"),
                checkpoint.get("causation_id"),
                _field(checkpoint, "schema_id"),
                _field(checkpoint, "created_at"),
                _field(checkpoint, "correlation_id"),
            ),
        ),
        request_id=str(_field(checkpoint, "request_id")),
    )


__all__ = [
    "create_agentic_persistence_store",
    "create_evidence_claim",
    "create_experiment_holdout_use",
    "create_experiment_run",
    "create_experiment_spec",
    "create_experiment_verdict",
    "create_incident_record",
    "create_lifecycle_packet_record",
    "create_lifecycle_record",
    "create_memory_record",
    "create_operation_trace_record",
    "create_replay_record",
    "create_workflow_checkpoint_record",
    "create_workflow_run_reservation",
]
