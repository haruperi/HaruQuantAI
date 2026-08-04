"""Update operations for Simulator-owned relational records."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.simulator.persistence.create import (
    _execute,
    _require_store,
    _result_json,
    _run_value,
    _text_field,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)


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


__all__ = ["complete_run_record", "update_run_record", "update_session_record"]
