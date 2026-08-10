"""Create operations for Brokers-owned symbol mappings."""

from __future__ import annotations

from typing import Any

from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)
from app.utils import get_logger

logger = get_logger(__name__)

_INSERT_SYMBOL_MAP = """
INSERT INTO broker_symbol_map (
    map_id, provider_code, symbol_id, provider_symbol, contract_size_decimal,
    digits_override, enabled, effective_from, effective_to,
    request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_HEALTH = """
INSERT INTO broker_health_history (
    checkpoint_id, provider_code, account_ref_digest, environment,
    health_status, latency_ms_decimal, error_rate_decimal, maintenance,
    route_ready, observed_at, request_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_PERMISSION = """
INSERT INTO broker_environment_permissions (
    permission_id, provider_code, account_ref_digest, environment,
    allow_read, allow_mutation, enabled, effective_from, effective_to,
    request_id, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def create_symbol_map_record(parameters: tuple[Any, ...], *, request_id: str) -> object:
    """Register one provider-to-canonical symbol mapping.

    Mappings are bitemporal. A broker that renames an instrument produces a new
    row with a later ``effective_from``; the prior row is closed rather than
    edited, so a backtest over an earlier period still resolves the instrument
    it actually traded.

    Args:
        parameters: Ordered ``broker_symbol_map`` column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Registering one Brokers symbol mapping")
    return _execute(_INSERT_SYMBOL_MAP, parameters, request_id=request_id, max_rows=1)


def create_health_record(parameters: tuple[Any, ...], *, request_id: str) -> object:
    """Persist one immutable broker health checkpoint.

    Args:
        parameters: Ordered health-history column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Recording one redacted broker health checkpoint")
    return _execute(_INSERT_HEALTH, parameters, request_id=request_id, max_rows=1)


def create_environment_permission_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Persist one default-deny environment/account permission record.

    Args:
        parameters: Ordered permission column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Recording one broker environment permission")
    return _execute(_INSERT_PERMISSION, parameters, request_id=request_id, max_rows=1)
