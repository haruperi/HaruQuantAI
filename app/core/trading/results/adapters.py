"""Adapter converting execution backtest results to databank persistence contracts.

Description:
    Provides explicit, typed conversions between execution-domain backtest results
    (BacktestRunResult) and persistence-domain databank results (StoredRunResult).
    Orchestrates trade and equity curve serialization, preserves Maximum Adverse
    Excursion (MAE) and Maximum Favorable Excursion (MFE) excursion metrics, ensures
    drawdown metric mapping, and validates JSON payloads against non-finite or invalid
    values to fail closed before persistence.

Purpose:
    FEAT-RESULTS-ADAPTER

Key Capabilities:
    FR-BACKTEST-RESULT-CONVERSION: Explicit conversion from BacktestRunResult
        to StoredRunResult.
    FR-MAE-MFE-PRESERVATION: Serializes and preserves MAE/MFE records across
        persistence boundaries.
    FR-PAYLOAD-VALIDATION: Validates payload and metrics, failing closed on
        non-finite values or missing identity.

Python API Usage:
    from app.core.trading.results.adapters import from_backtest_result

    stored_result = from_backtest_result(
        backtest_result,
        result_id="res-001",
        databank_id="db-default",
        strategy_name="TrendFollower",
    )

CLI Usage:
    N/A (Library-level contract adapter).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue, copy_json
from app.core.trading.backtest.contracts import (
    RunResult as BacktestRunResult,
)
from app.core.trading.results.contracts import (
    RunResult as StoredRunResult,
)

logger = get_logger(__name__)


def _check_finite_json(val: Any) -> None:
    """Recursively verify that no floating point numbers in payload are NaN or Inf."""
    if isinstance(val, float):
        if not math.isfinite(val):
            msg = f"Non-finite float value encountered: {val}"
            raise DomainError(code="INVALID_RESULT_PAYLOAD", message=msg)
    elif isinstance(val, dict):
        for k, v in val.items():
            if not isinstance(k, str):
                msg = f"Non-string dictionary key encountered: {k!r}"
                raise DomainError(code="INVALID_RESULT_PAYLOAD", message=msg)
            _check_finite_json(v)
    elif isinstance(val, (list, tuple)):
        for item in val:
            _check_finite_json(item)


def _to_json_dict_tuple(
    items: list[dict[str, Any]],
) -> tuple[dict[str, JSONValue], ...]:
    """Safely detach, copy, and filter list of dictionary records."""
    out: list[dict[str, JSONValue]] = []
    for item in items:
        copied = copy_json(item)
        if isinstance(copied, dict):
            out.append(copied)
    return tuple(out)


def from_backtest_result(
    result: BacktestRunResult,
    *,
    result_id: str,
    databank_id: str,
    strategy_name: str,
    parameters: Mapping[str, JSONValue] | None = None,
    strategy_payload: Mapping[str, JSONValue] | None = None,
) -> StoredRunResult:
    """Convert an execution BacktestRunResult into a persistence StoredRunResult.

    Args:
        result: Historical backtest execution result from BacktestRunner.
        result_id: Unique persistence identifier for the databank record.
        databank_id: Target databank destination identifier.
        strategy_name: Human-readable strategy name.
        parameters: Optional strategy input parameters mapping.
        strategy_payload: Optional serialized strategy AST or rules definition.

    Returns:
        StoredRunResult compatible with ResultStore.save_result.

    Raises:
        DomainError: If identity fields are invalid or payload contains
            non-finite values.
    """
    clean_result_id = str(result_id).strip()
    if not clean_result_id:
        msg = "result_id must be a non-empty string"
        raise DomainError(code="INVALID_RESULT_PAYLOAD", message=msg)

    clean_databank_id = str(databank_id).strip()
    if not clean_databank_id:
        msg = "databank_id must be a non-empty string"
        raise DomainError(code="INVALID_RESULT_PAYLOAD", message=msg)

    clean_strategy_name = str(strategy_name).strip()
    if not clean_strategy_name:
        msg = "strategy_name must be a non-empty string"
        raise DomainError(code="INVALID_RESULT_PAYLOAD", message=msg)

    # Serialize trades, equity curve, and MAE/MFE records
    trades_list = [t.to_dict() for t in result.trades]
    equity_list = [e.to_dict() for e in result.equity_curve]
    mae_mfe_list = [m.to_dict() for m in result.mae_mfe]

    # Metrics handling: preserve all original metrics, and map max_drawdown to drawdown
    metrics_dict: dict[str, float | int | str] = dict(result.metrics)

    if "drawdown" not in metrics_dict and "max_drawdown" in metrics_dict:
        metrics_dict["drawdown"] = metrics_dict["max_drawdown"]

    # Detach mutable parameters and strategy_payload
    copied_params: dict[str, JSONValue] = {}
    if parameters:
        c_p = copy_json(dict(parameters))
        if isinstance(c_p, dict):
            copied_params = c_p

    copied_payload: dict[str, JSONValue] = {}
    if strategy_payload:
        c_pay = copy_json(dict(strategy_payload))
        if isinstance(c_pay, dict):
            copied_payload = c_pay

    # Validate against non-finite floats
    _check_finite_json(metrics_dict)
    _check_finite_json(trades_list)
    _check_finite_json(equity_list)
    _check_finite_json(mae_mfe_list)
    _check_finite_json(copied_params)
    _check_finite_json(copied_payload)

    trades_tuple = _to_json_dict_tuple(trades_list)
    equity_tuple = _to_json_dict_tuple(equity_list)
    mae_mfe_tuple = _to_json_dict_tuple(mae_mfe_list)

    stored = StoredRunResult(
        result_id=clean_result_id,
        databank_id=clean_databank_id,
        strategy_id=result.strategy_id,
        strategy_name=clean_strategy_name,
        metrics=metrics_dict,
        trades=trades_tuple,
        equity_curve=equity_tuple,
        mae_mfe=mae_mfe_tuple,
        parameters=copied_params,
        strategy_payload=copied_payload,
    )

    logger.info(
        "Converted BacktestRunResult to StoredRunResult "
        "(result_id=%s, strategy=%s, databank=%s, trades=%d, mae_mfe=%d)",
        clean_result_id,
        clean_strategy_name,
        clean_databank_id,
        len(trades_tuple),
        len(mae_mfe_tuple),
    )

    return stored


__all__ = ["from_backtest_result"]
