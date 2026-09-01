"""Atomic update operations for Portfolio-owned relational records."""

from __future__ import annotations

from app.kernel.serialization import canonical_json
from app.services.portfolio.persistence.create import (
    _execute,
    _mapping_field,
    _outbox_parameters,
    _require_store,
    _text_field,
    _time_field,
)

_ALLOCATION_WRITE_ROWS = 4


def update_active_allocation_record(
    store: object,
    *,
    state_value: object,
    expected_revision: int,
    event_key: str,
    event_sequence: int,
    event_value: object,
) -> bool:
    """Atomically persist allocation, idempotency, active CAS, and outbox.

    Args:
        store: Portfolio persistence handle.
        state_value: Allocation model object.
        expected_revision: Expected active scope revision.
        event_key: Stable outbox event identity.
        event_sequence: Positive sequence number.
        event_value: Redacted audit event object.

    Returns:
        Whether all four records committed atomically.

    Raises:
        ValueError: If revision, identity, or material evidence conflicts.
    """
    persistence = _require_store(store)
    if expected_revision < 0 or event_sequence <= 0:
        raise ValueError("Portfolio allocation transition evidence is invalid")
    portfolio_id = _text_field(state_value, "portfolio_id")
    allocation_id = _text_field(state_value, "allocation_id")
    allocation_version = _text_field(state_value, "allocation_version")
    material_hash = _text_field(state_value, "canonical_hash")
    idempotency_key = _text_field(state_value, "idempotency_key")
    activated_at = _time_field(state_value, "activated_at").isoformat()
    request_id = _text_field(state_value, "request_id")
    correlation_id = _text_field(state_value, "correlation_id")
    scope_key = canonical_json(
        dict(_mapping_field(state_value, "scope")), max_items=None
    )
    result = _execute(
        (
            "INSERT INTO portfolio_idempotency "
            "(idempotency_key, material_hash, result_type, result_id, created_at, "
            "request_id, correlation_id) VALUES (?, ?, 'allocation', ?, ?, ?, ?) "
            "ON CONFLICT(idempotency_key) DO UPDATE SET material_hash=CASE WHEN "
            "portfolio_idempotency.material_hash=excluded.material_hash AND "
            "portfolio_idempotency.result_id=excluded.result_id THEN "
            "excluded.material_hash ELSE NULL END",
            "INSERT INTO portfolio_allocation_versions "
            "(allocation_id, portfolio_id, allocation_version, scope_key, "
            "canonical_hash, allocation_json, activated_at, request_id, "
            "correlation_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(allocation_id) DO UPDATE SET allocation_json=CASE WHEN "
            "portfolio_allocation_versions.allocation_json=excluded.allocation_json "
            "THEN excluded.allocation_json ELSE NULL END",
            "INSERT INTO portfolio_active_scopes "
            "(portfolio_id, scope_key, allocation_version, revision, request_id, "
            "correlation_id, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?, ?, ?) "
            "ON CONFLICT(portfolio_id, scope_key) DO UPDATE SET "
            "allocation_version=CASE WHEN portfolio_active_scopes.revision=? THEN "
            "excluded.allocation_version ELSE NULL END, "
            "revision=portfolio_active_scopes.revision+1, "
            "request_id=excluded.request_id, correlation_id=excluded.correlation_id, "
            "updated_at=excluded.updated_at",
            (
                "INSERT INTO portfolio_audit_outbox "
                "(event_id, event_type, aggregate_id, request_id, correlation_id, "
                "payload_json, occurred_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(event_id) DO UPDATE SET event_id=excluded.event_id, "
                "payload_json=CASE WHEN portfolio_audit_outbox.payload_json="
                "excluded.payload_json THEN excluded.payload_json ELSE NULL END"
            ),
        ),
        (
            (
                idempotency_key,
                material_hash,
                allocation_id,
                activated_at,
                request_id,
                correlation_id,
            ),
            (
                allocation_id,
                portfolio_id,
                allocation_version,
                scope_key,
                material_hash,
                persistence.encode("allocation", state_value),
                activated_at,
                request_id,
                correlation_id,
                activated_at,
            ),
            (
                portfolio_id,
                scope_key,
                allocation_version,
                request_id,
                correlation_id,
                activated_at,
                activated_at,
                expected_revision,
            ),
            _outbox_parameters(
                persistence,
                event_key=event_key,
                aggregate_id=portfolio_id,
                event_value=event_value,
                occurred_at=activated_at,
                request_id=request_id,
                correlation_id=correlation_id,
            ),
        ),
        request_id=request_id,
    )
    return result.affected_rows >= _ALLOCATION_WRITE_ROWS


__all__ = ["update_active_allocation_record"]
