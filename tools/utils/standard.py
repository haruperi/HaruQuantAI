"""Standard AI-tool response helpers for HaruQuantAI.

This module contains compact shared helpers for building official tool
responses, serializing tool payloads, and executing tool boundary logic. It is
a utility module, not an agent-callable tool module.

Classes:
    ToolStandardSpec: Generic metadata container for standard tool responses.
    ToolSpec: Lightweight metadata container used by calculation tools.

Functions:
    standard_tool_response: Build a schema-compliant response from full metadata.
    build_tool_response: Build a schema-compliant response from lightweight metadata.
    run_indicator_tool: Execute indicator calculations with standard boundaries.
    execute_tool_boundary: Execute strategy logic with standard boundaries.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd

from tools.utils.logger import logger

ToolStatus = Literal["success", "error"]
ToolResponse = dict[str, Any]

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "strategy"
TOOL_RISK_LEVEL_LOW = "low"
TOOL_RISK_LEVEL_MEDIUM = "medium"

READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


@dataclass(frozen=True)
class ToolStandardSpec:
    """Metadata describing one standardized HaruQuantAI tool."""

    tool_name: str
    tool_version: str
    tool_category: str
    tool_risk_level: str
    requires_approval: bool
    read_only: bool
    writes_file: bool
    modifies_database: bool
    places_trade: bool
    requires_network: bool


@dataclass(frozen=True)
class ToolSpec:
    """Lightweight metadata used by HaruQuant AI tool responses.

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
    tool_version: str = TOOL_VERSION
    tool_risk_level: str = TOOL_RISK_LEVEL_LOW
    read_only: bool = READ_ONLY
    writes_file: bool = WRITES_FILE
    modifies_database: bool = MODIFIES_DATABASE
    places_trade: bool = PLACES_TRADE
    requires_network: bool = REQUIRES_NETWORK
    requires_approval: bool = False


def standard_tool_response(
    spec: ToolStandardSpec,
    status: ToolStatus,
    message: str,
    *,
    data: Any = None,
    error: dict[str, str] | None = None,
    request_id: str | None = None,
    execution_ms: float = 0.0,
) -> ToolResponse:
    """Build a standard HaruQuantAI tool response dictionary.

    Args:
        spec: Tool metadata and side-effect declarations.
        status: Tool result status.
        message: Human-readable outcome message.
        data: Success payload. Ignored for error responses.
        error: Error payload with deterministic code and details.
        request_id: Optional request/workflow trace ID.
        execution_ms: Elapsed execution time in milliseconds.

    Returns:
        ToolResponse: Standard response dictionary.

    Raises:
        ValueError: If status or error payload shape is invalid.
    """
    if status not in {"success", "error"}:
        raise ValueError("status must be 'success' or 'error'.")

    if status == "error":
        if not error or not error.get("code") or not error.get("details"):
            raise ValueError("error responses require code and details.")
        response_error: dict[str, str] | None = {
            "code": str(error["code"]),
            "details": str(error["details"]),
        }
        response_data = None
    else:
        response_error = None
        response_data = data

    return {
        "status": status,
        "message": message,
        "data": response_data,
        "error": response_error,
        "metadata": {
            "tool_name": spec.tool_name,
            "tool_version": spec.tool_version,
            "tool_category": spec.tool_category,
            "tool_risk_level": spec.tool_risk_level,
            "request_id": request_id,
            "execution_ms": float(execution_ms),
            "read_only": spec.read_only,
            "writes_file": spec.writes_file,
            "modifies_database": spec.modifies_database,
            "places_trade": spec.places_trade,
            "requires_network": spec.requires_network,
        },
    }


def _json_safe(value: Any) -> Any:
    """Convert pandas and numpy scalar values into JSON-safe Python values."""
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
    """Serialize common tool outputs into JSON-safe payloads."""
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
) -> ToolResponse:
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
) -> ToolResponse:
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
        elapsed_ms = execution_ms(started_at)
        logger.info(
            "%s completed | request_id=%s | execution_ms=%s",
            spec.tool_name,
            request_id,
            elapsed_ms,
        )
        return build_tool_response(
            spec,
            status="success",
            message=success_message or "Indicator calculated successfully.",
            data=result,
            error=None,
            request_id=request_id,
            execution_ms=elapsed_ms,
        )
    except (TypeError, ValueError, LookupError) as exc:
        elapsed_ms = execution_ms(started_at)
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
            execution_ms=elapsed_ms,
        )
    except Exception as exc:  # pragma: no cover - safety boundary
        elapsed_ms = execution_ms(started_at)
        logger.exception(
            "%s failed | request_id=%s | execution_ms=%s",
            spec.tool_name,
            request_id,
            elapsed_ms,
        )
        return build_tool_response(
            spec,
            status="error",
            message="Tool execution failed.",
            data=None,
            error={"code": "TOOL_EXECUTION_FAILED", "details": str(exc)},
            request_id=request_id,
            execution_ms=elapsed_ms,
        )


