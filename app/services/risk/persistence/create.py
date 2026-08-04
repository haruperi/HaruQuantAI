"""Create operations for Risk-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, cast

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import canonical_json, generate_id, get_logger

logger = get_logger(__name__)
type _Codec = tuple[Callable[[object], str], Callable[[str], object]]


class _TransactionResult(Protocol):
    """Data transaction fields consumed by Risk persistence."""

    rows: tuple[Mapping[str, object], ...]
    affected_rows: int


@dataclass(frozen=True)
class _RiskPersistenceStore:
    """Opaque Risk codec registry without a database connection."""

    codecs: Mapping[str, _Codec]

    def encode(self, kind: str, value: object) -> str:
        """Encode one allowlisted Risk value.

        Returns:
            Canonical JSON text.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][0](value)
        except KeyError as error:
            raise ValueError("unsupported Risk persistence record kind") from error

    def decode(self, kind: str, value: str) -> object:
        """Decode one allowlisted Risk value.

        Returns:
            Validated Risk value.

        Raises:
            ValueError: If the record kind is unsupported.
        """
        try:
            return self.codecs[kind][1](value)
        except KeyError as error:
            raise ValueError("unsupported Risk persistence record kind") from error


def _require_store(store: object) -> _RiskPersistenceStore:
    """Return a validated private Risk persistence handle.

    Raises:
        TypeError: If the handle is not Risk-owned.
    """
    if not isinstance(store, _RiskPersistenceStore):
        raise TypeError("invalid Risk persistence store")
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
        raise ValueError("Risk persistence transaction failed")
    return cast("_TransactionResult", response.data)


def _field(value: object, field: str) -> object:
    """Return one required validated-model field.

    Raises:
        TypeError: If the value does not expose the required field.
    """
    if not hasattr(value, field):
        message = f"Risk persistence value lacks {field}"
        raise TypeError(message)
    return getattr(value, field)


def _text_field(value: object, field: str) -> str:
    """Return one required textual model field.

    Raises:
        TypeError: If the field is not text.
    """
    item = _field(value, field)
    if not isinstance(item, str) or not item:
        message = f"Risk persistence field {field} must be text"
        raise TypeError(message)
    return item


def _time_field(value: object, field: str) -> datetime:
    """Return one required timestamp model field.

    Raises:
        TypeError: If the field is not a timestamp.
    """
    item = _field(value, field)
    if not isinstance(item, datetime):
        message = f"Risk persistence field {field} must be datetime"
        raise TypeError(message)
    return item


def _mapping_field(value: object, field: str) -> Mapping[str, object]:
    """Return one required mapping model field.

    Raises:
        TypeError: If the field is not a mapping.
    """
    item = _field(value, field)
    if not isinstance(item, Mapping):
        message = f"Risk persistence field {field} must be a mapping"
        raise TypeError(message)
    return cast("Mapping[str, object]", item)


def create_risk_runtime_store(codecs: Mapping[str, _Codec]) -> object:
    """Create an opaque Risk relational-store handle.

    Args:
        codecs: Explicit allowlisted encoders and decoders by record kind.

    Returns:
        Opaque Risk-owned persistence handle.
    """
    logger.debug("Creating Risk relational persistence handle")
    return _RiskPersistenceStore(dict(codecs))


def _approval_token(state_value: object) -> Mapping[str, object]:
    """Decode the signed token embedded in one lifecycle state.

    Returns:
        Token JSON mapping.

    Raises:
        TypeError: If lifecycle state is malformed.
    """
    if not isinstance(state_value, Mapping):
        raise TypeError("Risk approval state must be a mapping")
    approval_json = state_value.get("approval_json")
    if not isinstance(approval_json, str):
        raise TypeError("Risk approval state lacks approval_json")
    decoded = json.loads(approval_json)
    if not isinstance(decoded, dict):
        raise TypeError("Risk approval token payload must be a mapping")
    return cast("Mapping[str, object]", decoded)


def create_approval_state_record(
    store: object,
    *,
    state_key: str,
    state_value: object,
    index_key: str,
    index_sequence: int,
    index_value: object,
) -> bool:
    """Atomically create one issued approval lifecycle row.

    Returns:
        Whether the row committed.

    Raises:
        TypeError: If token lifecycle evidence is malformed.
        ValueError: If identity conflicts or Data rejects the insert.
    """
    persistence = _require_store(store)
    token = _approval_token(state_value)
    token_id = token.get("token_id")
    if token_id != state_key or index_sequence <= 0:
        raise ValueError("Risk approval persistence identity is inconsistent")
    scope = token.get("scope")
    if not isinstance(scope, Mapping):
        raise TypeError("Risk approval token scope must be a mapping")
    request_id = token.get("request_id")
    correlation_id = token.get("correlation_id")
    issued_at = token.get("issued_at")
    expires_at = token.get("expires_at")
    if not all(
        isinstance(item, str)
        for item in (request_id, correlation_id, issued_at, expires_at)
    ):
        raise TypeError("Risk approval token trace or lifetime is malformed")
    result = _execute(
        (
            "INSERT INTO risk_approval_tokens "
            "(token_id, decision_id, scope_json, state, reservation_id, "
            "expires_at, payload_json, request_id, correlation_id, created_at, "
            "updated_at) VALUES (?, ?, ?, 'issued', NULL, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                token_id,
                token.get("decision_id"),
                canonical_json(dict(scope), max_items=None),
                expires_at,
                persistence.encode("approval-state", state_value),
                request_id,
                correlation_id,
                issued_at,
                issued_at,
            ),
        ),
        request_id=cast("str", request_id),
    )
    del index_key, index_value
    return result.affected_rows == 1


