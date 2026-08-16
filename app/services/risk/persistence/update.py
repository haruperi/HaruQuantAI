"""Atomic update operations for Risk-owned relational records."""

from __future__ import annotations

import json
from collections.abc import Mapping

from app.services.risk.persistence.create import (
    _execute,
    _field,
    _mapping_field,
    _require_store,
    _text_field,
    _time_field,
)
from app.utils import canonical_json, generate_id, get_logger

logger = get_logger(__name__)
_COMPOUND_WRITE_ROWS = 2
_ALLOCATION_WRITE_ROWS = 4


def _approval_update(value: object) -> tuple[str, str | None, str]:
    """Return normalized lifecycle state, reservation, and update time.

    Returns:
        State, optional reservation identity, and ISO update time.

    Raises:
        TypeError: If lifecycle evidence is malformed.
    """
    if not isinstance(value, Mapping):
        raise TypeError("Risk approval state must be a mapping")
    approval_json = value.get("approval_json")
    if not isinstance(approval_json, str):
        raise TypeError("Risk approval state lacks approval_json")
    token = json.loads(approval_json)
    if not isinstance(token, dict) or not isinstance(token.get("issued_at"), str):
        raise TypeError("Risk approval token lifetime is malformed")
    reservation = value.get("reservation_id")
    if reservation is not None and not isinstance(reservation, str):
        raise TypeError("Risk approval reservation identity is malformed")
    revoked_at = value.get("revoked_at")
    consumed_at = value.get("consumed_at")
    if revoked_at is not None:
        if not isinstance(revoked_at, str):
            raise TypeError("Risk approval revocation time is malformed")
        return "revoked", reservation, revoked_at
    if value.get("consumed") is True:
        if not isinstance(consumed_at, str):
            raise TypeError("Risk approval consumption time is malformed")
        return "consumed", reservation, consumed_at
    return "issued", reservation, str(token["issued_at"])


