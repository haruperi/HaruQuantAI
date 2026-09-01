"""Create operations for Trading-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from app.composition.logging import get_logger
from app.kernel.identity import generate_id
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)
type _Codec = tuple[Callable[[object], str], Callable[[str], object]]
_PROTECTIVE_LEG_COUNT = 2


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
        """Return the validated finite reservation status.

        Returns:
            Reservation status object.
        """
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
        """Return the validated finite event type.

        Returns:
            Event type object.
        """
        ...

    @property
    def event_version(self) -> object:
        """Return the validated event contract version.

        Returns:
            Event version object.
        """
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

        Args:
            kind: Registered record kind string.
            value: Object to encode.

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

        Args:
            kind: Registered record kind string.
            value: Canonical JSON text to decode.

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


def create_execution_session_record(
    value: Mapping[str, object], request_id: str
) -> None:
    """Create one session projection and its initial immutable event.

    Raises:
        ValueError: If session creation fails to insert both records.
    """
    metadata = json.dumps(value.get("metadata", {}), separators=(",", ":"))
    created_at = str(value["created_at"])
    result = _execute(
        (
            "INSERT INTO trading_sessions (session_id, principal_id, environment_id, "
            "name, description, mode, provider, provider_account_ref, credential_ref, "
            "simulation_session_id, dataset_ref, dataset_revision, dataset_hash, "
            "sim_initial_balance_decimal, sim_leverage, sim_account_currency, "
            "lifecycle_state, recovery_state, is_default, is_active, auto_start, "
            "metadata_json, version, created_at, updated_at) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            "INSERT INTO trading_session_events (event_id, session_id, sequence, "
            "event_type, payload_json, occurred_at, request_id) VALUES (?,?,?,?,?,?,?)",
        ),
        (
            (
                value["session_id"],
                value["principal_id"],
                value["environment_id"],
                value["name"],
                value.get("description", ""),
                value["mode"],
                value["provider"],
                value.get("provider_account_ref"),
                value.get("credential_ref"),
                value.get("simulation_session_id"),
                value.get("dataset_ref"),
                value.get("dataset_revision"),
                value.get("dataset_hash"),
                value.get("sim_initial_balance"),
                value.get("sim_leverage"),
                value.get("sim_account_currency"),
                value["lifecycle_state"],
                value["recovery_state"],
                int(bool(value.get("is_default"))),
                int(bool(value.get("is_active"))),
                int(bool(value.get("auto_start", True))),
                metadata,
                value.get("version", 0),
                created_at,
                str(value["updated_at"]),
            ),
            (
                generate_id("evt"),
                value["session_id"],
                0,
                "created",
                "{}",
                created_at,
                request_id,
            ),
        ),
        request_id=request_id,
    )
    if result.affected_rows != 2:  # noqa: PLR2004
        raise ValueError("Trading execution session creation was incomplete")


def create_idempotency_record(
    store: object,
    key: str,
    value: _ReservationValue,
) -> None:
    """Create one immutable idempotency reservation.

    Args:
        store: Persistence handle object.
        key: Idempotency reservation key string.
        value: Reservation value object.

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

    Args:
        store: Persistence handle object.
        key: Event key string.
        partition: Partition scope string.
        sequence: Event sequence integer.
        value: Event value object.

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

    Args:
        store: Persistence handle object.
        key: Scope key string.
        value: Projection value object.

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


def create_protective_order_records(
    plan: object, *, correlation_id: str, occurred_at: datetime
) -> None:
    """Persist the stop and target legs of one validated protection plan atomically.

    Args:
        plan: Validated protective order plan object.
        correlation_id: Correlation trace identifier string.
        occurred_at: Aware UTC timestamp when plan occurred.

    Raises:
        TypeError: If the value is not a Trading protective-order plan.
        ValueError: If both append-only legs cannot be confirmed.
    """
    from app.services.trading.protective_orders.contracts import _ProtectiveOrderPlan

    if not isinstance(plan, _ProtectiveOrderPlan):
        raise TypeError("protective-order persistence requires a validated plan")
    timestamp = occurred_at.isoformat()
    statement = (
        "INSERT INTO trading_protective_orders "
        "(protective_order_id, position_id, order_id, protection_type, "
        "quantity_decimal, price_decimal, state, oco_group_id, source_sequence, "
        "correlation_id, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    common = (
        plan.position_id,
        plan.order_id,
        str(plan.quantity),
        "pending",
        plan.oco_group_id,
        plan.source_sequence,
        correlation_id,
        timestamp,
        timestamp,
    )
    result = _execute(
        (statement, statement),
        (
            (
                f"{plan.plan_id}:stop",
                common[0],
                common[1],
                "stop",
                common[2],
                str(plan.stop_price),
                *common[3:],
            ),
            (
                f"{plan.plan_id}:target",
                common[0],
                common[1],
                "target",
                common[2],
                str(plan.target_price),
                *common[3:],
            ),
        ),
        max_rows=2,
    )
    if result.affected_rows != _PROTECTIVE_LEG_COUNT:
        raise ValueError("protective-order plan was not persisted atomically")


def create_trade_ownership_record(
    ownership: object, *, correlation_id: str, occurred_at: datetime
) -> None:
    """Append one validated ownership fact.

    Args:
        ownership: Validated ownership contract object.
        correlation_id: Correlation trace identifier string.
        occurred_at: Aware UTC timestamp when ownership fact occurred.

    Raises:
        TypeError: If the value is not a Trading ownership contract.
        ValueError: If the append cannot be confirmed.
    """
    from app.services.trading.trade_ownership.contracts import _TradeOwnership

    if not isinstance(ownership, _TradeOwnership):
        raise TypeError("ownership persistence requires validated evidence")
    result = _execute(
        (
            "INSERT INTO trading_trade_ownership "
            "(ownership_id, position_id, owner_type, owner_id, trade_plan_id, "
            "session_id, source_sequence, released, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                ownership.ownership_id,
                ownership.position_id,
                ownership.owner_type,
                ownership.owner_id,
                ownership.trade_plan_id,
                ownership.session_id,
                ownership.source_sequence,
                int(ownership.released),
                correlation_id,
                occurred_at.isoformat(),
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("trade ownership was not persisted")


__all__ = [
    "create_closed_position_record",
    "create_event_record",
    "create_execution_session_record",
    "create_idempotency_record",
    "create_projection_record",
    "create_protective_order_records",
    "create_trade_ownership_record",
    "create_trading_runtime_store",
]
