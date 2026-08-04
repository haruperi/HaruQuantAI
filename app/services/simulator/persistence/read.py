"""Read operations for Simulator-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.services.simulator.persistence.create import _execute, _require_store
from app.utils import get_logger

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
        "SELECT session_id, run_id, status, cursor, created_at, expires_at "
        "FROM sim_sessions WHERE session_id=?",
        (session_id,),
    )
    if row is None:
        return None
    return {
        "session_id": str(row["session_id"]),
        "run_id": str(row["run_id"]),
        "status": str(row["status"]),
        "cursor": int(str(row["cursor"])),
        "created_at": str(row["created_at"]),
        "expires_at": str(row["expires_at"]),
    }


__all__ = [
    "read_completed_run_record",
    "read_result_record",
    "read_run_record",
    "read_session_record",
]
