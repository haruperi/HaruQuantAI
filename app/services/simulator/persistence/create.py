"""Create operations for Simulator-owned relational records."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import canonical_json, generate_id, get_logger

logger = get_logger(__name__)


class _TransactionResult(Protocol):
    """Data transaction fields consumed by Simulator persistence."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


@dataclass(frozen=True)
class _SimulatorPersistenceStore:
    """Opaque Simulator result decoder without a database connection."""

    result_decoder: Callable[[str], object]


def _require_store(store: object) -> _SimulatorPersistenceStore:
    """Return a validated private Simulator persistence handle.

    Raises:
        TypeError: If the handle is not Simulator-owned.
    """
    if not isinstance(store, _SimulatorPersistenceStore):
        raise TypeError("invalid Simulator persistence store")
    return store


def _execute(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    max_rows: int = 1,
    request_id: str | None = None,
) -> _TransactionResult:
    """Execute one bounded relational plan through Data.

    Returns:
        Confirmed normalized transaction result.

    Raises:
        ValueError: If Data cannot confirm the transaction.
    """
    operation_id = request_id or generate_id("req")
    response = execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=statements,
                parameter_sets=parameter_sets,
                max_rows=max_rows,
            ),
            request_id=operation_id,
        )
    )
    if response.status != "success" or response.data is None:
        raise ValueError("Simulator persistence transaction failed")
    return cast("_TransactionResult", response.data)


def _run_value(value: object) -> Mapping[str, object]:
    """Return one validated run-lifecycle mapping.

    Raises:
        TypeError: If the value is not a mapping.
    """
    if not isinstance(value, Mapping):
        raise TypeError("Simulator run value must be a mapping")
    return cast("Mapping[str, object]", value)


def _text_field(value: Mapping[str, object], field: str) -> str:
    """Return one required nonempty textual field.

    Raises:
        TypeError: If the field is not text.
    """
    item = value.get(field)
    if not isinstance(item, str) or not item:
        message = f"Simulator run field {field} must be text"
        raise TypeError(message)
    return item


def _result_json(value: Mapping[str, object]) -> str | None:
    """Serialize an optional completed-result payload.

    Returns:
        Canonical result JSON or ``None``.

    Raises:
        TypeError: If result material is not a mapping.
    """
    result = value.get("result_payload")
    if result is None:
        return None
    if not isinstance(result, Mapping):
        raise TypeError("Simulator result payload must be a mapping")
    return canonical_json(dict(result), max_items=None)


def create_simulator_persistence_store(
    result_decoder: Callable[[str], object],
) -> object:
    """Create an opaque Simulator relational-store handle.

    Args:
        result_decoder: Validating decoder for completed result contracts.

    Returns:
        Opaque Simulator persistence handle.
    """
    logger.debug("Creating Simulator relational persistence handle")
    return _SimulatorPersistenceStore(result_decoder)


def create_run_record(store: object, key: str, value: object) -> None:
    """Create one initial Simulator run row idempotently.

    Args:
        store: Opaque Simulator persistence handle.
        key: Canonical request identifier.
        value: Validated run lifecycle state.

    Raises:
        ValueError: If the identity conflicts with different stored material.
    """
    _require_store(store)
    run = _run_value(value)
    request_id = _text_field(run, "request_id")
    if request_id != key:
        raise ValueError("Simulator request identity is inconsistent")
    request_hash = _text_field(run, "request_hash")
    run_id = _text_field(run, "run_id")
    status = _text_field(run, "status")
    result_json = _result_json(run)
    _execute(
        (
            "INSERT INTO sim_runs "
            "(request_id, request_hash, run_id, status, result_payload) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(request_id) DO UPDATE SET request_hash=CASE WHEN "
            "sim_runs.request_hash=excluded.request_hash AND "
            "sim_runs.run_id=excluded.run_id AND sim_runs.status=excluded.status AND "
            "COALESCE(sim_runs.result_payload, '')="
            "COALESCE(excluded.result_payload, '') THEN excluded.request_hash "
            "ELSE NULL END",
        ),
        ((request_id, request_hash, run_id, status, result_json),),
        request_id=request_id,
    )


def create_session_record(
    store: object,
    value: Mapping[str, object],
    *,
    request_id: str,
) -> None:
    """Create one immutable-identity playback session row.

    Args:
        store: Opaque Simulator persistence handle.
        value: Validated session fields.
        request_id: Trace identifier for the delegated transaction.

    Raises:
        ValueError: If the session cannot be inserted exactly once.
    """
    _require_store(store)
    result = _execute(
        (
            "INSERT INTO sim_sessions "
            "(session_id, run_id, status, cursor, created_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                _text_field(value, "session_id"),
                _text_field(value, "run_id"),
                _text_field(value, "status"),
                value["cursor"],
                _text_field(value, "created_at"),
                _text_field(value, "expires_at"),
            ),
        ),
        request_id=request_id,
    )
    if result.affected_rows != 1:
        raise ValueError("Simulator playback session was not created")


__all__ = [
    "create_run_record",
    "create_session_record",
    "create_simulator_persistence_store",
]
