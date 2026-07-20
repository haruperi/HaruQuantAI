"""common.py - Provide shared analytics result envelopes, data cleaning helpers, and exposure primitives.

This module contains foundational utilities for all analytics tools, including the standard
result envelope builder, data validation helpers, and core trade classification logic.

Classes:
    None.

Functions:
    analytics_tool_result: Build the standard result envelope for analytics tool functions.
    analytics_business_payload: Return business inputs after removing standard control fields.
    _has_col: Check if a column exists in a DataFrame.
    get_closed_trades: Filter for closed trades (AI Tool).
    _get_closed_trades_impl: Core logic for filtering closed trades.
    _to_1d_float_array: Normalize numeric inputs to a finite float NumPy array.
    _to_datetime_series: Convert a timestamp series safely, supporting datetime values and Unix seconds.
    classify_trades: Classify trades into wins, losses, and breakevens (AI Tool).
    _classify_trades_impl: Core logic for trade classification.
    avg_loss: Mean loss of losing trades (AI Tool).
    _avg_loss_impl: Core logic for calculating average loss.
    get_r_multiples: Get R-multiples for trades (AI Tool).
    _get_r_multiples_impl: Core logic for calculating R-multiples.
    _exposure_kernel: Accumulates size changes and returns the maximum peak reached.
    _time_weighted_kernel: Calculates time-weighted average of a step-function.
    _exposure_curve_kernel: Generates the step-function values for a given series of events.
    max_gross_size_held: Maximum absolute total size held across all positions (AI Tool).
    _max_gross_size_held_impl: Core logic for calculating gross exposure.
    _merge_intervals_kernel: Merge sorted interval start and end arrays into non-overlapping ranges.
    _merge_intervals: Merge overlapping trade intervals.
    time_in_market_duration: Calculate total duration where at least one position was open (AI Tool).
    _time_in_market_duration_impl: Core logic for calculating time in market duration.
    percent_time_in_market: Calculate percent of the trading period spent in the market (AI Tool).
    _percent_time_in_market_impl: Core logic for calculating percent time in market.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from app.services.utils.logger import logger
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

EPSILON = 1e-4
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "analytics"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False
CREATES = False
READS = True
UPDATES = False
DELETES = False
TRADES = False


def analytics_tool_result(
    tool_name: str,
    *,
    data: dict[str, Any] | None = None,
    status: str = "success",
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = True,
    approval_required: str = "none",
    risk_level: str = "low",
    side_effects: list[str] | None = None,
) -> dict[str, Any]:
    """Build the standard result envelope for analytics tool functions.

    Args:
        tool_name: The name of the tool being executed.
        data: The actual analytics data to return.
        status: The status of the execution (success/error).
        errors: A list of error messages.
        warnings: A list of warning messages.
        request_id: Unique ID for the request.
        agent_name: Name of the agent calling the tool.
        environment: Execution environment (e.g., development, production).
        dry_run: Whether this was a dry run.
        approval_required: Level of approval required for this action.
        risk_level: Risk level of the operation.
        side_effects: List of side effects caused by the operation.

    Returns:
        A dictionary following the HaruQuant standard tool result format.
    """
    _ = agent_name, environment, dry_run, side_effects, approval_required, uuid4
    error_list = errors or []
    normalized_status = "success" if status == "success" and not error_list else "error"
    return standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="analytics",
            tool_risk_level=risk_level,
            read_only=True,
        ),
        status=normalized_status,
        message=(
            "Analytics tool executed successfully."
            if normalized_status == "success"
            else "Analytics tool execution failed."
        ),
        data=data,
        error=None
        if normalized_status == "success"
        else {
            "code": "TOOL_EXECUTION_FAILED",
            "details": "; ".join(error_list) or "Analytics tool failed.",
        },
        request_id=request_id,
        execution_ms=0.0,
    )


def analytics_business_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return business inputs after removing standard control fields.

    Args:
        payload: The full tool input payload.

    Returns:
        A dictionary containing only the business-relevant inputs.
    """
    control_fields = {"request_id", "agent_name", "environment", "dry_run"}
    return {key: value for key, value in payload.items() if key not in control_fields}


try:
    from numba import njit
except ImportError:

    def njit(*args, **kwargs):
        """Return a no-op decorator when numba is unavailable."""

        def decorator(f):
            """Return the original function unchanged."""
            return f

        return decorator


# =========================================================================
# Data Access & Column Primitives
# =========================================================================


