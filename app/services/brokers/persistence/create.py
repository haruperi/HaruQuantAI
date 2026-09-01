"""Create operations for temporary Brokers-owned operational records."""

from __future__ import annotations

from typing import Any

from app.composition.logging import get_logger
from app.services.data import (
    build_statement_plan,
    build_transaction_request,
    execute_transaction,
)

logger = get_logger(__name__)

_INSERT_HEALTH = """
INSERT INTO broker_health_history (
    checkpoint_id, provider_code, account_ref_digest, environment,
    health_status, latency_ms_decimal, error_rate_decimal, maintenance,
    route_ready, observed_at, request_id, created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