def started_timer() -> float:
    """Return a high-resolution timer value for execution timing."""
    return time.perf_counter()


def execution_ms(started_at: float) -> float:
    """Return elapsed milliseconds rounded for stable metadata."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def metadata(
    *,
    tool_name: str,
    request_id: str | None,
    started_at: float,
    tool_version: str = TOOL_VERSION,
    tool_category: str = TOOL_CATEGORY,
    tool_risk_level: str = TOOL_RISK_LEVEL_LOW,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    modifies_database: bool = MODIFIES_DATABASE,
    places_trade: bool = PLACES_TRADE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Build standard HaruQuant AI tool metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": tool_version,
        "tool_category": tool_category,
        "tool_risk_level": tool_risk_level,
        "request_id": request_id,
        "execution_ms": execution_ms(started_at),
        "read_only": read_only,
        "writes_file": writes_file,
        "modifies_database": modifies_database,
        "places_trade": places_trade,
        "requires_network": requires_network,
    }


def success_response(
    *,
    tool_name: str,
    request_id: str | None,
    started_at: float,
    message: str,
    data: Any,
    tool_risk_level: str = TOOL_RISK_LEVEL_LOW,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Return a standard successful AI tool response."""
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": metadata(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        ),
    }


def error_response(
    *,
    tool_name: str,
    request_id: str | None,
    started_at: float,
    message: str,
    code: str,
    details: str,
    tool_risk_level: str = TOOL_RISK_LEVEL_LOW,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Return a standard failed AI tool response."""
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": metadata(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        ),
    }


def execute_tool_boundary(
    *,
    tool_name: str,
    request_id: str | None,
    operation: Callable[[], Any],
    success_message: str,
    tool_risk_level: str = TOOL_RISK_LEVEL_LOW,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
) -> ToolResponse:
    """Execute strategy tool logic with standard logging and error mapping.

    Args:
        tool_name: Public AI tool name.
        request_id: Optional trace identifier propagated by an agent workflow.
        operation: Callable containing validated business logic.
        success_message: Message returned on success.
        tool_risk_level: Standard HaruQuant risk level.
        read_only: Whether the operation is read-only.
        writes_file: Whether the operation writes files.

    Returns:
        Standard HaruQuant AI tool response dictionary.
    """
    started_at = started_timer()
    logger.info("%s called | request_id=%s", tool_name, request_id)
    try:
        data = operation()
        logger.info("%s completed | request_id=%s", tool_name, request_id)
        return success_response(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message=success_message,
            data=data,
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        )
    except ValueError as exc:
        logger.warning(
            "%s validation failed | request_id=%s | error=%s",
            tool_name,
            request_id,
            exc,
        )
        return error_response(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message="Invalid strategy tool input.",
            code="INVALID_INPUT",
            details=str(exc),
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        )
    except LookupError as exc:
        logger.warning(
            "%s lookup failed | request_id=%s | error=%s",
            tool_name,
            request_id,
            exc,
        )
        return error_response(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message="Strategy resource was not found.",
            code="DATA_NOT_FOUND",
            details=str(exc),
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        )
    except Exception as exc:  # pragma: no cover - tool boundary safety net
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return error_response(
            tool_name=tool_name,
            request_id=request_id,
            started_at=started_at,
            message="Strategy tool execution failed.",
            code="TOOL_EXECUTION_FAILED",
            details=str(exc),
            tool_risk_level=tool_risk_level,
            read_only=read_only,
            writes_file=writes_file,
        )


__all__ = [
    "MODIFIES_DATABASE",
    "PLACES_TRADE",
    "READ_ONLY",
    "REQUIRES_NETWORK",
    "TOOL_CATEGORY",
    "TOOL_RISK_LEVEL_LOW",
    "TOOL_RISK_LEVEL_MEDIUM",
    "TOOL_VERSION",
    "ToolSpec",
    "ToolResponse",
    "ToolStandardSpec",
    "ToolStatus",
    "WRITES_FILE",
    "build_tool_response",
    "dataframe_to_records",
    "error_response",
    "execute_tool_boundary",
    "execution_ms",
    "metadata",
    "run_indicator_tool",
    "serialize_payload",
    "series_to_list",
    "standard_tool_response",
    "started_timer",
    "success_response",
]
