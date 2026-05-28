"""In-memory scheduled data updater tools for HaruQuantAI.

This module provides safe, bounded, AI-callable tools for creating and managing
local scheduled data updater state. It intentionally avoids exposing unbounded
blocking loops as official AI Tools.

Exported AI Tools:
    - scheduled_data_updater_create: Create updater state and return a state_id.
    - scheduled_data_updater_run_once: Perform one bounded update cycle.
    - scheduled_data_updater_run_cycles: Perform a bounded number of update cycles.
    - scheduled_data_updater_status: Inspect updater state.
    - scheduled_data_updater_stop: Mark updater state as stopped.
    - scheduled_data_updater_delete: Remove updater state from memory.

Internal Helpers:
    - register_scheduled_update_function
    - clear_scheduled_update_functions
    - clear_scheduled_updater_states
    - _coerce_update_result
    - _state_summary
    - _validate_state_id
    - _tool_metadata

Classes:
    - ScheduledUpdaterState

Safety:
    Agents should call bounded tools only. This module does not expose an
    infinite blocking start loop.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Union
from uuid import uuid4

import pandas as pd

from tools.utils import logger

from ._common import Data, _frame_from_payload

TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "data"
TOOL_RISK_LEVEL = "medium"
REQUIRES_APPROVAL = False
READ_ONLY = False
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

MAX_ALLOWED_CYCLES = 100

UpdateFunction = Callable[[Data], Optional[Union[Data, Dict[str, Any]]]]
_UPDATE_FUNCTIONS: Dict[str, UpdateFunction] = {}
_UPDATER_STATES: Dict[str, "ScheduledUpdaterState"] = {}


@dataclass
class ScheduledUpdaterState:
    """Internal in-memory state for a scheduled data updater.

    Args:
        state_id: Unique identifier for the updater state.
        data: Current HaruQuant data object.
        update_func_name: Name of the approved update function.
        interval_sec: Suggested interval between cycles.
        running: Whether the state is marked running.
        created_at: Creation timestamp in seconds.
        updated_at: Last update timestamp in seconds.
        update_count: Number of successful update cycles attempted.
    """

    state_id: str
    data: Data
    update_func_name: str
    interval_sec: int
    running: bool
    created_at: float
    updated_at: float
    update_count: int = 0


def _tool_metadata(tool_name: str) -> Dict[str, Any]:
    """Return static metadata for scheduled updater tools."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "requires_approval": REQUIRES_APPROVAL,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _validation_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    message: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a standard validation error response with scheduler metadata."""
    logger.warning(
        "%s validation failed | request_id=%s | reason=%s",
        tool_name,
        request_id,
        details or message,
    )
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message=message,
        error_code="INVALID_INPUT",
        error_details=details or message,
    )


def _execution_ms(started_at: float) -> float:
    """Return elapsed tool execution time in milliseconds."""
    return round((time.perf_counter() - started_at) * 1000, 3)


