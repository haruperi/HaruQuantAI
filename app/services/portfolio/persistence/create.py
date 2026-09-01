"""Create operations for Portfolio-owned relational records."""

from __future__ import annotations

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

        Args:
            kind: Registered record kind string.
            value: Value object to encode.

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

        Args:
            kind: Registered record kind string.
            value: Canonical JSON text to decode.

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

    Args:
        store: Persistence handle object.

    Returns:
        Validated Portfolio persistence store.

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

    Args:
        statements: Tuple of SQL statement strings.
        parameter_sets: Tuple of SQL parameter tuples.
        max_rows: Bounded expected row limit.
        request_id: Optional request trace identifier.

    Returns:
        Confirmed normalized transaction result.

    Raises:
        ValueError: If Data cannot confirm the transaction.
    """
    operation_id = request_id or generate_id("req")
    logger.info("Executing Portfolio relational transaction")
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
        logger.error("Portfolio relational transaction failed closed")
        raise ValueError("Portfolio persistence transaction failed")
    logger.info("Portfolio relational transaction committed")
    return cast("_TransactionResult", response.data)


def _field(value: object, field: str) -> object:
    """Return one required model field.

    Args:
        value: Object exposing the attribute.
        field: Name of required attribute.

    Returns:
        Value of requested attribute.

    Raises:
        TypeError: If the value does not expose the field.
    """
    if not hasattr(value, field):
        message = f"Portfolio persistence value lacks {field}"
        raise TypeError(message)
    return getattr(value, field)


def _text_field(value: object, field: str) -> str:
    """Return one required nonempty textual field.

    Args:
        value: Object exposing the attribute.
        field: Name of required attribute.

    Returns:
        Nonempty text string.

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

    Args:
        value: Object exposing the attribute.
        field: Name of required attribute.

    Returns:
        Datetime object.

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

    Args:
        value: Object exposing the attribute.
        field: Name of required attribute.

    Returns:
        Mapping dictionary object.

    Raises:
        TypeError: If the field is not a mapping.
    """
    item = _field(value, field)
    if not isinstance(item, Mapping):
        message = f"Portfolio persistence field {field} must be a mapping"
        raise TypeError(message)
    return cast("Mapping[str, object]", item)


def _mapping_text(value: Mapping[str, object], field: str) -> str:
    """Return one required non-empty textual field from a mapping.

    Args:
        value: Source mapping.
        field: Required text field name.

    Returns:
        Validated text.

    Raises:
        TypeError: If the field is missing or not non-empty text.
    """
    item = value.get(field)
    if not isinstance(item, str) or not item:
        message = f"Portfolio persistence mapping field {field} must be text"
        raise TypeError(message)
    return item


def _mapping_time(value: Mapping[str, object], field: str) -> datetime:
    """Return one required timestamp field from a mapping.

    Args:
        value: Source mapping.
        field: Required timestamp field name.

    Returns:
        Validated timestamp.

    Raises:
        TypeError: If the field is missing or not an ISO-format timestamp.
    """
    item = value.get(field)
    if isinstance(item, datetime):
        return item
    if isinstance(item, str):
        try:
            return datetime.fromisoformat(item)
        except ValueError as error:
            message = f"Portfolio persistence field {field} must be ISO datetime"
            raise TypeError(message) from error
    message = f"Portfolio persistence field {field} must be a timestamp"
    raise TypeError(message)


def _outbox_event_type(value: object) -> str:
    """Extract a verified event type from the redacted audit envelope.

    Args:
        value: Redacted audit envelope mapping object.

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

    Args:
        persistence: Portfolio persistence store instance.
        event_key: Stable outbox event identity string.
        aggregate_id: Aggregate root ID string.
        event_value: Redacted audit event object.
        occurred_at: ISO timestamp string.
        request_id: Request trace ID string.
        correlation_id: Correlation trace ID string.

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


