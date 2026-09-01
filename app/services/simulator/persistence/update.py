"""Update operations for Simulator-owned relational records."""

from __future__ import annotations

from collections.abc import Mapping

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json
from app.services.simulator.persistence.create import (
    _execute,
    _require_store,
    _result_json,
    _run_value,
    _text_field,
)

logger = get_logger(__name__)


def append_interactive_intent_and_checkpoint(
    store: object,
    *,
    intent: Mapping[str, object],
    checkpoint: Mapping[str, object],
    request_id: str,
) -> bool:
    """Atomically append one manual intent and advance its session checkpoint.

    Args:
        store: Opaque Simulator persistence handle.
        intent: Immutable cursor-bound intent row.
        checkpoint: Replacement session checkpoint fields.
        request_id: Trace identifier.

    Returns:
        Whether both statements completed in one Data-owned transaction.
    """
    _require_store(store)
    result = _execute(
        (
            "INSERT INTO sim_interactive_intents "
            "(session_id, sequence, accepted_cursor, intent_json, intent_hash, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(session_id, intent_hash) DO NOTHING",
            "UPDATE sim_interactive_sessions SET cursor=?, status=?, "
            "state_hash=?, recovery_generation=?, recovery_run_id=?, updated_at=? "
            "WHERE session_id=? AND cursor<=?",
        ),
        (
            (
                _text_field(intent, "session_id"),
                intent["sequence"],
                intent["accepted_cursor"],
                canonical_json(intent["intent"], max_items=None),
                _text_field(intent, "intent_hash"),
                _text_field(intent, "created_at"),
            ),
            (
                checkpoint["cursor"],
                _text_field(checkpoint, "status"),
                _text_field(checkpoint, "state_hash"),
                checkpoint["recovery_generation"],
                checkpoint.get("recovery_run_id"),
                _text_field(checkpoint, "updated_at"),
                _text_field(checkpoint, "session_id"),
                checkpoint["cursor"],
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows in {1, 2}


def update_run_record(
    store: object,
    *,
    key: str,
    value: object,
    expected_status: str,
    expected_result_payload: Mapping[str, object] | None,
) -> bool:
    """Compare-and-swap one Simulator run lifecycle row.

    Args:
        store: Opaque Simulator persistence handle.
        key: Canonical request identifier.
        value: Replacement run lifecycle state.
        expected_status: Caller-observed lifecycle status.
        expected_result_payload: Caller-observed result material.

    Returns:
        Whether exactly one identity-bound row was updated.

    Raises:
        ValueError: If request identity is inconsistent.
    """
    _require_store(store)
    run = _run_value(value)
    request_id = _text_field(run, "request_id")
    if request_id != key:
        raise ValueError("Simulator request identity is inconsistent")
    prior_json = (
        None
        if expected_result_payload is None
        else canonical_json(dict(expected_result_payload), max_items=None)
    )
    result = _execute(
        (
            "UPDATE sim_runs SET status=?, result_payload=?, "
            "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ', 'now') "
            "WHERE request_id=? AND request_hash=? AND run_id=? AND status=? AND "
            "COALESCE(result_payload, '')=COALESCE(?, '')",
        ),
        (
            (
                _text_field(run, "status"),
                _result_json(run),
                request_id,
                _text_field(run, "request_hash"),
                _text_field(run, "run_id"),
                expected_status,
                prior_json,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows == 1


def complete_run_record(
    store: object,
    *,
    key: str,
    value: object,
    expected_status: str,
    expected_result_payload: Mapping[str, object] | None,
) -> None:
    """Atomically complete one run with its immutable result payload.

    Args:
        store: Opaque Simulator persistence handle.
        key: Canonical request identifier.
        value: Completed lifecycle state and result.
        expected_status: Caller-observed lifecycle status.
        expected_result_payload: Caller-observed result material.

    Raises:
        ValueError: If the identity or prior state changed concurrently.
    """
    logger.debug("Completing Simulator run and result atomically")
    if not update_run_record(
        store,
        key=key,
        value=value,
        expected_status=expected_status,
        expected_result_payload=expected_result_payload,
    ):
        raise ValueError("Simulator run completion state conflict")


def update_session_record(
    store: object,
    *,
    session_id: str,
    status: str,
    cursor: int,
    request_id: str,
) -> bool:
    """Advance one playback session without regressing its cursor.

    Args:
        store: Opaque Simulator persistence handle.
        session_id: Stable playback-session identity.
        status: Replacement lifecycle status.
        cursor: Greatest journal sequence delivered so far.
        request_id: Trace identifier for the delegated transaction.

    Returns:
        Whether one session row was updated.

    Raises:
        ValueError: If the status or cursor is invalid.
    """
    _require_store(store)
    if status not in {"active", "completed", "expired"} or cursor < -1:
        raise ValueError("Simulator playback session update is invalid")
    result = _execute(
        ("UPDATE sim_sessions SET status=?, cursor=MAX(cursor, ?) WHERE session_id=?",),
        ((status, cursor, session_id),),
        request_id=request_id,
    )
    return result.affected_rows == 1


def update_secured_session_record(
    store: object,
    *,
    session_id: str,
    mode: str,
    recovery_state: str,
    secured_at: str,
    state: Mapping[str, object],
    request_id: str,
) -> bool:
    """Replace one secured session's validated aggregate projection.

    Args:
        store: Opaque Simulator persistence handle.
        session_id: Stable session identity.
        mode: Supported simulation mode.
        recovery_state: Current recovery lifecycle state.
        secured_at: Aware canonical timestamp text.
        state: Aggregate state mappings.
        request_id: Trace identifier for transaction execution.

    Returns:
        Whether exactly one session row was updated.
    """
    _require_store(store)
    fields = (
        "clock_state",
        "scenario_state",
        "replay_identity",
        "checklist_state",
        "alert_state",
        "emergency_state",
        "counters",
        "branch_lineage",
    )
    payloads = tuple(
        canonical_json(state.get(field, {}), max_items=None) for field in fields
    )
    result = _execute(
        (
            "UPDATE sim_sessions SET session_kind='secured', mode=?, "
            "recovery_state=?, secured_at=?, clock_state_json=?, "
            "scenario_state_json=?, replay_identity_json=?, checklist_state_json=?, "
            "alert_state_json=?, emergency_state_json=?, counters_json=?, "
            "branch_lineage_json=? WHERE session_id=?",
        ),
        ((mode, recovery_state, secured_at, *payloads, session_id),),
        request_id=request_id,
    )
    return result.affected_rows == 1


def update_interactive_session_record(
    store: object,
    *,
    session_id: str,
    cursor: int,
    status: str,
    state_hash: str,
    recovery_generation: int,
    recovery_run_id: str | None,
    updated_at: str,
    request_id: str,
) -> bool:
    """Compare-and-advance one interactive recovery checkpoint.

    Returns:
        Whether exactly one session row was advanced.
    """
    _require_store(store)
    result = _execute(
        (
            "UPDATE sim_interactive_sessions SET cursor=?, status=?, "
            "state_hash=?, recovery_generation=?, recovery_run_id=?, updated_at=? "
            "WHERE session_id=? AND cursor<=?",
        ),
        (
            (
                cursor,
                status,
                state_hash,
                recovery_generation,
                recovery_run_id,
                updated_at,
                session_id,
                cursor,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows == 1


__all__ = [
    "append_interactive_intent_and_checkpoint",
    "complete_run_record",
    "update_interactive_session_record",
    "update_run_record",
    "update_secured_session_record",
    "update_session_record",
]