def update_approval_state_record(
    store: object,
    *,
    key: str,
    value: object,
    expected_revision: object,
) -> None:
    """Compare and swap one approval lifecycle row.

    Raises:
        ValueError: If the stored update token no longer matches.
    """
    persistence = _require_store(store)
    state, reservation, updated_at = _approval_update(value)
    result = _execute(
        (
            "UPDATE risk_approval_tokens SET state=?, reservation_id=?, "
            "payload_json=?, updated_at=? WHERE token_id=? AND updated_at=?",
        ),
        (
            (
                state,
                reservation,
                persistence.encode("approval-state", value),
                updated_at,
                key,
                expected_revision,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Risk approval state revision conflict")


def update_active_allocation_record(
    store: object,
    *,
    key: str,
    value: object,
    expected_revision: object,
) -> None:
    """Atomically replace one portfolio's active allocation decision.

    Raises:
        ValueError: If the predecessor or target review is absent.
    """
    persistence = _require_store(store)
    target_id = _text_field(value, "decision_id")
    request_id = generate_id("req")
    correlation_id = generate_id("cor")
    issued_at = _time_field(value, "issued_at").isoformat()
    # The first statement maps a missing expected active row to invalid ``-1``;
    # the existing CHECK constraint then rolls back the whole transition.
    result = _execute(
        (
            "INSERT INTO risk_allocation_decisions "
            "(decision_id, portfolio_id, reviewed_version, active, "
            "predecessor_version, payload_json, request_id, correlation_id, "
            "created_at) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?) "
            "ON CONFLICT(decision_id) DO UPDATE SET decision_id=excluded.decision_id "
            "WHERE risk_allocation_decisions.payload_json=excluded.payload_json",
            "UPDATE risk_allocation_decisions SET active=CASE WHEN EXISTS ("
            "SELECT 1 FROM risk_allocation_decisions current "
            "WHERE current.portfolio_id=? AND current.decision_id=? "
            "AND current.active=1) THEN active ELSE -1 END "
            "WHERE portfolio_id=? AND decision_id=?",
            "UPDATE risk_allocation_decisions SET active=0 "
            "WHERE portfolio_id=? AND decision_id=? AND active=1",
            "UPDATE risk_allocation_decisions SET active=1 "
            "WHERE portfolio_id=? AND decision_id=? AND active=0",
        ),
        (
            (
                target_id,
                key,
                _text_field(value, "reviewed_version"),
                _field(value, "predecessor_version"),
                persistence.encode("allocation", value),
                request_id,
                correlation_id,
                issued_at,
            ),
            (key, expected_revision, key, target_id),
            (key, expected_revision),
            (key, target_id),
        ),
        request_id=request_id,
    )
    if result.affected_rows < _ALLOCATION_WRITE_ROWS:
        raise ValueError("Risk active allocation revision conflict")


def update_kill_switch_with_audit(
    store: object,
    *,
    state_key: str,
    state_value: object,
    expected_revision: int,
    audit_key: str,
    audit_sequence: int,
    audit_value: object,
) -> bool:
    """Atomically compare and swap kill-switch state and append its audit.

    Returns:
        Whether both records committed.

    Raises:
        TypeError: If state or audit evidence is malformed.
        ValueError: If state or audit evidence conflicts.
    """
    persistence = _require_store(store)
    updated_at = _time_field(state_value, "updated_at").isoformat()
    state_version = _field(state_value, "version")
    audit_model_sequence = _field(audit_value, "sequence")
    if not isinstance(state_version, int) or not isinstance(audit_model_sequence, int):
        raise TypeError("Risk state or audit sequence is malformed")
    if audit_sequence != audit_model_sequence + 1:
        raise ValueError("Risk audit sequence is inconsistent")
    occurred_at = _time_field(audit_value, "occurred_at").isoformat()
    request_id = _text_field(audit_value, "request_id")
    result = _execute(
        (
            "INSERT INTO risk_kill_switch_states "
            "(state_id, scope_level, scope_json, state, version, payload_json, "
            "request_id, correlation_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(state_id) DO UPDATE SET "
            "scope_level=excluded.scope_level, scope_json=excluded.scope_json, "
            "state=CASE WHEN risk_kill_switch_states.version=? "
            "THEN excluded.state ELSE NULL END, version=excluded.version, "
            "payload_json=excluded.payload_json, request_id=excluded.request_id, "
            "correlation_id=excluded.correlation_id, updated_at=excluded.updated_at",
            "INSERT INTO risk_audit_records "
            "(record_id, sequence, event_type, payload_json, evidence_refs_json, "
            "config_hash, decision_id, occurred_at, previous_hash, record_hash, "
            "request_id, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ),
        (
            (
                state_key,
                _text_field(state_value, "scope_level"),
                canonical_json(dict(_mapping_field(state_value, "scope"))),
                _text_field(state_value, "state"),
                state_version,
                persistence.encode("kill-switch", state_value),
                request_id,
                _text_field(audit_value, "correlation_id"),
                updated_at,
                updated_at,
                expected_revision,
            ),
            (
                audit_key,
                audit_model_sequence,
                _text_field(audit_value, "event_type"),
                persistence.encode("audit", audit_value),
                canonical_json(dict(_mapping_field(audit_value, "evidence_refs"))),
                _text_field(audit_value, "config_hash"),
                _field(audit_value, "decision_id"),
                occurred_at,
                _text_field(audit_value, "previous_hash"),
                _text_field(audit_value, "record_hash"),
                request_id,
                _text_field(audit_value, "correlation_id"),
                occurred_at,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _COMPOUND_WRITE_ROWS


def update_equity_history_record(
    *,
    account_id: str,
    peak_equity: str,
    day_start_equity: str,
    day_start_date: str,
    updated_at: str,
    expected_revision: str,
) -> None:
    """Compare and swap one account's tracked peak/day-start equity.

    Raises:
        ValueError: If the stored update token no longer matches.
    """
    result = _execute(
        (
            "UPDATE risk_equity_history SET peak_equity=?, day_start_equity=?, "
            "day_start_date=?, updated_at=? WHERE account_id=? AND updated_at=?",
        ),
        (
            (
                peak_equity,
                day_start_equity,
                day_start_date,
                updated_at,
                account_id,
                expected_revision,
            ),
        ),
    )
    if result.affected_rows != 1:
        raise ValueError("Risk equity history revision conflict")


__all__ = [
    "update_active_allocation_record",
    "update_approval_state_record",
    "update_equity_history_record",
    "update_kill_switch_with_audit",
]
