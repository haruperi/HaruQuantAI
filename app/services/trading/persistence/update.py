"""Atomic update operations for Trading-owned relational records."""

from __future__ import annotations

from app.services.trading.persistence.create import (
    _EventValue,
    _execute,
    _ProjectionValue,
    _require_store,
    _ReservationValue,
)
from app.services.trading.state.materializations import build_materialization_batch
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


def update_idempotency_record(
    store: object,
    *,
    key: str,
    value: _ReservationValue,
    expected_revision: object,
) -> None:
    """Compare and swap one idempotency reservation by finite state.

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

    Raises:
        TypeError: If state values are not validated Trading contracts.
        ValueError: If mapping or transactional persistence fails.
    """
    from app.services.trading.state.events import TradingEvent
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

    result = _execute(tuple(statements), tuple(parameters))
    if result.affected_rows < _MIN_ATOMIC_AFFECTED_ROWS:
        raise ValueError("Trading atomic persistence was incomplete")


__all__ = [
    "update_event_projection_records",
    "update_idempotency_record",
    "update_projection_record",
]
