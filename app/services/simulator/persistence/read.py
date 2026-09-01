"""Read operations for Simulator-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.composition.logging import get_logger
from app.services.simulator.persistence.create import _execute, _require_store

logger = get_logger(__name__)


def _one_row(
    statement: str, parameters: tuple[object, ...]
) -> Mapping[str, object] | None:
    """Read at most one normalized row.

    Returns:
        Stored row or ``None``.
    """
    rows = _execute((statement,), (parameters,)).rows
    return None if not rows else rows[0]


def _decode_payload(payload: object) -> Mapping[str, object] | None:
    """Decode one optional result mapping.

    Returns:
        Decoded result mapping or ``None``.

    Raises:
        TypeError: If stored result material is not an object.
    """
    if payload is None:
        return None
    decoded = json.loads(str(payload))
    if not isinstance(decoded, dict):
        raise TypeError("stored Simulator result payload is malformed")
    return decoded


def read_run_record(store: object, key: str) -> Mapping[str, object] | None:
    """Read one Simulator run row by request identity.

    Returns:
        Normalized lifecycle mapping or ``None``.
    """
    _require_store(store)
    row = _one_row(
        "SELECT request_id, request_hash, run_id, status, result_payload "
        "FROM sim_runs WHERE request_id=?",
        (key,),
    )
    if row is None:
        return None
    return {
        "request_id": str(row["request_id"]),
        "request_hash": str(row["request_hash"]),
        "run_id": str(row["run_id"]),
        "status": str(row["status"]),
        "result_payload": _decode_payload(row.get("result_payload")),
    }


def read_result_record(store: object, run_id: str) -> object | None:
    """Read one validated completed result by canonical run ID.

    Returns:
        Validated completed result or ``None``.
    """
    row = _one_row(
        "SELECT result_payload FROM sim_runs WHERE run_id=? AND "
        "status='completed' AND result_payload IS NOT NULL",
        (run_id,),
    )
    if row is None:
        return None
    return _require_store(store).result_decoder(str(row["result_payload"]))


def read_completed_run_record(store: object, run_id: str) -> bool:
    """Return whether a completed canonical run exists.

    Args:
        store: Opaque Simulator persistence handle.
        run_id: Canonical run identity.

    Returns:
        Whether the run exists in completed state.
    """
    _require_store(store)
    return (
        _one_row(
            "SELECT run_id FROM sim_runs WHERE run_id=? AND status='completed'",
            (run_id,),
        )
        is not None
    )


def read_session_record(store: object, session_id: str) -> Mapping[str, object] | None:
    """Read one Simulator playback session.

    Args:
        store: Opaque Simulator persistence handle.
        session_id: Stable playback-session identity.

    Returns:
        Normalized session row or ``None``.
    """
    _require_store(store)
    row = _one_row(
        "SELECT session_id, run_id, status, cursor, created_at, expires_at, "
        "session_kind, mode, recovery_state, secured_at, clock_state_json, "
        "scenario_state_json, replay_identity_json, checklist_state_json, "
        "alert_state_json, emergency_state_json, counters_json, branch_lineage_json "
        "FROM sim_sessions WHERE session_id=?",
        (session_id,),
    )
    if row is None:
        return None
    result: dict[str, object] = {
        "session_id": str(row["session_id"]),
        "run_id": str(row["run_id"]),
        "status": str(row["status"]),
        "cursor": int(str(row["cursor"])),
        "created_at": str(row["created_at"]),
        "expires_at": str(row["expires_at"]),
        "session_kind": str(row["session_kind"]),
        "mode": str(row["mode"]),
        "recovery_state": str(row["recovery_state"]),
        "secured_at": None if row.get("secured_at") is None else str(row["secured_at"]),
    }
    for field in (
        "clock_state",
        "scenario_state",
        "replay_identity",
        "checklist_state",
        "alert_state",
        "emergency_state",
        "counters",
        "branch_lineage",
    ):
        result[field] = _decode_payload(row[f"{field}_json"]) or {}
    return result


def read_recovery_checkpoint_records(
    store: object, session_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read one session's ordered immutable recovery checkpoints.

    Args:
        store: Opaque Simulator persistence handle.
        session_id: Secured simulation-session identity.

    Returns:
        Ordered normalized checkpoint mappings.
    """
    _require_store(store)
    rows = _execute(
        (
            "SELECT session_id, sequence, checkpoint_hash, previous_hash, "
            "replay_identity_json, state_payload_json, created_at "
            "FROM sim_session_checkpoints WHERE session_id=? ORDER BY sequence",
        ),
        ((session_id,),),
        max_rows=10_000,
    ).rows
    return tuple(
        {
            "session_id": str(row["session_id"]),
            "sequence": int(str(row["sequence"])),
            "checkpoint_hash": str(row["checkpoint_hash"]),
            "previous_hash": (
                None if row.get("previous_hash") is None else str(row["previous_hash"])
            ),
            "replay_identity": _decode_payload(row["replay_identity_json"]),
            "state_payload": _decode_payload(row["state_payload_json"]),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    )


def read_interactive_session_record(
    store: object, session_id: str
) -> Mapping[str, object] | None:
    """Read one durable interactive-session recovery record.

    Returns:
        Normalized session row, or ``None`` when absent.
    """
    _require_store(store)
    row = _one_row(
        "SELECT session_id, run_id, request_json, cursor, status, state_hash, "
        "recovery_generation, recovery_run_id, created_at, updated_at "
        "FROM sim_interactive_sessions WHERE session_id=?",
        (session_id,),
    )
    if row is None:
        return None
    return {
        "session_id": str(row["session_id"]),
        "run_id": str(row["run_id"]),
        "request": _decode_payload(row["request_json"]),
        "cursor": int(str(row["cursor"])),
        "status": str(row["status"]),
        "state_hash": str(row["state_hash"]),
        "recovery_generation": int(str(row["recovery_generation"])),
        "recovery_run_id": (
            None if row.get("recovery_run_id") is None else str(row["recovery_run_id"])
        ),
        "created_at": str(row["created_at"]),
        "updated_at": str(row["updated_at"]),
    }


def read_interactive_intent_records(
    store: object, session_id: str
) -> tuple[Mapping[str, object], ...]:
    """Read cursor-bound manual intents in deterministic replay order.

    Returns:
        Ordered immutable intent rows.
    """
    _require_store(store)
    rows = _execute(
        (
            "SELECT session_id, sequence, accepted_cursor, intent_json, "
            "intent_hash, created_at FROM sim_interactive_intents "
            "WHERE session_id=? ORDER BY accepted_cursor, sequence",
        ),
        ((session_id,),),
        max_rows=100_000,
    ).rows
    return tuple(
        {
            "session_id": str(row["session_id"]),
            "sequence": int(str(row["sequence"])),
            "accepted_cursor": int(str(row["accepted_cursor"])),
            "intent": _decode_payload(row["intent_json"]),
            "intent_hash": str(row["intent_hash"]),
            "created_at": str(row["created_at"]),
        }
        for row in rows
    )


__all__ = [
    "read_completed_run_record",
    "read_interactive_intent_records",
    "read_interactive_session_record",
    "read_recovery_checkpoint_records",
    "read_result_record",
    "read_run_record",
    "read_session_record",
]
