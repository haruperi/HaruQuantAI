"""Create operations for Trading-owned relational records."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import generate_id, get_logger

logger = get_logger(__name__)
type _Codec = tuple[Callable[[object], str], Callable[[str], object]]


class _TransactionResult(Protocol):
    """Data transaction fields consumed by Trading persistence."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


class _ReservationValue(Protocol):
    """Reservation fields persisted without exposing its concrete class."""

    material_hash: str
    material_version: str
    reserved_at: datetime
    expires_at: datetime
    receipt_id: str | None

    @property
    def status(self) -> object:
        """Return the validated finite reservation status."""
        ...


class _EventValue(Protocol):
    """Event fields persisted without exposing its concrete class."""

    event_id: str
    aggregate_version: int
    occurred_at: datetime
    correlation_id: str
    causation_id: str | None

    @property
    def event_type(self) -> object:
        """Return the validated finite event type."""
        ...

    @property
    def event_version(self) -> object:
        """Return the validated event contract version."""
        ...


class _ProjectionValue(Protocol):
    """Projection fields persisted without exposing its concrete class."""

    version: int
    updated_at: datetime


@dataclass(frozen=True)
class _TradingPersistenceStore:
    """Opaque codec registry; Data continues to own every connection."""

    codecs: Mapping[str, _Codec]

    def encode(self, kind: str, value: object) -> str:
        """Encode one validated Trading value.

        Returns:
            Canonical JSON text.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][0](value)
        except KeyError as error:
            raise ValueError("unsupported Trading persistence record kind") from error

    def decode(self, kind: str, value: str) -> object:
        """Decode one validated Trading value.

        Returns:
            Validated Trading value.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][1](value)
        except KeyError as error:
            raise ValueError("unsupported Trading persistence record kind") from error


def _require_store(store: object) -> _TradingPersistenceStore:
    """Return a validated private Trading persistence handle.

    Raises:
        TypeError: If the opaque handle is not Trading-owned.
    """
    if not isinstance(store, _TradingPersistenceStore):
        raise TypeError("invalid Trading persistence store")
    return store


def _execute(
    statements: tuple[str, ...],
    parameter_sets: tuple[tuple[object, ...], ...],
    *,
    max_rows: int = 1,
    request_id: str | None = None,
) -> _TransactionResult:
    """Execute one bounded relational plan through Data's public boundary.

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
        raise ValueError("Trading persistence transaction failed")
    return cast("_TransactionResult", response.data)


def create_trading_runtime_store(codecs: Mapping[str, _Codec]) -> object:
    """Create an opaque Trading relational-store handle.

    Args:
        codecs: Explicit allowlisted encoders and decoders by record kind.

    Returns:
        Opaque Trading-owned persistence handle.
    """
    logger.debug("Creating Trading relational persistence handle")
    return _TradingPersistenceStore(dict(codecs))


def create_idempotency_record(
    store: object,
    key: str,
    value: _ReservationValue,
) -> None:
    """Create one immutable idempotency reservation.

    Raises:
        ValueError: If the reservation cannot be created.
    """
    _require_store(store)
    reserved_at = value.reserved_at
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    result = _execute(
        (
            "INSERT INTO trading_idempotency "
            "(idempotency_key, material_hash, material_version, status, "
            "expires_at, receipt_id, request_id, correlation_id, created_at, "
            "updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                key,
                value.material_hash,
                value.material_version,
                value.status,
                value.expires_at.isoformat(),
                value.receipt_id,
                request_id,
                correlation_id,
                reserved_at.isoformat(),
                reserved_at.isoformat(),
            ),
        ),
        request_id=request_id,
    )
    if result.affected_rows != 1:
        raise ValueError("Trading idempotency reservation was not created")


def create_event_record(
    store: object,
    *,
    key: str,
    partition: str,
    sequence: int,
    value: _EventValue,
) -> None:
    """Append one immutable Trading event directly to its owned table.

    Raises:
        ValueError: If the event cannot be appended.
    """
    persistence = _require_store(store)
    occurred_at = value.occurred_at
    result = _execute(
        (
            "INSERT INTO trading_events "
            "(event_id, event_type, event_version, scope_key, aggregate_version, "
            "occurred_at, payload_json, correlation_id, causation_id, bucket_year, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                key,
                value.event_type,
                value.event_version,
                partition,
                sequence - 1,
                occurred_at.isoformat(),
                persistence.encode("event", value),
                value.correlation_id,
                value.causation_id,
                f"{occurred_at.year:04d}",
                occurred_at.isoformat(),
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Trading event was not appended")


def create_projection_record(
    store: object,
    key: str,
    value: _ProjectionValue,
) -> None:
    """Create one initial exact-scope Trading projection.

    Raises:
        ValueError: If the projection cannot be created.
    """
    persistence = _require_store(store)
    updated_at = value.updated_at.isoformat()
    result = _execute(
        (
            "INSERT INTO trading_projections "
            "(scope_key, projection_version, last_event_seq, projection_json, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                key,
                value.version,
                value.version,
                persistence.encode("projection", value),
                updated_at,
                updated_at,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Trading projection was not created")


def create_closed_position_record(record: object) -> None:
    """Persist one complete immutable closed-position record exactly once.

    Args:
        record: Validated Trading-owned closed-position contract.

    Raises:
        TypeError: If ``record`` is not the registered contract.
        ValueError: If the insert cannot be confirmed.
    """
    from app.services.trading.contracts.models import ClosedPositionRecord

    if not isinstance(record, ClosedPositionRecord):
        raise TypeError("closed position persistence requires validated evidence")
    timestamp = record.created_at.isoformat()
    result = _execute(
        (
            "INSERT INTO trading_positions (ticket, symbol, type, volume, "
            "entry_time, entry_price, stop_loss, take_profit, exit_time, "
            "exit_price, exit_reason, commission, swap, profit, mae_points, "
            "mfe_points, slippage_points, magic, strategy, account, environment, "
            "request_id, correlation_id, evidence_hash, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                record.ticket,
                record.symbol,
                record.type,
                str(record.volume),
                record.entry_time.isoformat(),
                str(record.entry_price),
                None if record.stop_loss is None else str(record.stop_loss),
                None if record.take_profit is None else str(record.take_profit),
                record.exit_time.isoformat(),
                str(record.exit_price),
                record.exit_reason,
                str(record.commission),
                str(record.swap),
                str(record.profit),
                record.mae_points,
                record.mfe_points,
                record.slippage_points,
                record.magic,
                record.strategy,
                record.account,
                record.environment,
                record.request_id,
                record.correlation_id,
                record.evidence_hash,
                timestamp,
                timestamp,
            ),
        ),
        request_id=record.request_id,
    )
    if result.affected_rows != 1:
        raise ValueError("closed position was not persisted")


__all__ = [
    "create_closed_position_record",
    "create_event_record",
    "create_idempotency_record",
    "create_projection_record",
    "create_trading_runtime_store",
]