def create_audit_record(
    store: object,
    *,
    record_id: str,
    sequence: int,
    value: object,
) -> None:
    """Append one immutable sealed Risk audit record.

    Raises:
        ValueError: If the record cannot be appended.
    """
    persistence = _require_store(store)
    model_sequence = _field(value, "sequence")
    if not isinstance(model_sequence, int) or sequence != model_sequence + 1:
        raise ValueError("Risk audit sequence is inconsistent")
    occurred_at = _time_field(value, "occurred_at").isoformat()
    result = _execute(
        (
            "INSERT INTO risk_audit_records "
            "(record_id, sequence, event_type, payload_json, evidence_refs_json, "
            "config_hash, decision_id, occurred_at, previous_hash, record_hash, "
            "request_id, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                record_id,
                model_sequence,
                _text_field(value, "event_type"),
                persistence.encode("audit", value),
                canonical_json(dict(_mapping_field(value, "evidence_refs"))),
                _text_field(value, "config_hash"),
                _field(value, "decision_id"),
                occurred_at,
                _text_field(value, "previous_hash"),
                _text_field(value, "record_hash"),
                _text_field(value, "request_id"),
                _text_field(value, "correlation_id"),
                occurred_at,
            ),
        ),
        request_id=_text_field(value, "request_id"),
    )
    if result.affected_rows != 1:
        raise ValueError("Risk audit record was not appended")


def create_decision_record(
    store: object,
    *,
    decision_id: str,
    value: object,
) -> None:
    """Create one immutable canonical Risk decision snapshot.

    Raises:
        ValueError: If the identity conflicts with different material.
    """
    persistence = _require_store(store)
    issued_at = _time_field(value, "issued_at").isoformat()
    payload = persistence.encode("decision", value)
    result = _execute(
        (
            "INSERT INTO risk_decision_snapshots "
            "(record_id, record_type, config_hash, payload_json, occurred_at, "
            "request_id, correlation_id, created_at) "
            "VALUES (?, 'decision', ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(record_id) DO UPDATE SET record_id=excluded.record_id "
            "WHERE risk_decision_snapshots.payload_json=excluded.payload_json",
        ),
        (
            (
                decision_id,
                _text_field(value, "config_hash"),
                payload,
                issued_at,
                _text_field(value, "request_id"),
                _text_field(value, "correlation_id"),
                issued_at,
            ),
        ),
        request_id=_text_field(value, "request_id"),
    )
    if result.affected_rows != 1:
        raise ValueError("Risk decision identity conflict")


def create_eligibility_record(store: object, key: str, value: object) -> None:
    """Create one exact immutable eligibility decision.

    Raises:
        ValueError: If the identity conflicts with different material.
    """
    persistence = _require_store(store)
    issued_at = _time_field(value, "issued_at").isoformat()
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    payload = persistence.encode("eligibility", value)
    result = _execute(
        (
            "INSERT INTO risk_eligibility_decisions "
            "(decision_id, strategy_id, strategy_version, payload_json, "
            "expires_at, request_id, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(decision_id) DO UPDATE SET decision_id=excluded.decision_id "
            "WHERE risk_eligibility_decisions.payload_json=excluded.payload_json",
        ),
        (
            (
                key,
                _text_field(value, "strategy_id"),
                _text_field(value, "strategy_version"),
                payload,
                _time_field(value, "expires_at").isoformat(),
                request_id,
                correlation_id,
                issued_at,
            ),
        ),
        request_id=request_id,
    )
    if result.affected_rows != 1:
        raise ValueError("Risk eligibility identity conflict")


def create_allocation_review_record(store: object, key: str, value: object) -> None:
    """Create one immutable inactive allocation review.

    Raises:
        ValueError: If the identity conflicts with different material.
    """
    persistence = _require_store(store)
    issued_at = _time_field(value, "issued_at").isoformat()
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    payload = persistence.encode("allocation", value)
    result = _execute(
        (
            "INSERT INTO risk_allocation_decisions "
            "(decision_id, portfolio_id, reviewed_version, active, "
            "predecessor_version, payload_json, request_id, correlation_id, "
            "created_at) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?) "
            "ON CONFLICT(decision_id) DO UPDATE SET decision_id=excluded.decision_id "
            "WHERE risk_allocation_decisions.payload_json=excluded.payload_json",
        ),
        (
            (
                key,
                _text_field(value, "portfolio_id"),
                _text_field(value, "reviewed_version"),
                _field(value, "predecessor_version"),
                payload,
                request_id,
                correlation_id,
                issued_at,
            ),
        ),
        request_id=request_id,
    )
    if result.affected_rows != 1:
        raise ValueError("Risk allocation identity conflict")


def create_active_allocation_record(store: object, key: str, value: object) -> None:
    """Activate one existing allocation review when no active row exists.

    Raises:
        ValueError: If the review is missing or another row is active.
    """
    _require_store(store)
    result = _execute(
        (
            "UPDATE risk_allocation_decisions SET active=1 "
            "WHERE portfolio_id=? AND decision_id=? AND active=0 "
            "AND NOT EXISTS (SELECT 1 FROM risk_allocation_decisions "
            "WHERE portfolio_id=? AND active=1)",
        ),
        (
            (
                key,
                _text_field(value, "decision_id"),
                key,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Risk active allocation could not be created")


__all__ = [
    "create_active_allocation_record",
    "create_allocation_review_record",
    "create_approval_state_record",
    "create_audit_record",
    "create_decision_record",
    "create_eligibility_record",
    "create_risk_runtime_store",
]