def _tool_response(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    status: str,
    message: str,
    data: Any = None,
    error_code: Optional[str] = None,
    error_details: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a standard HaruQuantAI tool response."""
    error = None
    if status == "error":
        error = {
            "code": error_code or "TOOL_EXECUTION_FAILED",
            "details": error_details or message,
        }
    metadata = _tool_metadata(tool_name)
    metadata["request_id"] = request_id
    metadata["execution_ms"] = _execution_ms(started_at)
    return {
        "status": status,
        "message": message,
        "data": data if status == "success" else None,
        "error": error,
        "metadata": metadata,
    }


def _execution_error(
    *,
    tool_name: str,
    started_at: float,
    request_id: Optional[str],
    error: Exception,
) -> Dict[str, Any]:
    """Return a logged TOOL_EXECUTION_FAILED response."""
    logger.exception("%s failed | request_id=%s", tool_name, request_id)
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="error",
        message="Tool execution failed.",
        error_code="TOOL_EXECUTION_FAILED",
        error_details=str(error),
    )


def _validate_state_id(state_id: Any) -> Optional[str]:
    """Return an error message if state_id is invalid."""
    if not isinstance(state_id, str) or not state_id.strip():
        return "state_id must be a non-empty string."
    if state_id not in _UPDATER_STATES:
        return f"Unknown scheduled updater state_id: {state_id}."
    return None


def _state_summary(state: ScheduledUpdaterState) -> Dict[str, Any]:
    """Return a JSON-safe summary for an updater state."""
    frame = state.data.df
    start_at = None
    end_at = None
    if isinstance(frame.index, pd.DatetimeIndex) and not frame.empty:
        start_at = frame.index[0].isoformat()
        end_at = frame.index[-1].isoformat()

    return {
        "state_id": state.state_id,
        "update_func_name": state.update_func_name,
        "interval_sec": state.interval_sec,
        "running": state.running,
        "rows": int(len(frame)),
        "columns": [str(column) for column in frame.columns],
        "start_at": start_at,
        "end_at": end_at,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "update_count": state.update_count,
    }


def _coerce_scheduler_data(data: Union[Data, Dict[str, Any]]) -> Data:
    """Coerce scheduler payloads and use timestamp columns as indexes."""
    data_obj = _frame_from_payload(data)
    frame = data_obj.df.copy()
    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="raise")
        frame = frame.set_index("timestamp").sort_index()
    return Data(
        df=frame,
        symbol=data_obj.symbol,
        timeframe=data_obj.timeframe,
        metadata=data_obj.metadata,
    )


def _coerce_update_result(
    result: Optional[Union[Data, Dict[str, Any]]],
) -> Optional[Data]:
    """Coerce an updater result into a Data object or None."""
    if result is None:
        return None
    return _coerce_scheduler_data(result)


def register_scheduled_update_function(
    name: str,
    update_func: UpdateFunction,
    *,
    replace: bool = False,
) -> None:
    """Register an approved update function for scheduled updater tools.

    Args:
        name: Stable function name agents may reference.
        update_func: Callable receiving the current Data object and returning
            new Data, a data payload, or None.
        replace: Whether to replace an existing registration.

    Raises:
        ValueError: If name is invalid or already exists.
        TypeError: If update_func is not callable.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("update function name must be a non-empty string.")
    if not callable(update_func):
        raise TypeError("update_func must be callable.")
    normalized = name.strip()
    if normalized in _UPDATE_FUNCTIONS and not replace:
        raise ValueError(f"update function already registered: {normalized}")
    _UPDATE_FUNCTIONS[normalized] = update_func


def clear_scheduled_update_functions() -> None:
    """Clear all registered update functions.

    This helper is intended for tests and controlled local setup.
    """
    _UPDATE_FUNCTIONS.clear()


def clear_scheduled_updater_states() -> None:
    """Clear all in-memory updater states.

    This helper is intended for tests and controlled local setup.
    """
    _UPDATER_STATES.clear()


def scheduled_data_updater_create(
    data: Optional[Union[Data, Dict[str, Any]]],
    update_func_name: str,
    interval_sec: int = 60,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create scheduled updater state and return a JSON-safe state_id.

    Use this tool when an agent needs to initialize an in-memory updater for
    repeated local data refreshes. The updater function must already be
    registered with `register_scheduled_update_function`.

    Args:
        data: Initial data object or JSON-safe payload.
        update_func_name: Name of a registered approved update function.
        interval_sec: Suggested interval between update cycles. Must be >= 1.
        request_id: Optional workflow/request ID used for traceable logs and
            tool metadata.

    Returns:
        Dict[str, Any]: Standard tool response with a JSON-safe state summary.

    Error Cases:
        INVALID_INPUT: data, update function name, or interval is invalid.
        TOOL_EXECUTION_FAILED: An unexpected state creation failure occurs.

    Side Effects:
        Creates in-memory updater state. Does not write files, modify a
        database, use network access directly, or place trades.
    """
    tool_name = "scheduled_data_updater_create"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | update_func_name=%s",
        tool_name,
        request_id,
        update_func_name,
    )

    if data is None:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="data argument is required.",
        )
    if not isinstance(update_func_name, str) or not update_func_name.strip():
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="update_func_name must be a non-empty string.",
        )
    update_name = update_func_name.strip()
    if update_name not in _UPDATE_FUNCTIONS:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=f"update_func_name is not registered: {update_name}.",
        )
    if (
        not isinstance(interval_sec, int)
        or isinstance(interval_sec, bool)
        or interval_sec < 1
    ):
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="interval_sec must be an integer greater than or equal to 1.",
        )

    try:
        data_obj = _coerce_scheduler_data(data)
        now = time.time()
        state_id = f"updater_{uuid4().hex}"
        state = ScheduledUpdaterState(
            state_id=state_id,
            data=data_obj,
            update_func_name=update_name,
            interval_sec=interval_sec,
            running=False,
            created_at=now,
            updated_at=now,
        )
        _UPDATER_STATES[state_id] = state

        logger.info(
            "%s completed successfully | request_id=%s | state_id=%s",
            tool_name,
            request_id,
            state_id,
        )
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Scheduled data updater state created successfully.",
            data=_state_summary(state),
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def scheduled_data_updater_run_once(
    state_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform one scheduled data update cycle.

    Use this tool when an agent needs to run a single refresh cycle against an
    existing updater state.

    Args:
        state_id: State identifier returned by `scheduled_data_updater_create`.
        request_id: Optional workflow/request ID used for traceable logs and
            tool metadata.

    Returns:
        Dict[str, Any]: Standard tool response with new row counts and state
        summary.

    Error Cases:
        INVALID_INPUT: state_id is invalid or unknown.
        TOOL_EXECUTION_FAILED: The registered update function fails.

    Side Effects:
        Mutates in-memory updater state only.
    """
    tool_name = "scheduled_data_updater_run_once"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | state_id=%s", tool_name, request_id, state_id
    )

    state_error = _validate_state_id(state_id)
    if state_error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=state_error,
        )

    try:
        state = _UPDATER_STATES[state_id]
        update_func = _UPDATE_FUNCTIONS[state.update_func_name]

        previous_frame = state.data.df
        previous_len = len(previous_frame)
        new_data_obj = _coerce_update_result(update_func(state.data))

        if new_data_obj is not None and not new_data_obj.df.empty:
            combined = pd.concat([previous_frame, new_data_obj.df])
            combined = combined[~combined.index.duplicated(keep="last")].sort_index()
            state.data = Data(
                df=combined,
                symbol=state.data.symbol,
                timeframe=state.data.timeframe,
                metadata=state.data.metadata,
            )

        state.updated_at = time.time()
        state.update_count += 1
        current_len = len(state.data.df)
        new_rows = max(0, current_len - previous_len)

        payload = {
            "new_rows": int(new_rows),
            "total_rows": int(current_len),
            "state": _state_summary(state),
        }
        logger.info(
            "%s completed successfully | request_id=%s | state_id=%s | new_rows=%s",
            tool_name,
            request_id,
            state_id,
            new_rows,
        )
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Scheduled data update cycle completed successfully.",
            data=payload,
        )
    except Exception as error:
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def scheduled_data_updater_run_cycles(
    state_id: str,
    cycles: int = 1,
    sleep_between_cycles: Any = False,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform a bounded number of scheduled data update cycles.

    Use this tool instead of an unbounded blocking scheduler loop. It runs at
    most `MAX_ALLOWED_CYCLES` cycles and then returns a standard response.

    Args:
        state_id: State identifier returned by `scheduled_data_updater_create`.
        cycles: Number of update cycles to run. Must be 1 to MAX_ALLOWED_CYCLES.
        sleep_between_cycles: Whether to sleep `interval_sec` between cycles.
            Defaults to False to avoid unnecessary tool blocking.
        request_id: Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with cycle results.

    Side Effects:
        Mutates in-memory updater state only.
    """
    tool_name = "scheduled_data_updater_run_cycles"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | state_id=%s | cycles=%s",
        tool_name,
        request_id,
        state_id,
        cycles,
    )

    state_error = _validate_state_id(state_id)
    if state_error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=state_error,
        )
    if (
        not isinstance(cycles, int)
        or isinstance(cycles, bool)
        or cycles < 1
        or cycles > MAX_ALLOWED_CYCLES
    ):
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=f"cycles must be an integer between 1 and {MAX_ALLOWED_CYCLES}.",
        )
    if not isinstance(sleep_between_cycles, bool):
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details="sleep_between_cycles must be a boolean.",
        )

    try:
        state = _UPDATER_STATES[state_id]
        state.running = True
        cycle_results: list[Dict[str, Any]] = []

        for cycle_number in range(1, cycles + 1):
            result = scheduled_data_updater_run_once(state_id, request_id=request_id)
            if result.get("status") != "success":
                state.running = False
                return result
            cycle_data = result.get("data") or {}
            cycle_results.append(
                {
                    "cycle": cycle_number,
                    "new_rows": int(cycle_data.get("new_rows", 0)),
                    "total_rows": int(cycle_data.get("total_rows", len(state.data.df))),
                }
            )
            if sleep_between_cycles and cycle_number < cycles:
                time.sleep(state.interval_sec)

        state.running = False
        payload = {
            "cycles_completed": cycles,
            "cycle_results": cycle_results,
            "state": _state_summary(state),
        }

        logger.info(
            "%s completed successfully | request_id=%s | state_id=%s | cycles=%s",
            tool_name,
            request_id,
            state_id,
            cycles,
        )
        return _tool_response(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            status="success",
            message="Scheduled data update cycles completed successfully.",
            data=payload,
        )
    except Exception as error:
        if state_id in _UPDATER_STATES:
            _UPDATER_STATES[state_id].running = False
        return _execution_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            error=error,
        )


def scheduled_data_updater_status(
    state_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Inspect updater state without returning raw DataFrames or callables.

    Args:
        state_id: State identifier returned by `scheduled_data_updater_create`.
        request_id: Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with JSON-safe state summary.
    """
    tool_name = "scheduled_data_updater_status"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | state_id=%s", tool_name, request_id, state_id
    )

    state_error = _validate_state_id(state_id)
    if state_error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=state_error,
        )

    state = _UPDATER_STATES[state_id]
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="success",
        message="Scheduled data updater status retrieved successfully.",
        data=_state_summary(state),
    )