def _has_col(df: pd.DataFrame, col: str) -> bool:
    """Check if a column exists in a DataFrame.

    Args:
        df: The DataFrame to check.
        col: The column name to search for.

    Returns:
        True if the column exists, False otherwise.
    """
    return col in df.columns


def _get_closed_trades_impl(trades: pd.DataFrame) -> pd.DataFrame:
    """Core logic for filtering closed trades.

    Args:
        trades: DataFrame containing trade records.

    Returns:
        A DataFrame containing only trades that are considered closed.
    """
    if trades.empty:
        return trades.copy()

    closed = trades.copy()
    if "exit_reason" in closed.columns:
        open_reasons = {"END_OF_DATA", "OPEN"}
        closed = closed[~closed["exit_reason"].isin(open_reasons)]

    if "close_time" in closed.columns:
        closed = closed[closed["close_time"].notna()]

    return closed


def _to_1d_float_array(values: Any) -> np.ndarray:
    """Normalize numeric inputs to a finite float NumPy array.

    Args:
        values: Input data (list, Series, array, etc.).

    Returns:
        A 1D NumPy array of finite floats.
    """
    if isinstance(values, pd.Series):
        array = values.astype(float).to_numpy()
    else:
        array = np.asarray(values, dtype=float)

    if array.ndim == 0:
        array = array.reshape(1)

    return array[np.isfinite(array)]


def _to_datetime_series(series: pd.Series) -> pd.Series:
    """Convert a timestamp series safely, supporting datetime values and Unix seconds.

    Args:
        series: A pandas Series containing timestamp data.

    Returns:
        A pandas Series of datetime64[ns] values.
    """
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="s")
    return pd.to_datetime(series)


# =========================================================================
# Core Trade Statistics (The Analytics Foundation)
# =========================================================================


