"""Shared response and serialization helpers for HaruQuant indicator tools.

This file contains internal helpers only. Official AI Tools are exposed through
``tools.indicators.__init__`` and must return the standard HaruQuant tool
response schema.

Classes:
    ToolSpec: Metadata container used to build standard responses.

Functions:
    build_tool_response: Build a schema-compliant tool response.
    dataframe_to_records: Serialize DataFrames safely.
    series_to_list: Serialize Series safely.
    run_indicator_tool: Execute indicator logic with logging, timing, and errors.

Exported AI Tools:
    None.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ToolSpec:
    """Metadata used by official HaruQuant AI Tool responses.

    Args:
        tool_name: Public tool name.
        tool_category: Tool domain/category.
        tool_version: Semantic version string.
        tool_risk_level: Risk level: low, medium, high, or critical.
        read_only: Whether the tool is read-only.
        writes_file: Whether the tool writes local files.
        modifies_database: Whether the tool modifies a database.
        places_trade: Whether the tool places or closes trades.
        requires_network: Whether the tool requires network access.
        requires_approval: Whether the tool requires explicit approval.
    """

    tool_name: str
    tool_category: str = "indicators"
    tool_version: str = "1.0.0"
    tool_risk_level: str = "low"
    read_only: bool = True
    writes_file: bool = False
    modifies_database: bool = False
    places_trade: bool = False
    requires_network: bool = False
    requires_approval: bool = False


def _json_safe(value: Any) -> Any:
    """Convert pandas/numpy scalar values into JSON-safe Python values."""
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def dataframe_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Serialize a DataFrame into records while preserving index information.

    Args:
        frame: DataFrame to serialize.

    Returns:
        List of dictionaries with an ``index`` field plus DataFrame columns.
    """
    serialized = frame.copy()
    serialized.insert(0, "index", [_json_safe(item) for item in serialized.index])
    return [
        {key: _json_safe(value) for key, value in row.items()}
        for row in serialized.to_dict(orient="records")
    ]


def series_to_list(series: pd.Series) -> list[Any]:
    """Serialize a pandas Series to a JSON-safe list."""
    return [_json_safe(value) for value in series.to_list()]


def serialize_payload(value: Any) -> Any:
    """Serialize common indicator outputs into JSON-safe payloads."""
    if isinstance(value, pd.DataFrame):
        return dataframe_to_records(value)
    if isinstance(value, pd.Series):
        return series_to_list(value)
    if isinstance(value, Mapping):
        return {str(key): serialize_payload(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [serialize_payload(item) for item in value]
    if isinstance(value, list):
        return [serialize_payload(item) for item in value]
    return _json_safe(value)


def build_tool_response(
    spec: ToolSpec,
    *,
    status: str,
    message: str,
    data: Any = None,
    error: dict[str, str] | None = None,
    request_id: str | None = None,
    execution_ms: float = 0.0,
) -> dict[str, Any]:
    """Build a standard HaruQuant AI Tool response.

    Args:
        spec: Tool metadata.
        status: ``success`` or ``error``.
        message: Human-readable result message.
        data: Optional result payload.
        error: Optional standard error dictionary.
        request_id: Optional trace identifier.
        execution_ms: Execution time in milliseconds.

    Returns:
        Schema-compliant tool response dictionary.
    """
    return {
        "status": status,
        "message": message,
        "data": serialize_payload(data),
        "error": error,
        "metadata": {
            "tool_name": spec.tool_name,
            "tool_version": spec.tool_version,
            "tool_category": spec.tool_category,
            "tool_risk_level": spec.tool_risk_level,
            "request_id": request_id,
            "execution_ms": execution_ms,
            "read_only": spec.read_only,
            "writes_file": spec.writes_file,
            "modifies_database": spec.modifies_database,
            "places_trade": spec.places_trade,
            "requires_network": spec.requires_network,
        },
    }


def run_indicator_tool(
    spec: ToolSpec,
    operation: Callable[[], Any],
    *,
    request_id: str | None = None,
    success_message: str | None = None,
) -> dict[str, Any]:
    """Run an indicator operation with standard logging and error handling.

    Args:
        spec: Tool metadata for the public tool.
        operation: Zero-argument calculation function.
        request_id: Optional request/workflow identifier.
        success_message: Optional custom success message.

    Returns:
        Standard HaruQuant tool response.
    """
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", spec.tool_name, request_id)

    try:
        result = operation()
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info(
            "%s completed | request_id=%s | execution_ms=%s",
            spec.tool_name,
            request_id,
            execution_ms,
        )
        return build_tool_response(
            spec,
            status="success",
            message=success_message or "Indicator calculated successfully.",
            data=result,
            error=None,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except (TypeError, ValueError, LookupError) as exc:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "%s validation failed | request_id=%s | error=%s",
            spec.tool_name,
            request_id,
            exc,
        )
        return build_tool_response(
            spec,
            status="error",
            message="Invalid input.",
            data=None,
            error={"code": "INVALID_INPUT", "details": str(exc)},
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as exc:  # pragma: no cover - safety boundary
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception(
            "%s failed | request_id=%s | execution_ms=%s",
            spec.tool_name,
            request_id,
            execution_ms,
        )
        return build_tool_response(
            spec,
            status="error",
            message="Tool execution failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            execution_ms=execution_ms,
        )