def create_definition_record(
    store: object,
    *,
    state_value: object,
    event_key: str,
    event_value: object,
) -> bool:
    """Atomically create an immutable definition and outbox record.

    Args:
        store: Portfolio persistence handle.
        state_value: Validated immutable definition.
        event_key: Stable outbox event identity.
        event_value: Redacted audit envelope.

    Returns:
        Whether both records committed atomically.

    Raises:
        ValueError: If Data cannot confirm both writes.
    """
    logger.info("Persisting immutable Portfolio definition and audit event")
    persistence = _require_store(store)
    created_at = _time_field(state_value, "created_at").isoformat()
    request_id = _text_field(state_value, "request_id")
    correlation_id = _text_field(state_value, "correlation_id")
    portfolio_id = _text_field(state_value, "portfolio_id")
    result = _execute(
        (
            "INSERT INTO portfolio_definitions "
            "(portfolio_id, portfolio_version, scope_key, definition_json, "
            "canonical_hash, request_id, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(portfolio_id, portfolio_version) DO UPDATE SET "
            "definition_json=CASE WHEN portfolio_definitions.definition_json="
            "excluded.definition_json AND portfolio_definitions.canonical_hash="
            "excluded.canonical_hash THEN excluded.definition_json ELSE NULL END",
            _OUTBOX_INSERT,
        ),
        (
            (
                portfolio_id,
                _text_field(state_value, "portfolio_version"),
                persistence.encode("scope", _mapping_field(state_value, "scope")),
                persistence.encode("definition", state_value),
                _text_field(state_value, "canonical_hash"),
                request_id,
                correlation_id,
                created_at,
            ),
            _outbox_parameters(
                persistence,
                event_key=event_key,
                aggregate_id=portfolio_id,
                event_value=event_value,
                occurred_at=created_at,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _COMPOUND_WRITE_ROWS


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

    Args:
        store: Portfolio persistence handle.
        state_key: Canonical hash string matching result.
        state_value: Construction result model object.
        event_key: Stable outbox event identity.
        event_sequence: Positive sequence number.
        event_value: Redacted audit event object.

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

    Args:
        store: Portfolio persistence handle.
        state_value: Rebalance plan model object.
        event_key: Stable outbox event identity.
        event_sequence: Positive sequence number.
        event_value: Redacted audit event object.

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


def create_ledger_account_record(
    store: object,
    *,
    state_value: object,
    event_key: str,
    event_value: object,
) -> bool:
    """Atomically create an immutable ledger account and outbox record.

    Args:
        store: Portfolio persistence handle.
        state_value: Validated ``LedgerAccount`` mapping.
        event_key: Stable outbox event identity.
        event_value: Redacted audit envelope.

    Returns:
        Whether both records committed atomically.

    Raises:
        TypeError: If the value is not a mapping.
        ValueError: If Data cannot confirm both writes.
    """
    logger.info("Persisting immutable Portfolio ledger account")
    persistence = _require_store(store)
    if not isinstance(state_value, Mapping):
        raise TypeError("Portfolio ledger account value must be a mapping")
    created_at = _mapping_time(state_value, "registered_at").isoformat()
    request_id = _mapping_text(state_value, "request_id")
    correlation_id = _mapping_text(state_value, "correlation_id")
    account_id = _mapping_text(state_value, "account_id")
    portfolio_id = _mapping_text(state_value, "portfolio_id")
    result = _execute(
        (
            "INSERT INTO portfolio_ledger_accounts "
            "(account_id, portfolio_id, currency, normal_balance, category, "
            "account_json, registered_at, request_id, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(account_id) DO UPDATE SET "
            "account_json=CASE WHEN portfolio_ledger_accounts.account_json="
            "excluded.account_json THEN excluded.account_json ELSE NULL END",
            _OUTBOX_INSERT,
        ),
        (
            (
                account_id,
                portfolio_id,
                _mapping_text(state_value, "currency"),
                _mapping_text(state_value, "normal_balance"),
                _mapping_text(state_value, "category"),
                persistence.encode("ledger_account", state_value),
                created_at,
                request_id,
                correlation_id,
                created_at,
            ),
            _outbox_parameters(
                persistence,
                event_key=event_key,
                aggregate_id=portfolio_id,
                event_value=event_value,
                occurred_at=created_at,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _COMPOUND_WRITE_ROWS


def create_ledger_batch_record(
    store: object,
    *,
    batch_value: object,
    entry_rows: tuple[tuple[object, ...], ...],
    event_key: str,
    event_value: object,
) -> bool:
    """Atomically append one balanced batch, its legs, and an outbox record.

    The batch and its entries are append-only (financial records are never
    edited; corrections are reversal batches). A replayed
    ``(source_event_id, source_sequence)`` with identical material is idempotent.

    Args:
        store: Portfolio persistence handle.
        batch_value: Validated ``PostingBatch`` mapping.
        entry_rows: Normalized per-leg parameter tuples.
        event_key: Stable outbox event identity.
        event_value: Redacted audit envelope.

    Returns:
        Whether the batch, all legs, and the outbox row committed atomically.

    Raises:
        TypeError: If the batch value is not a mapping.
        ValueError: If Data cannot confirm the transaction.
    """
    logger.info("Persisting immutable Portfolio ledger batch and entries")
    persistence = _require_store(store)
    if not isinstance(batch_value, Mapping):
        raise TypeError("Portfolio ledger batch value must be a mapping")
    posted_at = _mapping_time(batch_value, "posted_at").isoformat()
    request_id = _mapping_text(batch_value, "request_id")
    correlation_id = _mapping_text(batch_value, "correlation_id")
    batch_id = _mapping_text(batch_value, "batch_id")
    batch_json = persistence.encode("ledger_batch", batch_value)
    batch_insert = (
        "INSERT INTO portfolio_ledger_posting_batches "
        "(batch_id, source_event_id, source_sequence, entry_sequence, "
        "reversal_of, posted_at, canonical_hash, batch_json, request_id, "
        "correlation_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(batch_id) DO UPDATE SET "
        "batch_json=CASE WHEN portfolio_ledger_posting_batches.batch_json="
        "excluded.batch_json THEN excluded.batch_json ELSE NULL END"
    )
    statements: tuple[str, ...] = (batch_insert,)
    parameters: list[tuple[object, ...]] = [
        (
            batch_id,
            _mapping_text(batch_value, "source_event_id"),
            batch_value.get("source_sequence", 0),
            batch_value.get("entry_sequence", 0),
            batch_value.get("reversal_of"),
            posted_at,
            _mapping_text(batch_value, "canonical_hash"),
            batch_json,
            request_id,
            correlation_id,
            posted_at,
        )
    ]
    statements = (*statements, *(_LEDGER_ENTRY_INSERT for _ in entry_rows))
    parameters.extend(entry_rows)
    statements = (*statements, _OUTBOX_INSERT)
    parameters.append(
        _outbox_parameters(
            persistence,
            event_key=event_key,
            aggregate_id=batch_id,
            event_value=event_value,
            occurred_at=posted_at,
            request_id=request_id,
            correlation_id=correlation_id,
        )
    )
    result = _execute(
        tuple(statements),
        tuple(parameters),
        max_rows=max(len(parameters), 1),
        request_id=request_id,
    )
    return result.affected_rows >= len(parameters)


_LEDGER_ENTRY_INSERT = (
    "INSERT INTO portfolio_ledger_entries "
    "(entry_id, batch_id, entry_sequence, account_id, side, amount_decimal, "
    "currency, posting_type, posted_at, request_id, correlation_id, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
    "ON CONFLICT(entry_id, batch_id) DO UPDATE SET "
    "amount_decimal=CASE WHEN portfolio_ledger_entries.amount_decimal="
    "excluded.amount_decimal THEN excluded.amount_decimal ELSE NULL END"
)


__all__ = [
    "create_construction_record",
    "create_definition_record",
    "create_ledger_account_record",
    "create_ledger_batch_record",
    "create_plan_record",
    "create_portfolio_runtime_store",
]