def scheduled_data_updater_stop(
    state_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark an updater state as stopped.

    Args:
        state_id: State identifier returned by `scheduled_data_updater_create`.
        request_id: Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response confirming stopped state.
    """
    tool_name = "scheduled_data_updater_stop"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | state_id=%s", tool_name, request_id, state_id
    )

    state_error = _validate_state_id(state_id)
    if state_error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=state_error,
        )

    state = _UPDATER_STATES[state_id]
    state.running = False
    state.updated_at = time.time()

    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="success",
        message="Scheduled data updater stopped successfully.",
        data=_state_summary(state),
    )


def scheduled_data_updater_delete(
    state_id: str,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Delete an updater state from memory.

    Args:
        state_id: State identifier returned by `scheduled_data_updater_create`.
        request_id: Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response confirming deletion.
    """
    tool_name = "scheduled_data_updater_delete"
    started_at = time.perf_counter()
    logger.info(
        "%s called | request_id=%s | state_id=%s", tool_name, request_id, state_id
    )

    state_error = _validate_state_id(state_id)
    if state_error:
        return _validation_error(
            tool_name=tool_name,
            started_at=started_at,
            request_id=request_id,
            message="Invalid input.",
            details=state_error,
        )

    del _UPDATER_STATES[state_id]
    return _tool_response(
        tool_name=tool_name,
        started_at=started_at,
        request_id=request_id,
        status="success",
        message="Scheduled data updater state deleted successfully.",
        data={"state_id": state_id, "deleted": True},
    )


# Backward-compatible alias. The old scheduler exposed an unsafe blocking
# function named scheduled_data_updater_update. Keep a safe one-cycle alias.
scheduled_data_updater_update = scheduled_data_updater_run_once


__all__ = [
    "clear_scheduled_update_functions",
    "clear_scheduled_updater_states",
    "register_scheduled_update_function",
    "scheduled_data_updater_create",
    "scheduled_data_updater_delete",
    "scheduled_data_updater_run_cycles",
    "scheduled_data_updater_run_once",
    "scheduled_data_updater_status",
    "scheduled_data_updater_stop",
    "scheduled_data_updater_update",
]
