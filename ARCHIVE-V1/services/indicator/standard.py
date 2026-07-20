"""Standard response helpers for indicator tools.

Purpose:
    Provide shared wrapping utilities for exported AI-callable indicator tools.

Exported AI Tools:
    None. This module contains internal helpers only.

Internal Helpers:
    - run_indicator_tool: Execute an indicator implementation with standard
      response schema, logging, timing, and serialization.
    - serialize_indicator_result: Convert pandas-heavy indicator outputs into
      JSON-safe payloads.

Classes:
    None
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
from app.services.data.frames import _serialize_frame_records
from app.services.utils.logger import logger
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

INDICATOR_TOOL_SPEC = ToolStandardSpec(
    tool_name="indicator",
    tool_category="indicator",
    tool_risk_level="low",
    requires_approval=False,
    read_only=True,
    writes_file=False,
    modifies_database=False,
    places_trade=False,
    requires_network=False,
)


def serialize_indicator_result(value: Any) -> Any:
    """Serialize indicator output into JSON-safe data.

    Args:
        value: Indicator output, commonly a pandas DataFrame, Series, tuple,
            list, or dictionary.

    Returns:
        Any: JSON-safe representation of the indicator output.
    """
    if isinstance(value, pd.DataFrame):
        return _serialize_frame_records(value)
    if isinstance(value, pd.Series):
        return value.to_list()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [serialize_indicator_result(item) for item in value]
    if isinstance(value, list):
        return [serialize_indicator_result(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_indicator_result(item) for key, item in value.items()}
    return value


def run_indicator_tool(
    tool_name: str,
    operation: Callable[[], Any],
    *,
    request_id: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Run an indicator operation and return the standard AI tool schema.

    Use this helper from exported indicator tools so every public indicator
    returns status, message, data, error, and metadata with traceable timing.

    Args:
        tool_name: Public exported tool name.
        operation: Zero-argument callable that performs validation and
            calculation.
        request_id: Optional workflow/request ID for traceability.
        message: Optional success message.

    Returns:
        Dict[str, Any]: Standard tool response containing serialized indicator
        data or a deterministic error code.
    """
    spec = ToolStandardSpec(
        **{
            **INDICATOR_TOOL_SPEC.__dict__,
            "tool_name": tool_name,
        }
    )
    started_at = time.perf_counter()

    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        result = operation()
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "%s completed successfully | request_id=%s | execution_ms=%s",
            tool_name,
            request_id,
            execution_ms,
        )
        return standard_tool_response(
            spec,
            "success",
            message or "Indicator tool executed successfully.",
            data={
                "source": tool_name,
                "data": serialize_indicator_result(result),
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )

    except (TypeError, ValueError, LookupError, KeyError) as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.warning(
            "%s validation failed | request_id=%s | reason=%s",
            tool_name,
            request_id,
            error,
        )
        return standard_tool_response(
            spec,
            "error",
            "Invalid input.",
            error={
                "code": "INVALID_INPUT",
                "details": str(error),
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.exception(
            "%s failed | request_id=%s | execution_ms=%s",
            tool_name,
            request_id,
            execution_ms,
        )
        return standard_tool_response(
            spec,
            "error",
            "Tool execution failed.",
            error={
                "code": "TOOL_EXECUTION_FAILED",
                "details": str(error),
            },
            request_id=request_id,
            execution_ms=execution_ms,
        )


__all__ = [
    "run_indicator_tool",
    "serialize_indicator_result",
]
