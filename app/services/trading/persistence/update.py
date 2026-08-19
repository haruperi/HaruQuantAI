"""Atomic update operations for Trading-owned relational records."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.services.trading.persistence.create import (
    _EventValue,
    _execute,
    _ProjectionValue,
    _require_store,
    _ReservationValue,
)
from app.utils import get_logger

logger = get_logger(__name__)
_MIN_ATOMIC_AFFECTED_ROWS = 2

_ORDER_COLUMNS = (
    "order_id, client_order_id, broker_order_id, account_id, symbol_id, "
    "strategy_version_id, config_id, signal_id, risk_decision_id, side, "
    "order_type, time_in_force, quantity_decimal, filled_qty_decimal, "
    "limit_price_decimal, stop_price_decimal, avg_fill_price_decimal, "
    "stop_loss_decimal, take_profit_decimal, state, reject_reason, "
    "runtime_profile, submitted_at, terminal_at, correlation_id, created_at, "
    "updated_at"
)


def _append_session_event(
    session_id: str,
    event_type: str,
    payload: dict[str, object],
    request_id: str,
    expected_version: int,
) -> tuple[str, tuple[object, ...]]:
    """Build a revision-conditional lifecycle-event append.

    Returns:
        Parameterized SQL and bound values.
    """
    from app.utils import generate_id

    return (
        "INSERT INTO trading_session_events "
        "(event_id, session_id, sequence, event_type, payload_json, occurred_at, "
        "request_id) SELECT ?, ?, (SELECT COALESCE(MAX(sequence), -1) + 1 "
        "FROM trading_session_events WHERE session_id=?), ?, ?, ?, ? "
        "WHERE EXISTS (SELECT 1 FROM trading_sessions "
        "WHERE session_id=? AND version=?)",
        (
            generate_id("evt"),
            session_id,
            session_id,
            event_type,
            json.dumps(payload, separators=(",", ":")),
            datetime.now(UTC).isoformat(),
            request_id,
            session_id,
            expected_version,
        ),
    )


def update_execution_session_record(
    session_id: str,
    *,
    expected_version: int,
    changes: dict[str, object],
    event_type: str,
    request_id: str,
) -> None:
    """Compare-and-swap allowlisted session columns and append an event.

    Raises:
        ValueError: If the update is unsupported or its revision is stale.
    """
    allowed = {
        "name",
        "description",
        "auto_start",
        "metadata",
        "lifecycle_state",
        "recovery_state",
        "is_active",
        "last_error_code",
        "last_reconciled_at",
        "started_at",
        "stopped_at",
        "archived_at",
        "updated_at",
        "simulation_session_id",
        "simulation_runtime_ref",
        "provider_account_ref",
        "dataset_ref",
        "dataset_revision",
        "dataset_hash",
    }
    if not changes or not set(changes).issubset(allowed):
        raise ValueError("unsupported execution session update")
    columns: list[str] = []
    values: list[object] = []
    for key, raw_value in changes.items():
        column = "metadata_json" if key == "metadata" else key
        columns.append(f"{column}=?")
        value = raw_value
        if key == "metadata":
            value = json.dumps(value, separators=(",", ":"))
        elif key in {"auto_start", "is_active"}:
            value = int(bool(value))
        values.append(value)
    columns.extend(("version=version+1",))
    event_sql, event_params = _append_session_event(
        session_id,
        event_type,
        {key: str(value) for key, value in changes.items()},
        request_id,
        expected_version + 1,
    )
    result = _execute(
        (
            f"UPDATE trading_sessions SET {', '.join(columns)} "  # noqa: S608
            "WHERE session_id=? AND version=? AND archived_at IS NULL",
            event_sql,
        ),
        ((*values, session_id, expected_version), event_params),
        request_id=request_id,
    )
    if result.affected_rows != _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("Trading execution session revision conflict")


def assign_simulation_session_identity_record(
    session_id: str,
    *,
    expected_version: int,
    username: str,
    request_id: str,
) -> None:
    """Allocate one monotonic per-principal SIM identity atomically.

    Args:
        session_id: Durable Trading session identifier.
        expected_version: Optimistic session revision.
        username: Identifier-safe authenticated login name.
        request_id: Caller trace identifier.

    Raises:
        ValueError: If allocation loses its revision race or is inapplicable.
    """
    next_sequence = (
        "(SELECT COALESCE(MAX(s.sim_sequence), 0) + 1 FROM trading_sessions AS s "
        "WHERE s.principal_id=(SELECT principal_id FROM trading_sessions "
        "WHERE session_id=?))"
    )
    now = datetime.now(UTC).isoformat()
    event_sql, event_params = _append_session_event(
        session_id,
        "simulation_identity_assigned",
        {"username": username},
        request_id,
        expected_version + 1,
    )
    result = _execute(
        (
            "UPDATE trading_sessions SET "  # noqa: S608
            f"sim_sequence={next_sequence}, "
            f"simulation_session_id=? || '_' || {next_sequence}, "
            "provider_account_ref=?, "
            "version=version+1, updated_at=? WHERE session_id=? AND version=? "
            "AND mode='sim' AND simulation_session_id IS NULL",
            event_sql,
        ),
        (
            (
                session_id,
                username,
                session_id,
                username,
                now,
                session_id,
                expected_version,
            ),
            event_params,
        ),
        request_id=request_id,
    )
    if result.affected_rows != _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("SIM session identity allocation conflict")


def complete_simulation_session_configuration_record(
    session_id: str,
    *,
    expected_version: int,
    username: str,
    account_name: str,
    dataset_ref: str,
    dataset_revision: str,
    dataset_hash: str,
    request_id: str,
) -> None:
    """Atomically complete identity and dataset lineage for a stopped legacy SIM.

    Raises:
        ValueError: If the session is running, unavailable, or revision-stale.
    """
    next_sequence = (
        "(SELECT COALESCE(MAX(s.sim_sequence), 0) + 1 FROM trading_sessions AS s "
        "WHERE s.principal_id=(SELECT principal_id FROM trading_sessions "
        "WHERE session_id=?))"
    )
    now = datetime.now(UTC).isoformat()
    event_sql, event_params = _append_session_event(
        session_id,
        "configuration_completed",
        {"account_name": account_name, "dataset_ref": dataset_ref},
        request_id,
        expected_version + 1,
    )
    statement = (
        "UPDATE trading_sessions SET "  # noqa: S608 - fixed internal fragments.
        f"sim_sequence=COALESCE(sim_sequence, {next_sequence}), "
        "simulation_session_id=COALESCE(simulation_session_id, ? || '_' || "
        f"{next_sequence}), "
        "provider_account_ref=?, dataset_ref=?, dataset_revision=?, "
        "dataset_hash=?, version=version+1, updated_at=? "
        "WHERE session_id=? AND version=? AND mode='sim' AND is_active=0 "
        "AND lifecycle_state IN ('draft','stopped','error','verified')"
    )
    result = _execute(
        (
            statement,
            event_sql,
        ),
        (
            (
                session_id,
                username,
                session_id,
                account_name,
                dataset_ref,
                dataset_revision,
                dataset_hash,
                now,
                session_id,
                expected_version,
            ),
            event_params,
        ),
        request_id=request_id,
    )
    if result.affected_rows != _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("legacy SIM configuration requires a stopped current revision")


def set_default_execution_session_record(
    session_id: str, *, expected_version: int, request_id: str
) -> None:
    """Atomically replace the default session within one mode and scope.

    Raises:
        ValueError: If the session is unavailable or its revision is stale.
    """
    from app.services.trading.persistence.read import read_execution_session_record

    current = read_execution_session_record(session_id)
    if current is None or current["lifecycle_state"] == "archived":
        raise ValueError("execution session is unavailable")
    now = datetime.now(UTC).isoformat()
    event_sql, event_params = _append_session_event(
        session_id, "default_selected", {}, request_id, expected_version + 1
    )
    result = _execute(
        (
            "UPDATE trading_sessions SET is_default=0, version=version+1, updated_at=? "
            "WHERE principal_id=? AND environment_id=? AND mode=? AND is_default=1 "
            "AND session_id<>?",
            "UPDATE trading_sessions SET is_default=1, version=version+1, updated_at=? "
            "WHERE session_id=? AND version=? AND archived_at IS NULL",
            event_sql,
        ),
        (
            (
                now,
                current["principal_id"],
                current["environment_id"],
                current["mode"],
                session_id,
            ),
            (now, session_id, expected_version),
            event_params,
        ),
        request_id=request_id,
    )
    if result.affected_rows < _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("Trading default session revision conflict")


def update_idempotency_record(
    store: object,
    *,
    key: str,
    value: _ReservationValue,
    expected_revision: object,
) -> None:
    """Compare and swap one idempotency reservation by finite state.

    Args:
        store: Persistence handle object.
        key: Idempotency reservation key string.
        value: Reservation value object.
        expected_revision: Revision object expected to match current state.

    Raises:
        ValueError: If the stored state no longer matches.
    """
    _require_store(store)
    result = _execute(
        (
            "UPDATE trading_idempotency SET status = ?, receipt_id = ?, "
            "updated_at = ? WHERE idempotency_key = ? AND status = ?",
        ),
        (
            (
                value.status,
                value.receipt_id,
                value.reserved_at.isoformat(),
                key,
                expected_revision,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Trading idempotency revision conflict")


def update_projection_record(
    store: object,
    *,
    key: str,
    value: _ProjectionValue,
    expected_revision: int,
) -> None:
    """Compare and swap one exact-scope projection.

    A stale version is deliberately mapped to ``-1`` so the table constraint
    aborts and rolls back the transaction rather than committing a zero-row CAS.

    Args:
        store: Persistence handle object.
        key: Scope key string.
        value: Projection value object.
        expected_revision: Revision integer expected to match current state.

    Raises:
        ValueError: If the projection version no longer matches.
    """
    persistence = _require_store(store)
    updated_at = value.updated_at.isoformat()
    result = _execute(
        (
            "UPDATE trading_projections SET projection_version = CASE "
            "WHEN projection_version = ? THEN ? ELSE -1 END, "
            "last_event_seq = ?, projection_json = ?, updated_at = ? "
            "WHERE scope_key = ?",
        ),
        (
            (
                expected_revision,
                value.version,
                value.version,
                persistence.encode("projection", value),
                updated_at,
                key,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Trading projection revision conflict")


def _event_statement(
    store: object,
    event: _EventValue,
    scope_key: str,
) -> tuple[str, tuple[object, ...]]:
    """Build the authoritative event append statement and parameters.

    Args:
        store: Persistence handle object.
        event: Event value object.
        scope_key: Partition scope key string.

    Returns:
        Parameterized SQL and its bound values.
    """
    persistence = _require_store(store)
    occurred_at = event.occurred_at
    return (
        "INSERT INTO trading_events "
        "(event_id, event_type, event_version, scope_key, aggregate_version, "
        "occurred_at, payload_json, correlation_id, causation_id, bucket_year, "
        "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            event.event_id,
            event.event_type,
            event.event_version,
            scope_key,
            event.aggregate_version,
            occurred_at.isoformat(),
            persistence.encode("event", event),
            event.correlation_id,
            event.causation_id,
            f"{occurred_at.year:04d}",
            occurred_at.isoformat(),
        ),
    )


def _projection_statement(
    store: object,
    projection: _ProjectionValue,
    scope_key: str,
    expected_version: int,
    event_id: str,
) -> tuple[str, tuple[object, ...]]:
    """Build a constraint-backed optimistic projection upsert.

    Args:
        store: Persistence handle object.
        projection: Projection value object.
        scope_key: Scope key string.
        expected_version: Expected projection version integer.
        event_id: Associated event ID string.

    Returns:
        Parameterized SQL and its bound values.
    """
    persistence = _require_store(store)
    updated_at = projection.updated_at.isoformat()
    return (
        "INSERT INTO trading_projections "
        "(scope_key, projection_version, last_event_seq, projection_json, "
        "created_at, updated_at) VALUES (?, ?, "
        "(SELECT event_seq FROM trading_events WHERE event_id = ?), ?, ?, ?) "
        "ON CONFLICT(scope_key) DO UPDATE SET "
        "projection_version = CASE WHEN trading_projections.projection_version = ? "
        "THEN excluded.projection_version ELSE -1 END, "
        "last_event_seq = excluded.last_event_seq, "
        "projection_json = excluded.projection_json, updated_at = excluded.updated_at",
        (
            scope_key,
            projection.version,
            event_id,
            persistence.encode("projection", projection),
            updated_at,
            updated_at,
            expected_version,
        ),
    )


def update_event_projection_records(
    store: object,
    *,
    event: object,
    projection: object,
    scope_key: str,
    expected_version: int,
) -> None:
    """Atomically append an event, save its projection, and materialize facts.

    Args:
        store: Persistence handle object.
        event: TradingEvent instance.
        projection: TradingProjection instance.
        scope_key: Scope key string.
        expected_version: Expected projection version integer.

    Raises:
        TypeError: If state values are not validated Trading contracts.
        ValueError: If mapping or transactional persistence fails.
    """
    from app.services.trading.state.events import TradingEvent
    from app.services.trading.state.materializations import build_materialization_batch
    from app.services.trading.state.projections import TradingProjection

    if not isinstance(event, TradingEvent) or not isinstance(
        projection, TradingProjection
    ):
        raise TypeError("Trading atomic persistence requires validated state")
    batch = build_materialization_batch(event, projection)
    statements: list[str] = []
    parameters: list[tuple[object, ...]] = []
    for statement, values in (
        _event_statement(store, event, scope_key),
        _projection_statement(
            store,
            projection,
            scope_key,
            expected_version,
            event.event_id,
        ),
    ):
        statements.append(statement)
        parameters.append(values)

    if batch.order is not None:
        statements.append(
            f"INSERT INTO trading_orders ({_ORDER_COLUMNS}) "  # noqa: S608
            f"VALUES ({', '.join('?' for _ in batch.order.values)})"
        )
        parameters.append(batch.order.values)

    if batch.outcome is not None:
        outcome = batch.outcome
        if outcome.lookup_by_broker_id:
            lookup = "broker_order_id = ?"
        else:
            lookup = "order_id = ?"
        # Empty order identity violates the table check and rolls back when the
        # receipt cannot be tied to an already-materialized order.
        statements.append(
            "UPDATE trading_orders SET broker_order_id = COALESCE(?, broker_order_id), "  # noqa: S608
            "state = ?, filled_qty_decimal = ?, avg_fill_price_decimal = ?, "
            "reject_reason = ?, terminal_at = ?, updated_at = ? "
            f"WHERE {lookup}"
        )
        parameters.append(
            (
                outcome.broker_order_id,
                outcome.state,
                outcome.filled_quantity,
                outcome.average_price,
                outcome.reject_reason,
                outcome.terminal_at,
                outcome.updated_at,
                outcome.order_id,
            )
        )

    if batch.transition is not None:
        statements.append(
            "INSERT INTO trading_order_transitions "
            "(transition_id, order_id, from_state, to_state, source_sequence, "
            "reason_code, occurred_at, correlation_id, causation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        parameters.append(batch.transition.values)

    if batch.fill is not None:
        statements.append(
            "INSERT INTO trading_fills "
            "(fill_id, order_id, broker_fill_id, source_sequence, "
            "quantity_decimal, price_decimal, fee_estimate_decimal, executed_at, "
            "correlation_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        parameters.append(batch.fill.values)

    result = _execute(tuple(statements), tuple(parameters))
    if result.affected_rows < _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("Trading atomic persistence was incomplete")


__all__ = [
    "set_default_execution_session_record",
    "update_event_projection_records",
    "update_execution_session_record",
    "update_idempotency_record",
    "update_projection_record",
]
