"""Standard AI-tool response helpers for HaruQuantAI.

This module contains compact shared helpers for building official tool
responses. It is a utility module, not an agent-callable tool module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ToolStatus = Literal["success", "error"]
ToolResponse = dict[str, Any]


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


__all__ = [
    "ToolResponse",
    "ToolStandardSpec",
    "ToolStatus",
    "standard_tool_response",
]
