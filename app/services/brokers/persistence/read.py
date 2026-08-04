"""Read operations for Brokers-owned symbol mappings."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

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
            statements=(statement,),
            parameter_sets=(parameters,),
            max_rows=max_rows,
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