def _classify_trades_impl(
    trades: pd.DataFrame, pnl_col: str = "profit_loss"
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Classify trades into wins, losses, and breakevens using a consistent threshold.

    Args:
        trades: DataFrame of trade records.
        pnl_col: Name of the column containing Profit/Loss values.

    Returns:
        A tuple of (wins_df, losses_df, breakevens_df).
    """
    if trades.empty or not _has_col(trades, pnl_col):
        empty = pd.DataFrame(columns=trades.columns)
        return empty, empty, empty

    pnl = trades[pnl_col]
    wins = trades[pnl > EPSILON]
    losses = trades[pnl < -EPSILON]
    breakevens = trades[pnl.abs() <= EPSILON]
    return wins, losses, breakevens


def _avg_loss_impl(trades: pd.DataFrame) -> float:
    """Core logic for calculating average loss of losing trades.

    Args:
        trades: DataFrame of trade records.

    Returns:
        The mean loss of losing trades (as a float). Returns 0.0 if no losses.
    """
    if trades.empty or not _has_col(trades, "profit_loss"):
        return 0.0
    _, losses, _ = _classify_trades_impl(_get_closed_trades_impl(trades))
    return float(losses["profit_loss"].mean()) if not losses.empty else 0.0


def _get_r_multiples_impl(trades: pd.DataFrame, closed_only: bool = True) -> pd.Series:
    """Core logic for calculating R-multiples for trades.

    Args:
        trades: DataFrame of trade records.
        closed_only: If True, only closed trades are considered.

    Returns:
        A pandas Series of R-multiples.
    """
    data = _get_closed_trades_impl(trades) if closed_only else trades
    if data.empty or not _has_col(data, "profit_loss"):
        return pd.Series(dtype=float)

    # 1. Official Risk Amount (Monetary)
    for col in ["initial_risk_amount", "initial_risk"]:
        if col in data.columns:
            risk = data[col].abs().replace(0, np.nan)
            r = data["profit_loss"] / risk
            r = r.replace([np.inf, -np.inf], np.nan).dropna()
            if not r.empty:
                return r

    # 2. Fallback: Use Average Loss as proxy for 1R baseline
    avg_l = abs(_avg_loss_impl(data))
    if avg_l > EPSILON:
        r = data["profit_loss"] / avg_l
        return r.replace([np.inf, -np.inf], np.nan).dropna()

    return pd.Series(dtype=float)


# =========================================================================
# Exposure & Market Presence Primitives (Shared)
# =========================================================================


@njit(cache=True)
def _exposure_kernel(sizes: np.ndarray) -> float:
    """Accumulates size changes and returns the maximum peak reached.

    Args:
        sizes: Array of size changes at each event.

    Returns:
        The maximum peak exposure reached.
    """
    current = 0.0
    peak = 0.0
    for i in range(len(sizes)):
        current += sizes[i]
        # Precision correction
        if abs(current) < 1e-9:
            current = 0.0
        peak = max(peak, current)
    return peak


@njit(cache=True)
def _time_weighted_kernel(times: np.ndarray, sizes: np.ndarray) -> float:
    """Calculates time-weighted average of a step-function (area under curve / duration).

    Args:
        times: Array of timestamps (in integer representation).
        sizes: Array of size changes at each timestamp.

    Returns:
        The time-weighted average exposure.
    """
    if len(times) < 2:
        return 0.0

    total_area = 0.0
    current_size = 0.0

    for i in range(len(times) - 1):
        current_size += sizes[i]
        # Precision correction
        if abs(current_size) < 1e-9:
            current_size = 0.0

        duration = times[i + 1] - times[i]
        if duration > 0:
            total_area += current_size * duration

    total_duration = times[-1] - times[0]
    if total_duration <= 0:
        return 0.0

    return total_area / total_duration


@njit(cache=True)
def _exposure_curve_kernel(times: np.ndarray, sizes: np.ndarray) -> np.ndarray:
    """Generates the step-function values for a given series of events.

    Args:
        times: Array of timestamps.
        sizes: Array of size changes.

    Returns:
        An array containing the cumulative exposure at each timestamp.
    """
    n = len(times)
    curve = np.zeros(n, dtype=np.float64)
    current = 0.0
    for i in range(n):
        current += sizes[i]
        if abs(current) < 1e-9:
            current = 0.0
        curve[i] = current
    return curve


def _max_gross_size_held_impl(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> float:
    """Core logic for calculating maximum absolute total size held (Gross Exposure).

    Args:
        trades: DataFrame of trade records.
        end_time: The end of the trading period for open trades.

    Returns:
        The maximum gross exposure reached.
    """
    if trades.empty:
        return 0.0

    # Identify size column
    size_col = None
    for col in ["size", "quantity", "volume"]:
        if col in trades.columns:
            size_col = col
            break

    if not size_col:
        return 0.0

    # For gross exposure, use absolute size
    open_times = trades["open_time"].values
    close_times = (
        trades["close_time"].fillna(end_time or trades["open_time"].max()).values
    )
    sizes = trades[size_col].abs().values

    event_times = np.concatenate([open_times, close_times])
    event_sizes = np.concatenate([sizes, -sizes])

    # Secondary sort by sizes descending to handle simultaneous open/close events correctly
    idx = np.lexsort((-event_sizes, event_times))
    sorted_sizes = event_sizes[idx]

    return float(_exposure_kernel(sorted_sizes))


@njit(cache=True)
def _merge_intervals_kernel(starts: np.ndarray, ends: np.ndarray) -> np.ndarray:
    """Merge sorted interval start and end arrays into non-overlapping ranges.

    Args:
        starts: Sorted array of interval start times.
        ends: Array of interval end times.

    Returns:
        A 2D array of merged [start, end] intervals.
    """
    n = len(starts)
    if n == 0:
        return np.empty((0, 2), dtype=starts.dtype)

    # Pre-allocate worst case
    merged = np.empty((n, 2), dtype=starts.dtype)
    m_ptr = 0

    curr_start = starts[0]
    curr_end = ends[0]

    for i in range(1, n):
        if starts[i] <= curr_end:
            curr_end = max(curr_end, ends[i])
        else:
            merged[m_ptr, 0] = curr_start
            merged[m_ptr, 1] = curr_end
            m_ptr += 1
            curr_start = starts[i]
            curr_end = ends[i]

    merged[m_ptr, 0] = curr_start
    merged[m_ptr, 1] = curr_end
    m_ptr += 1

    return merged[:m_ptr]


def _merge_intervals(
    trades: pd.DataFrame,
    end_time: pd.Timestamp | None = None,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Merge overlapping trade intervals.

    Args:
        trades: DataFrame of trade records.
        end_time: The end of the trading period for open trades.

    Returns:
        A list of merged (start, end) Timestamps.
    """
    if (
        trades.empty
        or "open_time" not in trades.columns
        or "close_time" not in trades.columns
    ):
        return []

    data = trades.copy()
    fallback = end_time if end_time is not None else data["open_time"].max()
    data["close_time"] = data["close_time"].fillna(fallback)

    data = data.dropna(subset=["open_time", "close_time"])
    if data.empty:
        return []

    starts_dt = _to_datetime_series(data["open_time"])
    ends_dt = _to_datetime_series(data["close_time"])

    valid = ends_dt >= starts_dt
    starts_dt = starts_dt[valid]
    ends_dt = ends_dt[valid]

    if starts_dt.empty:
        return []

    idx = np.argsort(starts_dt.values)
    starts = starts_dt.values[idx].astype("datetime64[ns]").view("int64")
    ends = ends_dt.values[idx].astype("datetime64[ns]").view("int64")

    merged_raw = _merge_intervals_kernel(starts, ends)

    return [
        (pd.Timestamp(merged_raw[i, 0]), pd.Timestamp(merged_raw[i, 1]))
        for i in range(len(merged_raw))
    ]


def _time_in_market_duration_impl(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> pd.Timedelta:
    """Core logic for calculating total duration where at least one position was open.

    Args:
        trades: DataFrame of trade records.
        end_time: The end of the trading period.

    Returns:
        The total duration spent in the market as a Timedelta.
    """
    merged_intervals = _merge_intervals(trades, end_time)
    total_duration = pd.Timedelta(0)
    for start, end in merged_intervals:
        total_duration += end - start
    return total_duration


def _percent_time_in_market_impl(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> float:
    """Core logic for calculating percent of the trading period spent in the market.

    Args:
        trades: DataFrame of trade records.
        start_time: Start of the trading period.
        end_time: End of the trading period.

    Returns:
        The percentage of time spent in the market (0-100).
    """
    if len(trades) == 0:
        return 0.0

    t_start = start_time or trades["open_time"].min()
    t_end = end_time or (
        trades["close_time"].max()
        if "close_time" in trades.columns
        else trades["open_time"].max()
    )

    if pd.isna(t_start) or pd.isna(t_end) or t_end <= t_start:
        return 0.0

    total_period = t_end - t_start
    market_time = _time_in_market_duration_impl(trades, end_time)
    ratio = market_time.total_seconds() / total_period.total_seconds()
    return float(min(1.0, ratio) * 100.0)


# =========================================================================
# AI Tool Wrappers (Rule 3)
# =========================================================================


def _get_closed_trades_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
) -> dict[str, Any]:
    """Filter for closed trades (AI Tool).

    Args:
        trades: Trade records as a DataFrame or list of dictionaries.

    Returns:
        A standardized tool result containing the filtered trades.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {
                "status": "error",
                "message": "Invalid trades format. Expected DataFrame or list of dicts.",
            }

        # Core Execution
        result_df = _get_closed_trades_impl(df)

        # Structured Return
        data_payload = result_df.to_dict(orient="records")
        logger.info("Executed get_closed_trades tool successfully.")
        return analytics_tool_result(
            "get_closed_trades", data={"closed_trades": data_payload}
        )

    except Exception as e:
        logger.error(f"Error in get_closed_trades: {e!s}")
        return {"status": "error", "message": str(e)}


def _classify_trades_impl(
    trades: pd.DataFrame | list[dict[str, Any]], pnl_col: str = "profit_loss"
) -> dict[str, Any]:
    """Classify trades into wins, losses, and breakevens (AI Tool).

    Args:
        trades: Trade records as a DataFrame or list of dictionaries.
        pnl_col: Column name for P&L.

    Returns:
        A standardized tool result containing wins, losses, and breakevens.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        # Core Execution
        wins, losses, breakevens = _classify_trades_impl(df, pnl_col)

        # Structured Return
        data = {
            "wins": wins.to_dict(orient="records"),
            "losses": losses.to_dict(orient="records"),
            "breakevens": breakevens.to_dict(orient="records"),
        }
        logger.info("Executed classify_trades tool successfully.")
        return analytics_tool_result("classify_trades", data=data)

    except Exception as e:
        logger.error(f"Error in classify_trades: {e!s}")
        return {"status": "error", "message": str(e)}


def _avg_loss_impl(trades: pd.DataFrame | list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate mean loss of losing trades (AI Tool).

    Args:
        trades: Trade records as a DataFrame or list of dictionaries.

    Returns:
        A standardized tool result containing the average loss.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        # Core Execution
        result = _avg_loss_impl(df)

        # Structured Return
        logger.info("Executed avg_loss tool successfully.")
        return analytics_tool_result("avg_loss", data={"avg_loss": result})

    except Exception as e:
        logger.error(f"Error in avg_loss: {e!s}")
        return {"status": "error", "message": str(e)}


def _get_r_multiples_impl(
    trades: pd.DataFrame | list[dict[str, Any]], closed_only: bool = True
) -> dict[str, Any]:
    """Get R-multiples for trades (AI Tool).

    Args:
        trades: Trade records as a DataFrame or list of dictionaries.
        closed_only: Filter for closed trades first.

    Returns:
        A standardized tool result containing R-multiples.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        # Core Execution
        r_multiples = _get_r_multiples_impl(df, closed_only)

        # Structured Return
        logger.info("Executed get_r_multiples tool successfully.")
        return analytics_tool_result(
            "get_r_multiples", data={"r_multiples": r_multiples.tolist()}
        )

    except Exception as e:
        logger.error(f"Error in get_r_multiples: {e!s}")
        return {"status": "error", "message": str(e)}


def _max_gross_size_held_impl(
    trades: pd.DataFrame | list[dict[str, Any]], end_time: str | None = None
) -> dict[str, Any]:
    """Maximum absolute total size held across all positions (AI Tool).

    Args:
        trades: Trade records.
        end_time: ISO timestamp string for the end of period.

    Returns:
        A standardized tool result containing max gross size.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        e_time = pd.Timestamp(end_time) if end_time else None

        # Core Execution
        result = _max_gross_size_held_impl(df, e_time)

        # Structured Return
        logger.info("Executed max_gross_size_held tool successfully.")
        return analytics_tool_result(
            "max_gross_size_held", data={"max_gross_size": result}
        )

    except Exception as e:
        logger.error(f"Error in max_gross_size_held: {e!s}")
        return {"status": "error", "message": str(e)}


def _time_in_market_duration_impl(
    trades: pd.DataFrame | list[dict[str, Any]], end_time: str | None = None
) -> dict[str, Any]:
    """Calculate total duration where at least one position was open (AI Tool).

    Args:
        trades: Trade records.
        end_time: ISO timestamp string for the end of period.

    Returns:
        A standardized tool result containing the duration in seconds.
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        e_time = pd.Timestamp(end_time) if end_time else None

        # Core Execution
        duration = _time_in_market_duration_impl(df, e_time)

        # Structured Return
        logger.info("Executed time_in_market_duration tool successfully.")
        return analytics_tool_result(
            "time_in_market_duration",
            data={"duration_seconds": duration.total_seconds()},
        )

    except Exception as e:
        logger.error(f"Error in time_in_market_duration: {e!s}")
        return {"status": "error", "message": str(e)}


def _percent_time_in_market_impl(
    trades: pd.DataFrame | list[dict[str, Any]],
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """Calculate percent of the trading period spent in the market (AI Tool).

    Args:
        trades: Trade records.
        start_time: ISO timestamp string for start of period.
        end_time: ISO timestamp string for end of period.

    Returns:
        A standardized tool result containing the percentage (0-100).
    """
    try:
        # Input Validation
        if isinstance(trades, list):
            df = pd.DataFrame(trades)
        elif isinstance(trades, pd.DataFrame):
            df = trades.copy()
        else:
            return {"status": "error", "message": "Invalid trades format."}

        s_time = pd.Timestamp(start_time) if start_time else None
        e_time = pd.Timestamp(end_time) if end_time else None

        # Core Execution
        result = _percent_time_in_market_impl(df, s_time, e_time)

        # Structured Return
        logger.info("Executed percent_time_in_market tool successfully.")
        return analytics_tool_result(
            "percent_time_in_market", data={"percent_time_in_market": result}
        )

    except Exception as e:
        logger.error(f"Error in percent_time_in_market: {e!s}")
        return {"status": "error", "message": str(e)}


def get_closed_trades(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _get_closed_trades_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _get_closed_trades_impl(**kwargs)
        logger.info("Executed get_closed_trades tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "get_closed_trades", data={"get_closed_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def classify_trades(
    trades: pd.DataFrame, pnl_col: str = "profit_loss"
) -> dict[str, Any]:
    """AI Tool wrapper for _classify_trades_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_pnl_col = pnl_col
        if "pnl_col" in ["trades", "open_trades"] and isinstance(
            arg_pnl_col, (list, dict)
        ):
            arg_pnl_col = pd.DataFrame(arg_pnl_col)
        elif "pnl_col" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_pnl_col, list):
            arg_pnl_col = pd.Series(arg_pnl_col)
        kwargs["pnl_col"] = arg_pnl_col

        res = _classify_trades_impl(**kwargs)
        logger.info("Executed classify_trades tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "classify_trades", data={"classify_trades": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def avg_loss(trades: pd.DataFrame) -> dict[str, Any]:
    """AI Tool wrapper for _avg_loss_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        res = _avg_loss_impl(**kwargs)
        logger.info("Executed avg_loss tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result("avg_loss", data={"avg_loss": data_payload})
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def get_r_multiples(trades: pd.DataFrame, closed_only: bool = True) -> dict[str, Any]:
    """AI Tool wrapper for _get_r_multiples_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_closed_only = closed_only
        if "closed_only" in ["trades", "open_trades"] and isinstance(
            arg_closed_only, (list, dict)
        ):
            arg_closed_only = pd.DataFrame(arg_closed_only)
        elif "closed_only" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_closed_only, list):
            arg_closed_only = pd.Series(arg_closed_only)
        kwargs["closed_only"] = arg_closed_only

        res = _get_r_multiples_impl(**kwargs)
        logger.info("Executed get_r_multiples tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "get_r_multiples", data={"get_r_multiples": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def max_gross_size_held(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _max_gross_size_held_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _max_gross_size_held_impl(**kwargs)
        logger.info("Executed max_gross_size_held tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "max_gross_size_held", data={"max_gross_size_held": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def time_in_market_duration(
    trades: pd.DataFrame, end_time: pd.Timestamp | None = None
) -> dict[str, Any]:
    """AI Tool wrapper for _time_in_market_duration_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _time_in_market_duration_impl(**kwargs)
        logger.info("Executed time_in_market_duration tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "time_in_market_duration", data={"time_in_market_duration": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def percent_time_in_market(
    trades: pd.DataFrame,
    start_time: pd.Timestamp | None = None,
    end_time: pd.Timestamp | None = None,
) -> dict[str, Any]:
    """AI Tool wrapper for _percent_time_in_market_impl."""
    try:
        import pandas as pd
        from app.services.utils import logger

        from .common import analytics_tool_result

        kwargs = {}

        arg_trades = trades
        if "trades" in ["trades", "open_trades"] and isinstance(
            arg_trades, (list, dict)
        ):
            arg_trades = pd.DataFrame(arg_trades)
        elif "trades" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_trades, list):
            arg_trades = pd.Series(arg_trades)
        kwargs["trades"] = arg_trades

        arg_start_time = start_time
        if "start_time" in ["trades", "open_trades"] and isinstance(
            arg_start_time, (list, dict)
        ):
            arg_start_time = pd.DataFrame(arg_start_time)
        elif "start_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_start_time, list):
            arg_start_time = pd.Series(arg_start_time)
        kwargs["start_time"] = arg_start_time

        arg_end_time = end_time
        if "end_time" in ["trades", "open_trades"] and isinstance(
            arg_end_time, (list, dict)
        ):
            arg_end_time = pd.DataFrame(arg_end_time)
        elif "end_time" in [
            "returns",
            "rets",
            "returns_in",
            "values",
            "equity_curve",
            "benchmark_equity",
            "benchmark_equity_series",
            "strategy_equity",
            "monthly_returns",
            "values",
            "observed_sharpe",
            "strategy_returns",
            "benchmark_returns",
            "train_scores",
            "test_scores",
            "returns_list",
        ] and isinstance(arg_end_time, list):
            arg_end_time = pd.Series(arg_end_time)
        kwargs["end_time"] = arg_end_time

        res = _percent_time_in_market_impl(**kwargs)
        logger.info("Executed percent_time_in_market tool successfully.")

        data_payload = res
        if hasattr(res, "to_dict") and callable(res.to_dict):
            data_payload = (
                res.to_dict(orient="records")
                if isinstance(res, pd.DataFrame)
                else res.to_dict()
            )
        elif hasattr(res, "tolist") and callable(res.tolist):
            data_payload = res.tolist()
        elif (
            isinstance(res, (list, tuple))
            and len(res) > 0
            and hasattr(res[0], "to_dict")
        ):
            data_payload = [x.to_dict() for x in res]
        elif isinstance(res, (pd.Timestamp, pd.Timedelta)):
            data_payload = str(res)

        return analytics_tool_result(
            "percent_time_in_market", data={"percent_time_in_market": data_payload}
        )
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}
