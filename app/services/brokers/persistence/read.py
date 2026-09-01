"""Read operations for Brokers-owned symbol mappings."""

from __future__ import annotations

from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)

_SELECT_FORWARD = """
SELECT provider_symbol, contract_size_decimal, digits_override
FROM broker_symbol_map
WHERE provider_code = ? AND symbol_id = ?
  AND enabled = 1 AND effective_to IS NULL
""".strip()

_SELECT_REVERSE = """
SELECT symbol_id, contract_size_decimal, digits_override
FROM broker_symbol_map
WHERE provider_code = ? AND provider_symbol = ?
  AND enabled = 1 AND effective_to IS NULL
""".strip()

_SELECT_AS_OF = """
SELECT provider_symbol, contract_size_decimal, digits_override
FROM broker_symbol_map
WHERE provider_code = ? AND symbol_id = ?
  AND effective_from <= ?
  AND (effective_to IS NULL OR effective_to > ?)
ORDER BY effective_from DESC
""".strip()

_SELECT_PERMISSION = """
SELECT allow_read, allow_mutation
FROM broker_environment_permissions
WHERE provider_code = ? AND account_ref_digest = ? AND environment = ?
  AND enabled = 1 AND effective_from <= ?
  AND (effective_to IS NULL OR effective_to > ?)
ORDER BY effective_from DESC
""".strip()

_SELECT_ROUTE_RECOVERY = """
SELECT provider_code, account_ref_digest, environment, recovery_cursor,
       uncertainty, updated_at
FROM broker_route_recovery
WHERE route_ref = ?
""".strip()

_SELECT_EVENT_CHECKPOINT = """
SELECT source_cursor, source_sequence, event_digest, updated_at
FROM broker_event_checkpoints
WHERE provider_code = ? AND account_ref_digest = ? AND source_stream = ?
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


def read_provider_symbol(
    provider_code: str, symbol_id: str, *, request_id: str
) -> object:
    """Resolve the current provider symbol for a canonical instrument.

    Args:
        provider_code: Provider identity.
        symbol_id: Canonical symbol identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Resolving one Brokers provider symbol")
    return _execute(
        _SELECT_FORWARD, (provider_code, symbol_id), request_id=request_id, max_rows=1
    )


def read_canonical_symbol(
    provider_code: str, provider_symbol: str, *, request_id: str
) -> object:
    """Resolve the canonical instrument for a provider symbol.

    Args:
        provider_code: Provider identity.
        provider_symbol: Provider-side symbol string.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Resolving one Brokers canonical symbol")
    return _execute(
        _SELECT_REVERSE,
        (provider_code, provider_symbol),
        request_id=request_id,
        max_rows=1,
    )


def read_provider_symbol_as_of(
    provider_code: str, symbol_id: str, as_of: str, *, request_id: str
) -> object:
    """Resolve the provider symbol that applied at a point in time.

    This is the read a backtest must use. Resolving a historical bar through the
    *current* mapping silently attributes it to whatever instrument the provider
    named later.

    Args:
        provider_code: Provider identity.
        symbol_id: Canonical symbol identity.
        as_of: Point in time to resolve against.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result carrying at most one row.
    """
    logger.debug("Resolving one Brokers symbol mapping as of a point in time")
    return _execute(
        _SELECT_AS_OF,
        (provider_code, symbol_id, as_of, as_of),
        request_id=request_id,
        max_rows=1,
    )


def read_environment_permission(
    provider_code: str,
    account_ref_digest: str,
    environment: str,
    as_of: str,
    *,
    request_id: str,
) -> object:
    """Read the current explicit environment/account permission.

    Args:
        provider_code: Exact provider identity.
        account_ref_digest: Redacted account-reference digest.
        environment: Exact provider environment.
        as_of: Permission evaluation timestamp.
        request_id: Caller trace identity.

    Returns:
        Data-owned result carrying at most one permission row.
    """
    return _execute(
        _SELECT_PERMISSION,
        (provider_code, account_ref_digest, environment, as_of, as_of),
        request_id=request_id,
        max_rows=1,
    )


def read_route_recovery(route_ref: str, *, request_id: str) -> object:
    """Read one authoritative route recovery cursor.

    Args:
        route_ref: Stable route reference.
        request_id: Caller trace identity.

    Returns:
        Data-owned result carrying at most one route row.
    """
    return _execute(
        _SELECT_ROUTE_RECOVERY, (route_ref,), request_id=request_id, max_rows=1
    )


def read_event_checkpoint(
    provider_code: str,
    account_ref_digest: str,
    source_stream: str,
    *,
    request_id: str,
) -> object:
    """Read one event deduplication checkpoint.

    Args:
        provider_code: Exact provider identity.
        account_ref_digest: Redacted account-reference digest.
        source_stream: Exact provider stream identity.
        request_id: Caller trace identity.

    Returns:
        Data-owned result carrying at most one checkpoint row.
    """
    return _execute(
        _SELECT_EVENT_CHECKPOINT,
        (provider_code, account_ref_digest, source_stream),
        request_id=request_id,
        max_rows=1,
    )
