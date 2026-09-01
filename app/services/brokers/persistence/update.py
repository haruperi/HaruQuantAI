"""Update operations for Brokers-owned symbol mappings."""

from __future__ import annotations

from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)

_CLOSE_MAPPING = """
UPDATE broker_symbol_map
SET effective_to = ?, updated_at = ?
WHERE provider_code = ? AND symbol_id = ? AND effective_to IS NULL
""".strip()

_DISABLE_MAPPING = """
UPDATE broker_symbol_map
SET enabled = 0, updated_at = ?
WHERE map_id = ?
""".strip()

_UPSERT_ROUTE_RECOVERY = """
INSERT INTO broker_route_recovery (
    route_ref, provider_code, account_ref_digest, environment,
    recovery_cursor, uncertainty, request_id, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(route_ref) DO UPDATE SET
    provider_code = excluded.provider_code,
    account_ref_digest = excluded.account_ref_digest,
    environment = excluded.environment,
    recovery_cursor = excluded.recovery_cursor,
    uncertainty = excluded.uncertainty,
    request_id = excluded.request_id,
    updated_at = excluded.updated_at
""".strip()

_UPSERT_EVENT_CHECKPOINT = """
INSERT INTO broker_event_checkpoints (
    checkpoint_id, provider_code, account_ref_digest, source_stream,
    source_cursor, source_sequence, event_digest, request_id, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(provider_code, account_ref_digest, source_stream) DO UPDATE SET
    source_cursor = excluded.source_cursor,
    source_sequence = excluded.source_sequence,
    event_digest = excluded.event_digest,
    request_id = excluded.request_id,
    updated_at = excluded.updated_at
""".strip()


def _execute(
    statement: str, parameters: tuple[Any, ...], *, request_id: str, max_rows: int
) -> object:
    """Execute one bounded Brokers statement.

    Args:
        statement: Single SQL statement.
        parameters: Ordered parameter values.
        request_id: Caller trace identity.
        max_rows: Bounded row ceiling.

    Returns:
        Data-owned transaction result.
    """
    return execute_transaction(
        build_transaction_request(
            plan=build_statement_plan(
                statements=(statement,),
                parameter_sets=(parameters,),
                max_rows=max_rows,
            ),
            request_id=request_id,
        )
    )


def close_symbol_mapping(
    effective_to: str,
    updated_at: str,
    provider_code: str,
    symbol_id: str,
    *,
    request_id: str,
) -> object:
    """Close the open mapping for one instrument so a successor can begin.

    Closing rather than rewriting is what preserves the bitemporal record.

    Args:
        effective_to: Exclusive end of the mapping's validity.
        updated_at: Update timestamp.
        provider_code: Provider identity.
        symbol_id: Canonical symbol identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Closing one Brokers symbol mapping")
    return _execute(
        _CLOSE_MAPPING,
        (effective_to, updated_at, provider_code, symbol_id),
        request_id=request_id,
        max_rows=1,
    )


def disable_symbol_mapping(updated_at: str, map_id: str, *, request_id: str) -> object:
    """Disable one mapping without closing its validity window.

    Args:
        updated_at: Update timestamp.
        map_id: Mapping identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Disabling one Brokers symbol mapping")
    return _execute(
        _DISABLE_MAPPING, (updated_at, map_id), request_id=request_id, max_rows=1
    )


def upsert_route_recovery_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Atomically create or advance one route recovery cursor.

    Args:
        parameters: Ordered route-recovery column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Advancing one broker route recovery cursor")
    return _execute(
        _UPSERT_ROUTE_RECOVERY, parameters, request_id=request_id, max_rows=1
    )


def upsert_event_checkpoint_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Atomically create or advance one event deduplication checkpoint.

    Args:
        parameters: Ordered event-checkpoint column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Advancing one broker event checkpoint")
    return _execute(
        _UPSERT_EVENT_CHECKPOINT, parameters, request_id=request_id, max_rows=1
    )
