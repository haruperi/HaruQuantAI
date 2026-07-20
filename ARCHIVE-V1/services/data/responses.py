"""Build standard HaruQuant data-tool response envelopes.

Purpose:
    Provide the shared tool-envelope helpers used by the data-domain AI tools
    and the CSV/Parquet/labeling modules. These helpers previously lived in
    ``app.services.data._common`` and were extracted so that legacy module can
    be retired.

Classes and functions:
    _execution_ms: Return elapsed tool execution time in milliseconds.
    _data_tool_spec: Build a standard metadata specification for a data tool.
    _data_tool_response: Build a standard HaruQuant data tool response envelope.
    _data_tool_validation_error: Return a standardized invalid-input response.
    _data_tool_execution_error: Return a standardized execution-failure response.
"""

from __future__ import annotations

import time
from typing import Any, cast

from app.services.utils.logger import logger
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False


def _execution_ms(started_at: float) -> float:
    """Description.
        Return elapsed tool execution time in milliseconds.
    
    Args:
        started_at: float.
    
    Returns:
        float.
    """
    logger.debug("Calculating tool execution time in milliseconds.")
    return round((time.perf_counter() - started_at) * 1000, 3)


def _data_tool_spec(
    tool_name: str,
    *,
    tool_risk_level: str = TOOL_RISK_LEVEL,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> ToolStandardSpec:
    """Description.
        Build a standard metadata specification for a data-domain AI tool.
    
    Args:
        tool_name: str.
        tool_risk_level: str.
        read_only: bool.
        writes_file: bool.
        requires_network: bool.
    
    Returns:
        ToolStandardSpec.
    """
    logger.debug(f"Building tool metadata specification for: '{tool_name}'")
    return ToolStandardSpec(
        tool_name=tool_name,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=tool_risk_level,
        requires_approval=REQUIRES_APPROVAL,
        read_only=read_only,
        writes_file=writes_file,
        modifies_database=MODIFIES_DATABASE,
        places_trade=PLACES_TRADE,
        requires_network=requires_network,
    )


def _data_tool_response(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    status: str,
    message: str,
    data: Any = None,
    error_code: str | None = None,
    error_details: str | None = None,
    tool_risk_level: str = TOOL_RISK_LEVEL,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Description.
        Build a standard HaruQuant data tool response envelope.
    
    Args:
        tool_name: str.
        started_at: float.
        request_id: str | None.
        status: str.
        message: str.
        data: Any.
        error_code: str | None.
        error_details: str | None.
        tool_risk_level: str.
        read_only: bool.
        writes_file: bool.
        requires_network: bool.
    
    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Building tool response envelope for '{tool_name}' "
        f"(status={status}, request_id={request_id})."
    )
    error = None
    if status == "error":
        error = {
            "code": error_code or "TOOL_EXECUTION_FAILED",
            "details": error_details or message,
        }
        data = None

    return cast(
        dict[str, Any],
        standard_tool_response(
            spec=_data_tool_spec(
                tool_name,
                tool_risk_level=tool_risk_level,
                read_only=read_only,
                writes_file=writes_file,
                requires_network=requires_network,
            ),
            status=status,
            message=message,
            data=data,
            error=error,
            request_id=request_id,
            execution_ms=_execution_ms(started_at),
        ),
    )


def _data_tool_validation_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    message: str,
    details: str | None = None,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Description.
        Return a standardized invalid-input response for a data tool.
    
    Args:
        tool_name: str.
        started_at: float.
        request_id: str | None.
        message: str.
        details: str | None.
        read_only: bool.
        writes_file: bool.
        requires_network: bool.
    
    Returns:
        dict[str, Any].
    """
    logger.warning(
        "{} failed validation | request_id={} | reason={}",
        tool_name,
        request_id,
        details or message,
    )
    return _data_tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Invalid input.",
        error_code="INVALID_INPUT",
        error_details=details or message,
        read_only=read_only,
        writes_file=writes_file,
        requires_network=requires_network,
    )


def _data_tool_execution_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: str | None,
    error: Exception,
    read_only: bool = READ_ONLY,
    writes_file: bool = WRITES_FILE,
    requires_network: bool = REQUIRES_NETWORK,
) -> dict[str, Any]:
    """Description.
        Return a standardized execution-failure response for a data tool.
    
    Args:
        tool_name: str.
        started_at: float.
        request_id: str | None.
        error: Exception.
        read_only: bool.
        writes_file: bool.
        requires_network: bool.
    
    Returns:
        dict[str, Any].
    """
    logger.exception("{} failed | request_id={}", tool_name, request_id)
    return _data_tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
        read_only=read_only,
        writes_file=writes_file,
        requires_network=requires_network,
    )
