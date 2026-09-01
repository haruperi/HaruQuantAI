"""Read operations for Trading-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.composition.logging import get_logger
from app.services.trading.persistence.create import (
    _execute,
    _require_store,
)

logger = get_logger(__name__)

_SESSION_COLUMNS = (
    "session_id, principal_id, environment_id, name, description, mode, provider, "
    "provider_account_ref, credential_ref, simulation_session_id, sim_sequence, "
    "simulation_runtime_ref, dataset_ref, "
    "dataset_revision, dataset_hash, lifecycle_state, recovery_state, is_default, "
    "sim_initial_balance_decimal, sim_leverage, sim_account_currency, "
    "is_active, auto_start, metadata_json, last_error_code, last_reconciled_at, "
    "started_at, stopped_at, archived_at, version, created_at, updated_at"
)


def _session_row(row: Mapping[str, object]) -> Mapping[str, object]:
    """Decode one relational execution-session row.

    Returns:
        Decoded session dictionary.
    """
    result = dict(row)
    result["metadata"] = json.loads(str(result.pop("metadata_json")))
    result["sim_initial_balance"] = result.pop("sim_initial_balance_decimal")
    for field in ("is_default", "is_active", "auto_start"):
        result[field] = bool(result[field])
    return result


def read_execution_session_record(session_id: str) -> Mapping[str, object] | None:
    """Read one durable execution session, including archived records.

    Returns:
        Session record dictionary if found, otherwise None.
    """
    row = _one_row(
        f"SELECT {_SESSION_COLUMNS} FROM trading_sessions WHERE session_id=?",  # noqa: S608
        (session_id,),
    )
    return None if row is None else _session_row(row)


def read_execution_session_records(
    principal_id: str, environment_id: str, mode: str | None = None
) -> tuple[Mapping[str, object], ...]:
    """List non-archived execution sessions for one exact scope.

    Returns:
        Tuple of session record dictionaries.
    """
    mode_clause = "" if mode is None else " AND mode=?"
    parameters: tuple[object, ...] = (
        (principal_id, environment_id)
        if mode is None
        else (principal_id, environment_id, mode)
    )
    rows = _execute(
        (
            f"SELECT {_SESSION_COLUMNS} FROM trading_sessions WHERE principal_id=? "  # noqa: S608
            f"AND environment_id=? AND archived_at IS NULL{mode_clause} "
            "ORDER BY updated_at DESC",
        ),
        (parameters,),
        max_rows=1000,
    ).rows
    return tuple(_session_row(row) for row in rows)


def read_execution_session_events(session_id: str) -> tuple[Mapping[str, object], ...]:
    """Read bounded newest-first lifecycle events for one session.

    Returns:
        Tuple of event record dictionaries.
    """
    rows = _execute(
        (
            "SELECT event_id, session_id, sequence, event_type, payload_json, "
            "occurred_at, request_id FROM trading_session_events WHERE session_id=? "
            "ORDER BY sequence DESC",
        ),
        ((session_id,),),
        max_rows=1000,
    ).rows
    return tuple(
        {**row, "payload": json.loads(str(row["payload_json"]))} for row in rows
    )


def _one_row(
    statement: str,
    parameters: tuple[object, ...],
) -> Mapping[str, object] | None:
    """Read at most one normalized row.

    Args:
        statement: SQL query string.
        parameters: Tuple of query parameters.

    Returns:
        Stored row or ``None``.
    """
    rows = _execute((statement,), (parameters,)).rows
    return None if not rows else rows[0]


def _decode_reservation(store: object, row: Mapping[str, object]) -> object:
    """Reconstruct one validated reservation from relational columns.

    Args:
        store: Persistence handle object.
        row: Column mapping dictionary from relational query.

    Returns:
        Validated reservation value.
    """
    persistence = _require_store(store)

    return persistence.decode(
        "reservation",
        json.dumps(
            {
                "key": row["idempotency_key"],
                "material_hash": row["material_hash"],
                "material_version": row["material_version"],
                "status": row["status"],
                "reserved_at": row["created_at"],
                "expires_at": row["expires_at"],
                "receipt_id": row["receipt_id"],
            },
            separators=(",", ":"),
        ),
    )


def read_idempotency_record(store: object, key: str) -> object | None:
    """Read one idempotency reservation.

    Args:
        store: Persistence handle object.
        key: Idempotency reservation key string.

    Returns:
        Reservation or ``None``.
    """
    row = _one_row(
        "SELECT idempotency_key, material_hash, material_version, status, "
        "expires_at, receipt_id, created_at FROM trading_idempotency "
        "WHERE idempotency_key = ?",
        (key,),
    )
    return None if row is None else _decode_reservation(store, row)


def read_idempotency_record_with_revision(
    store: object,
    key: str,
) -> tuple[object, str] | None:
    """Read one reservation with its finite-state compare token.

    Args:
        store: Persistence handle object.
        key: Idempotency reservation key string.

    Returns:
        Reservation and token, or ``None``.
    """
    row = _one_row(
        "SELECT idempotency_key, material_hash, material_version, status, "
        "expires_at, receipt_id, created_at FROM trading_idempotency "
        "WHERE idempotency_key = ?",
        (key,),
    )
    if row is None:
        return None
    return _decode_reservation(store, row), str(row["status"])


def read_projection_record(store: object, key: str) -> object | None:
    """Read one exact-scope projection.

    Args:
        store: Persistence handle object.
        key: Scope key string.

    Returns:
        Projection or ``None``.
    """
    row = _one_row(
        "SELECT projection_json FROM trading_projections WHERE scope_key = ?",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("projection", str(row["projection_json"]))


def read_projection_record_with_revision(
    store: object,
    key: str,
) -> tuple[object, int] | None:
    """Read one exact-scope projection and optimistic version.

    Args:
        store: Persistence handle object.
        key: Scope key string.

    Returns:
        Projection and version, or ``None``.
    """
    row = _one_row(
        "SELECT projection_json, projection_version FROM trading_projections "
        "WHERE scope_key = ?",
        (key,),
    )
    if row is None:
        return None
    value = _require_store(store).decode("projection", str(row["projection_json"]))
    return value, int(str(row["projection_version"]))


def read_event_records(store: object, partition: str) -> tuple[object, ...]:
    """Read ordered Trading events for one exact-scope partition.

    Args:
        store: Persistence handle object.
        partition: Partition scope string.

    Returns:
        Ordered decoded events.
    """
    rows = _execute(
        (
            "SELECT payload_json FROM trading_events WHERE scope_key = ? "
            "ORDER BY aggregate_version ASC LIMIT 1000",
        ),
        ((partition,),),
        max_rows=1_000,
    ).rows
    persistence = _require_store(store)
    return tuple(persistence.decode("event", str(row["payload_json"])) for row in rows)


def read_all_event_records(store: object, limit: int) -> tuple[object, ...]:
    """Read bounded Trading events across all exact-scope partitions.

    Args:
        store: Persistence handle object.
        limit: Maximum number of events to return.

    Returns:
        Ordered decoded events.

    Raises:
        ValueError: If the bound is not positive.
    """
    if limit <= 0:
        raise ValueError("Trading event read limit must be positive")
    rows = _execute(
        ("SELECT payload_json FROM trading_events ORDER BY event_seq ASC LIMIT ?",),
        ((limit,),),
        max_rows=limit,
    ).rows
    persistence = _require_store(store)
    return tuple(persistence.decode("event", str(row["payload_json"])) for row in rows)


__all__ = [
    "read_all_event_records",
    "read_event_records",
    "read_idempotency_record",
    "read_idempotency_record_with_revision",
    "read_projection_record",
    "read_projection_record_with_revision",
]
