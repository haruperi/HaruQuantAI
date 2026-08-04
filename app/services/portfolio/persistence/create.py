"""Create operations for Portfolio-owned relational records."""

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
_COMPOUND_WRITE_ROWS = 2


class _TransactionResult(Protocol):
    """Data transaction fields consumed by Portfolio persistence."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


@dataclass(frozen=True)
class _PortfolioPersistenceStore:
    """Opaque Portfolio codec registry without a database connection."""

    codecs: Mapping[str, _Codec]

    def encode(self, kind: str, value: object) -> str:
        """Encode one allowlisted value.

        Returns:
            Canonical JSON text.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][0](value)
        except KeyError as error:
            raise ValueError("unsupported Portfolio persistence record kind") from error

    def decode(self, kind: str, value: str) -> object:
        """Decode one allowlisted value.

        Returns:
            Validated Portfolio value.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][1](value)
        except KeyError as error:
            raise ValueError("unsupported Portfolio persistence record kind") from error


def _require_store(store: object) -> _PortfolioPersistenceStore:
    """Return a validated private Portfolio persistence handle.

    Raises:
        TypeError: If the handle is not Portfolio-owned.
    """
    if not isinstance(store, _PortfolioPersistenceStore):
        raise TypeError("invalid Portfolio persistence store")
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
        raise ValueError("Portfolio persistence transaction failed")
    return cast("_TransactionResult", response.data)


def _field(value: object, field: str) -> object:
    """Return one required model field.

    Raises:
        TypeError: If the value does not expose the field.
    """
    if not hasattr(value, field):
        message = f"Portfolio persistence value lacks {field}"
        raise TypeError(message)
    return getattr(value, field)


def _text_field(value: object, field: str) -> str:
    """Return one required nonempty textual field.

    Raises:
        TypeError: If the field is not text.
    """
    item = _field(value, field)
    if not isinstance(item, str) or not item:
        message = f"Portfolio persistence field {field} must be text"
        raise TypeError(message)
    return item


def _time_field(value: object, field: str) -> datetime:
    """Return one required timestamp field.

    Raises:
        TypeError: If the field is not a timestamp.
    """
    item = _field(value, field)
    if not isinstance(item, datetime):
        message = f"Portfolio persistence field {field} must be datetime"
        raise TypeError(message)
    return item


def _mapping_field(value: object, field: str) -> Mapping[str, object]:
    """Return one required mapping field.

    Raises:
        TypeError: If the field is not a mapping.
    """
    item = _field(value, field)
    if not isinstance(item, Mapping):
        message = f"Portfolio persistence field {field} must be a mapping"
        raise TypeError(message)
    return cast("Mapping[str, object]", item)


def _outbox_event_type(value: object) -> str:
    """Extract a verified event type from the redacted audit envelope.

    Returns:
        Existing event-type evidence.

    Raises:
        TypeError: If no event type is present.
    """
    if not isinstance(value, Mapping):
        raise TypeError("Portfolio outbox value must be a mapping")
    audit = value.get("audit", value)
    if not isinstance(audit, Mapping):
        raise TypeError("Portfolio outbox audit value must be a mapping")
    for key in ("action", "event_type", "event"):
        item = audit.get(key)
        if isinstance(item, str) and item:
            return item
    raise TypeError("Portfolio outbox event type is missing")


def create_portfolio_runtime_store(codecs: Mapping[str, _Codec]) -> object:
    """Create an opaque Portfolio relational-store handle.

    Args:
        codecs: Explicit allowlisted encoders and decoders by record kind.

    Returns:
        Opaque Portfolio-owned persistence handle.
    """
    logger.debug("Creating Portfolio relational persistence handle")
    return _PortfolioPersistenceStore(dict(codecs))


def _outbox_parameters(
    persistence: _PortfolioPersistenceStore,
    *,
    event_key: str,
    aggregate_id: str,
    event_value: object,
    occurred_at: str,
    request_id: str,
    correlation_id: str,
) -> tuple[object, ...]:
    """Build one normalized outbox parameter set.

    Returns:
        Ordered outbox values.
    """
    return (
        event_key,
        _outbox_event_type(event_value),
        aggregate_id,
        request_id,
        correlation_id,
        persistence.encode("outbox", event_value),
        occurred_at,
        occurred_at,
    )


_OUTBOX_INSERT = (
    "INSERT INTO portfolio_audit_outbox "
    "(event_id, event_type, aggregate_id, request_id, correlation_id, "
    "payload_json, occurred_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
    "ON CONFLICT(event_id) DO UPDATE SET event_id=excluded.event_id, "
    "payload_json=CASE WHEN portfolio_audit_outbox.payload_json=excluded.payload_json "
    "THEN excluded.payload_json ELSE NULL END"
)


def create_construction_record(
    store: object,
    *,
    state_key: str,
    state_value: object,
    event_key: str,
    event_sequence: int,
    event_value: object,
) -> bool:
    """Atomically create immutable construction and outbox records.

    Returns:
        Whether both records committed atomically.

    Raises:
        ValueError: If identity or material conflicts.
    """
    persistence = _require_store(store)
    canonical_hash = _text_field(state_value, "canonical_hash")
    if state_key != canonical_hash or event_sequence <= 0:
        raise ValueError("Portfolio construction persistence identity conflicts")
    created_at = _time_field(state_value, "created_at").isoformat()
    request_id = _text_field(state_value, "request_id")
    correlation_id = _text_field(state_value, "correlation_id")
    result = _execute(
        (
            "INSERT INTO portfolio_construction_results "
            "(result_id, portfolio_id, portfolio_version, canonical_hash, "
            "result_json, request_id, correlation_id, created_at) "
            "VALUES (CASE WHEN EXISTS (SELECT 1 FROM "
            "portfolio_construction_results WHERE canonical_hash=? AND "
            "result_id<>?) THEN NULL ELSE ? END, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(result_id) DO UPDATE SET result_id=excluded.result_id, "
            "result_json=CASE WHEN portfolio_construction_results.result_json="
            "excluded.result_json THEN excluded.result_json ELSE NULL END",
            _OUTBOX_INSERT,
        ),
        (
            (
                canonical_hash,
                _text_field(state_value, "result_id"),
                _text_field(state_value, "result_id"),
                _text_field(state_value, "portfolio_id"),
                _text_field(state_value, "portfolio_version"),
                canonical_hash,
                persistence.encode("construction", state_value),
                request_id,
                correlation_id,
                created_at,
            ),
            _outbox_parameters(
                persistence,
                event_key=event_key,
                aggregate_id=_text_field(state_value, "portfolio_id"),
                event_value=event_value,
                occurred_at=created_at,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _COMPOUND_WRITE_ROWS


def create_plan_record(
    store: object,
    *,
    state_value: object,
    event_key: str,
    event_sequence: int,
    event_value: object,
) -> bool:
    """Atomically create immutable plan and outbox records.

    Returns:
        Whether both records committed atomically.

    Raises:
        ValueError: If identity or material conflicts.
    """
    persistence = _require_store(store)
    if event_sequence <= 0:
        raise ValueError("Portfolio plan sequence must be positive")
    created_at = _time_field(state_value, "created_at").isoformat()
    request_id = _text_field(state_value, "request_id")
    correlation_id = _text_field(state_value, "correlation_id")
    result = _execute(
        (
            "INSERT INTO portfolio_rebalance_plans "
            "(plan_id, plan_version, portfolio_id, allocation_version, "
            "canonical_hash, plan_json, created_at, request_id, correlation_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(plan_id, plan_version) DO UPDATE SET "
            "plan_json=CASE WHEN portfolio_rebalance_plans.plan_json="
            "excluded.plan_json THEN excluded.plan_json ELSE NULL END",
            _OUTBOX_INSERT,
        ),
        (
            (
                _text_field(state_value, "plan_id"),
                _text_field(state_value, "plan_version"),
                _text_field(state_value, "portfolio_id"),
                _text_field(state_value, "allocation_version"),
                _text_field(state_value, "canonical_hash"),
                persistence.encode("plan", state_value),
                created_at,
                request_id,
                correlation_id,
            ),
            _outbox_parameters(
                persistence,
                event_key=event_key,
                aggregate_id=_text_field(state_value, "portfolio_id"),
                event_value=event_value,
                occurred_at=created_at,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _COMPOUND_WRITE_ROWS


__all__ = [
    "create_construction_record",
    "create_plan_record",
    "create_portfolio_runtime_store",
]
