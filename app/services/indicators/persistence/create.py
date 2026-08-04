"""Create operations for Indicators-owned records."""

from __future__ import annotations

from typing import Any

from app.services.data import build_transaction_request, execute_transaction
from app.utils import get_logger

logger = get_logger(__name__)

_INSERT_DEFINITION = """
INSERT INTO indicator_definitions (
    definition_id, indicator_code, version, category, formula_hash,
    param_schema_json, output_names_json, lookback_bars, is_causal, state,
    request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_PARAM_SET = """
INSERT INTO indicator_param_sets (
    param_set_id, definition_id, params_json, params_hash, label,
    created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?)
""".strip()

_INSERT_MATERIALIZATION = """
INSERT INTO indicator_materializations (
    materialization_id, definition_id, param_set_id, symbol_id, timeframe,
    dataset_id, source_dataset_id, source_data_hash, formula_hash,
    covered_from_utc, covered_to_utc, row_count, state, built_at,
    request_id, correlation_id, created_at, updated_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""".strip()


def _execute(statement: str, parameters: tuple[Any, ...], *, request_id: str) -> object:
    """Execute one bounded Indicators write.

    Args:
        statement: Single SQL statement.
        parameters: Ordered parameter values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    return execute_transaction(
        build_transaction_request(
            statements=(statement,),
            parameter_sets=(parameters,),
            max_rows=1,
            request_id=request_id,
        )
    )


def create_indicator_definition_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Register one immutable indicator definition.

    A definition is identified by ``(indicator_code, version)`` and carries a
    ``formula_hash``. Changing the formula must produce a new version rather
    than mutate this row, because every materialisation records the hash it was
    built from.

    Args:
        parameters: Ordered ``indicator_definitions`` column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Registering one Indicators definition")
    return _execute(_INSERT_DEFINITION, parameters, request_id=request_id)


def create_indicator_param_set_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Register one parameter set for an indicator definition.

    Args:
        parameters: Ordered ``indicator_param_sets`` column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.debug("Registering one Indicators parameter set")
    return _execute(_INSERT_PARAM_SET, parameters, request_id=request_id)


def create_indicator_materialization_record(
    parameters: tuple[Any, ...], *, request_id: str
) -> object:
    """Record that an indicator series has been materialised to an artifact.

    Args:
        parameters: Ordered ``indicator_materializations`` column values.
        request_id: Caller trace identity.

    Returns:
        Data-owned transaction result.
    """
    logger.info("Recording one Indicators materialisation")
    return _execute(_INSERT_MATERIALIZATION, parameters, request_id=request_id)
