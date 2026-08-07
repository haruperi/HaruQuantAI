"""Read operations for Risk-owned relational records."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.risk.persistence.create import _execute, _require_store
from app.utils import get_logger

logger = get_logger(__name__)


def _one_row(
    statement: str,
    parameters: tuple[object, ...],
) -> Mapping[str, object] | None:
    """Read at most one normalized row.

    Returns:
        Stored row or ``None``.
    """
    rows = _execute((statement,), (parameters,)).rows
    return None if not rows else rows[0]


def read_approval_state_record(store: object, key: str) -> object | None:
    """Read one approval lifecycle state.

    Returns:
        Decoded state or ``None``.
    """
    row = _one_row(
        "SELECT payload_json FROM risk_approval_tokens WHERE token_id=?",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("approval-state", str(row["payload_json"]))


def read_approval_state_record_with_revision(
    store: object,
    key: str,
) -> tuple[Mapping[str, object], str] | None:
    """Read one approval state with its update-time CAS token.

    Returns:
        Decoded state and token, or ``None``.

    Raises:
        TypeError: If the stored state is malformed.
    """
    row = _one_row(
        "SELECT payload_json, updated_at FROM risk_approval_tokens WHERE token_id=?",
        (key,),
    )
    if row is None:
        return None
    decoded = _require_store(store).decode("approval-state", str(row["payload_json"]))
    if not isinstance(decoded, Mapping):
        raise TypeError("stored Risk approval state is malformed")
    return decoded, str(row["updated_at"])


def read_approval_index_records(store: object) -> tuple[Mapping[str, object], ...]:
    """Read the enumerable approval identities in issuance order.

    Returns:
        Ordered approval identity records.
    """
    _require_store(store)
    rows = _execute(
        (
            "SELECT token_id FROM risk_approval_tokens "
            "ORDER BY created_at ASC, token_id ASC LIMIT 1000",
        ),
        ((),),
        max_rows=1_000,
    ).rows
    return tuple({"approval_id": str(row["token_id"])} for row in rows)


def read_audit_record(store: object, key: str) -> object | None:
    """Read one immutable Risk audit record.

    Returns:
        Decoded audit record or ``None``.
    """
    row = _one_row(
        "SELECT payload_json FROM risk_audit_records WHERE record_id=?",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("audit", str(row["payload_json"]))


def read_audit_records(store: object) -> tuple[object, ...]:
    """Read the complete ordered Risk audit chain.

    Returns:
        Ordered decoded audit records.
    """
    rows = _execute(
        (
            "SELECT payload_json FROM risk_audit_records "
            "ORDER BY sequence ASC LIMIT 1000",
        ),
        ((),),
        max_rows=1_000,
    ).rows
    persistence = _require_store(store)
    return tuple(persistence.decode("audit", str(row["payload_json"])) for row in rows)


def read_decision_records(store: object, limit: int) -> tuple[object, ...]:
    """Read a bounded newest-first page of canonical Risk decisions.

    Returns:
        Ordered decoded decisions.

    Raises:
        ValueError: If the bound is not positive.
    """
    if limit <= 0:
        raise ValueError("Risk decision read limit must be positive")
    rows = _execute(
        (
            "SELECT payload_json FROM risk_decision_snapshots "
            "WHERE record_type='decision' "
            "ORDER BY occurred_at DESC, record_id DESC LIMIT ?",
        ),
        ((limit,),),
        max_rows=limit,
    ).rows
    persistence = _require_store(store)
    return tuple(
        persistence.decode("decision", str(row["payload_json"])) for row in rows
    )


def read_decision_record(store: object, decision_id: str) -> object | None:
    """Read one immutable canonical Risk decision by identity.

    Returns:
        Decoded decision or ``None``.
    """
    row = _one_row(
        "SELECT payload_json FROM risk_decision_snapshots "
        "WHERE record_id=? AND record_type='decision'",
        (decision_id,),
    )
    if row is None:
        return None
    return _require_store(store).decode("decision", str(row["payload_json"]))


def read_active_allocation_record(store: object, key: str) -> object | None:
    """Read one active Risk allocation decision.

    Returns:
        Decoded active decision or ``None``.
    """
    row = _one_row(
        "SELECT payload_json FROM risk_allocation_decisions "
        "WHERE portfolio_id=? AND active=1",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("allocation", str(row["payload_json"]))


def read_active_allocation_record_with_revision(
    store: object,
    key: str,
) -> tuple[object, str] | None:
    """Read one active allocation and its decision-identity CAS token.

    Returns:
        Decoded decision and token, or ``None``.
    """
    row = _one_row(
        "SELECT decision_id, payload_json FROM risk_allocation_decisions "
        "WHERE portfolio_id=? AND active=1",
        (key,),
    )
    if row is None:
        return None
    value = _require_store(store).decode("allocation", str(row["payload_json"]))
    return value, str(row["decision_id"])


def read_kill_switch_record(store: object, key: str) -> object | None:
    """Read one canonical Risk kill-switch state.

    Returns:
        Decoded state or ``None``.
    """
    row = _one_row(
        "SELECT payload_json FROM risk_kill_switch_states WHERE state_id=?",
        (key,),
    )
    if row is None:
        return None
    return _require_store(store).decode("kill-switch", str(row["payload_json"]))


def read_policy_version(config_hash: str) -> Mapping[str, object] | None:
    """Read one normalized Risk policy row by exact hash.

    Returns:
        Stored row mapping or ``None``.
    """
    return _one_row(
        "SELECT config_hash, policy_version, profile, payload_json, effective_at, "
        "request_id, correlation_id, created_at, updated_at "
        "FROM risk_policy_versions WHERE config_hash=?",
        (config_hash,),
    )


__all__ = [
    "read_active_allocation_record",
    "read_active_allocation_record_with_revision",
    "read_approval_index_records",
    "read_approval_state_record",
    "read_approval_state_record_with_revision",
    "read_audit_record",
    "read_audit_records",
    "read_decision_record",
    "read_decision_records",
    "read_kill_switch_record",
    "read_policy_version",
]
