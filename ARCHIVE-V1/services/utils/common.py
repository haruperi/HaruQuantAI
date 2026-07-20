"""Public utility tools for HaruQuant.

Purpose:
    This module provides shared data manipulation, comparison, and numerical
    utility tools used across the HaruQuant framework. It includes helpers
    for parameter expansion, dataframe alignment, and high-performance
    rolling calculations using Numba.

Rule 1 - Entities:
    - Param (Class): Wrapper for optimization-style parameter expansion.
    - HQTAccessor (Class): Pandas DataFrame accessor for HaruQuant utility helpers.
    - HQTSeriesAccessor (Class): Pandas Series accessor for HaruQuant utility helpers.
    - combine_params (Function): Expand raw values and Param objects into parameter dictionaries.
    - merge (Function): Merge a higher-timeframe dataset into a lower-timeframe dataset.
    - concat (Function): Concatenate multiple datasets into a single Data object.
    - rolling_mean (Function): Compute a rolling mean with an optional Numba-optimized path.
    - chunked (Function/Decorator): Decorator to run a function over data chunks.
    - serialize_dataframe_records (Function): Convert a pandas DataFrame to JSON-safe records.
    - bars_to_records (Function): Convert indexed OHLCV bars to JSON-safe records.
    - clear_dataframe_cache (Function): Clear the shared in-memory dataframe cache.
    - get_cached_dataframe (Function): Get a dataframe-like object from cache or load it.
    - tool_result_envelope (Function): Build a standard HaruQuant tool result envelope.
    - align_dataframes_by_datetime (AI Tool): Align two dataframes by common datetime index values.
    - compare_dataframes (AI Tool): Compare two dataframes for equality across selected columns.
    - compare_ohlc (AI Tool): Compare matching OHLC columns between two dataframes.
    - compare_ohlcv (AI Tool): Compare matching OHLCV columns between two dataframes.

Notes:
    External-facing functions imported by app.services.utils are exposed through
    app/services/utils/__init__.py; private underscore helpers remain implementation details.
"""

from __future__ import annotations

import json
import random
import time
from collections.abc import Callable, Iterable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import datetime
from functools import partial, wraps
from itertools import product
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services import load_service_module, resolve_service_attr, service_modules
from app.services.utils.errors import ErrorDescriptor, InfrastructureError
from app.services.utils.logger import logger
from app.services.utils.normalization import format_timestamp_z, to_utc
from app.services.utils.standard import ToolStandardSpec, standard_tool_response

# Tool Metadata Constants
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL = "low"
REQUIRES_APPROVAL = False
READ_ONLY = True
WRITES_FILE = False
MODIFIES_DATABASE = False
PLACES_TRADE = False
REQUIRES_NETWORK = False

# Optional dependencies for numerical processing
np: Any
pd: Any
try:
    import numpy as _np
    import pandas as _pd

    np = _np
    pd = _pd
except ModuleNotFoundError as exc:
    if exc.name not in {"pandas", "numpy"}:
        raise
    np = None
    pd = None

# Optional Numba support for high-performance calculations
try:
    if np is None:
        raise ImportError("numpy")
    from numba import njit, prange

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    def njit(*_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], Any]:
        """Return the wrapped function unchanged when Numba is unavailable."""

        def wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
            """Identity wrapper when Numba is not installed."""
            return func

        return wrapper

    prange = range


_SERVICE_MODULES = tuple(
    module_name
    for module_name in service_modules("app.services.utils")
    if module_name not in {"app.services.utils", "app.services.utils.common"}
)
logger_module = load_service_module("app.services.utils.logger")
_DATAFRAME_CACHE: dict[str, Any] = {}


def _get_data_class() -> Any:
    """
    Retrieve the Data wrapper class from app.services.data.

    Returns:
        Any: The Data class definition.
    """
    from app.services.data.frames import Data

    return Data


class Param:
    """
    Wrap parameter values for optimization-style parameter expansion.

    This class allows users to define parameters that should be either
    zipped together or combined via cartesian product during optimization
    tasks.

    Args:
        values (Any): One value, a list/tuple of values, or a NumPy array.
        name (str, optional): Display name for the parameter.
        level (int, optional): Grouping level for zipping. Parameters with the
            same level are zipped; others are combined by cartesian product.
    """

    def __init__(
        self,
        values: Any,
        name: str | None = None,
        level: int | None = None,
    ) -> None:
        """
        Initialize a Param instance with values and optional metadata.

        Logic:
        1. Normalizes input `values` into a list.
        2. Handles NumPy arrays by converting to list.
        3. Stores optional name and zipping level.
        """
        if np is not None and isinstance(values, np.ndarray):
            self.values: list[Any] = values.tolist()
        elif not isinstance(values, (list, tuple)):
            self.values = [values]
        else:
            self.values = list(values)
        self.name = name
        self.level = level

    def __iter__(self) -> Iterable[Any]:
        """Iterate over wrapped parameter values."""
        return iter(self.values)

    def __len__(self) -> int:
        """Return the number of wrapped parameter values."""
        return len(self.values)

    def __repr__(self) -> str:
        """Return a compact developer-facing representation."""
        return f"Param(values={self.values}, name={self.name}, level={self.level})"


def __getattr__(name: str) -> Any:
    """
    Resolve dynamic utility attributes from service modules.

    This allows app.services.utils to act as a facade for multiple sub-modules.

    Logic:
    1. Checks if the attribute exists in the logger service module.
    2. Falls back to resolving from other registered service modules.

    Args:
        name (str): Attribute name requested from the app.services.utils module.

    Returns:
        Any: The matching logger helper or service utility attribute.

    Raises:
        AttributeError: If the name cannot be resolved from app.services.utils.
    """
    if name.startswith("__"):
        raise AttributeError(name)
    if hasattr(logger_module, name):
        value = getattr(logger_module, name)
        globals()[name] = value
        return value
    return resolve_service_attr(name, _SERVICE_MODULES)


def _as_list(value: Any) -> list[Any]:
    """
    Ensure the input value is returned as a list.

    Args:
        value (Any): The value to wrap or convert.

    Returns:
        List[Any]: A list containing the value or the converted list.
    """
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _combine_params(  # noqa: C901
    params_dict: dict[str, Any],
    random_subset: int | None = None,
    build_index: bool = False,
) -> list[dict[str, Any]]:
    """Internal logic for combining parameters."""
    _ = build_index
    levels: dict[int, dict[str, list[Any]]] = {}
    default_level_counter = 1000

    for name, param in params_dict.items():
        if isinstance(param, Param):
            level = param.level if param.level is not None else default_level_counter
            if param.level is None:
                default_level_counter += 1
            values = list(param.values)
        else:
            level = default_level_counter
            default_level_counter += 1
            values = _as_list(param)

        levels.setdefault(level, {})[name] = values

    level_combinations: list[list[dict[str, Any]]] = []
    for level in sorted(levels):
        group = levels[level]
        lengths = {name: len(values) for name, values in group.items()}
        max_len = max(lengths.values())

        for name, length in lengths.items():
            if length not in {1, max_len}:
                raise ValueError(
                    f"Parameters in level {level} must have the same length "
                    f"or length 1. Error in {name}."
                )

        group_combos: list[dict[str, Any]] = []
        for index in range(max_len):
            combo = {
                name: values[index] if len(values) > 1 else values[0]
                for name, values in group.items()
            }
            group_combos.append(combo)
        level_combinations.append(group_combos)

    final_combos: list[dict[str, Any]] = []
    for product_tuple in product(*level_combinations):
        merged: dict[str, Any] = {}
        for combo in product_tuple:
            merged.update(combo)
        final_combos.append(merged)

    if random_subset and random_subset < len(final_combos):
        final_combos = random.sample(final_combos, random_subset)

    return final_combos


def combine_params(
    params_dict: dict[str, Any],
    random_subset: int | None = None,
    build_index: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Expand raw values and Param objects into parameter dictionaries.

    Use this tool to generate all valid combinations of parameters for
    optimization or multi-strategy backtesting.

    Args:
        params_dict (Dict[str, Any]): Mapping from parameter names to values or Param objects.
        random_subset (int, optional): Maximum number of combinations to sample.
        build_index (bool): Reserved for VectorBT compatibility. Defaults to False.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with data containing the combinations.
    """
    tool_name = "combine_params"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if not isinstance(params_dict, dict):
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=invalid_params_dict",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "params_dict must be a dictionary.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "params_dict must be a dictionary.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        final_combos = _combine_params(params_dict, random_subset, build_index)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "{} completed successfully | request_id={} | combinations={}",
            tool_name,
            request_id,
            len(final_combos),
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Combined params into {len(final_combos)} combinations.",
            "data": final_combos,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Parameter combination failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _merge(
    lower_data: Any,
    higher_data: Any,
    suffix: str = "_H",
) -> Any:
    """Internal logic for merging datasets."""
    if pd is None:
        raise ModuleNotFoundError("pandas")

    data_class = _get_data_class()
    lower_frame = lower_data.df if isinstance(lower_data, data_class) else lower_data
    higher_frame = (
        higher_data.df if isinstance(higher_data, data_class) else higher_data
    )
    merged_df = lower_frame.join(higher_frame.add_suffix(suffix), how="left").ffill()

    symbol = lower_data._symbol if isinstance(lower_data, data_class) else None
    timeframe = lower_data._timeframe if isinstance(lower_data, data_class) else None

    return data_class(merged_df, symbol=symbol, timeframe=timeframe)


def merge(
    lower_data: Any,
    higher_data: Any,
    suffix: str = "_H",
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Merge a higher-timeframe dataset into a lower-timeframe dataset.

    Use this tool to align multi-timeframe data for analysis or strategy execution.

    Args:
        lower_data (Any): Base lower-timeframe Data object or pandas DataFrame.
        higher_data (Any): Higher-timeframe Data object or pandas DataFrame.
        suffix (str): Suffix for higher-timeframe columns. Defaults to "_H".
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with the merged Data object.
    """
    tool_name = "merge"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if lower_data is None or higher_data is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_data",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Both lower_data and higher_data are required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "Data objects cannot be None.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _merge(lower_data, higher_data, suffix)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info("{} completed successfully | request_id={}", tool_name, request_id)

        # 3. Structured Return
        return {
            "status": "success",
            "message": "Merged higher-timeframe data into lower-timeframe.",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Data merge failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _concat(
    data_list: list[Any],
    keys: list[Any] | None = None,
    axis: int = 1,
) -> Any:
    """Internal logic for concatenating datasets."""
    if pd is None:
        raise ModuleNotFoundError("pandas")

    data_class = _get_data_class()
    frames = [item.df if isinstance(item, data_class) else item for item in data_list]
    combined_df = pd.concat(frames, axis=axis, keys=keys)

    timeframe = None
    for item in data_list:
        if isinstance(item, data_class) and item._timeframe:
            timeframe = item._timeframe
            break

    return data_class(
        combined_df,
        symbol=str(keys) if keys else None,
        timeframe=timeframe,
    )


def concat(
    data_list: list[Any],
    keys: list[Any] | None = None,
    axis: int = 1,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Concatenate multiple datasets into a single Data object.

    Use this tool to combine multiple symbols or features into one dataset.

    Args:
        data_list (List[Any]): List of Data objects, DataFrames, or Series.
        keys (List[Any], optional): Labels for MultiIndex along the concat axis.
        axis (int): Axis for concatenation (0 for rows, 1 for cols). Defaults to 1.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with the concatenated Data object.
    """
    tool_name = "concat"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if not data_list:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=empty_data_list",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "data_list cannot be empty.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "data_list must contain at least one item.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _concat(data_list, keys, axis)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "{} completed successfully | request_id={} | items={}",
            tool_name,
            request_id,
            len(data_list),
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Concatenated {len(data_list)} data objects.",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Data concatenation failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


if pd is None:

    class HQTAccessor:
        """Unavailable DataFrame accessor placeholder when pandas is absent."""

        def __init__(self, obj: Any) -> None:
            """Store nothing; pandas accessors are unavailable."""
            _ = obj

    class HQTSeriesAccessor:
        """Unavailable Series accessor placeholder when pandas is absent."""

        def __init__(self, obj: Any) -> None:
            """Store nothing; pandas accessors are unavailable."""
            _ = obj

else:

    @pd.api.extensions.register_dataframe_accessor("hqt")
    class HQTAccessor:  # type: ignore[no-redef]
        """Pandas DataFrame accessor for HaruQuant utility helpers."""

        def __init__(self, pandas_obj: Any) -> None:
            """Initialize the accessor with a pandas object."""
            self._obj = pandas_obj

        def rolling_mean(
            self, window: int, jitted: dict[str, Any] | None = None
        ) -> Any:
            """Compute a rolling mean for the accessor DataFrame.

            Args:
                window (int): Rolling window size.
                jitted (Dict[str, Any], optional): Numba execution options,
                    for example ``{"parallel": True}``.

            Returns:
                Any: A pandas DataFrame of rolling-mean values aligned to
                    the accessor's index and columns.
            """
            return _rolling_mean(self._obj, window, jitted=jitted)

    @pd.api.extensions.register_series_accessor("hqt")
    class HQTSeriesAccessor:  # type: ignore[no-redef]
        """Pandas Series accessor for HaruQuant utility helpers."""

        def __init__(self, pandas_obj: Any) -> None:
            """Initialize the accessor with a pandas object."""
            self._obj = pandas_obj

        def rolling_mean(
            self, window: int, jitted: dict[str, Any] | None = None
        ) -> Any:
            """Compute a rolling mean for the accessor Series.

            Args:
                window (int): Rolling window size.
                jitted (Dict[str, Any], optional): Numba execution options,
                    for example ``{"parallel": True}``.

            Returns:
                Any: A pandas Series of rolling-mean values aligned to the
                    accessor's index.
            """
            return _rolling_mean(self._obj, window, jitted=jitted)


@njit  # type: ignore[untyped-decorator]
def _rolling_mean_nb(arr: Any, window: int) -> Any:
    """
    Internal Numba-optimized rolling mean calculation.

    Args:
        arr (Any): NumPy array to process.
        window (int): Rolling window size.

    Returns:
        Any: NumPy array containing the rolling mean.
    """
    n, m = arr.shape
    out = np.empty((n, m))
    out[:] = np.nan
    for col_index in range(m):
        for row_index in range(window - 1, n):
            value = 0.0
            for offset in range(window):
                value += arr[row_index - offset, col_index]
            out[row_index, col_index] = value / window
    return out


@njit(parallel=True)  # type: ignore[untyped-decorator]
def _rolling_mean_parallel_nb(arr: Any, window: int) -> Any:
    """
    Internal parallel Numba-optimized rolling mean calculation.

    Args:
        arr (Any): NumPy array to process.
        window (int): Rolling window size.

    Returns:
        Any: NumPy array containing the rolling mean.
    """
    n, m = arr.shape
    out = np.empty((n, m))
    out[:] = np.nan
    for col_index in prange(m):
        for row_index in range(window - 1, n):
            value = 0.0
            for offset in range(window):
                value += arr[row_index - offset, col_index]
            out[row_index, col_index] = value / window
    return out


def _rolling_mean(
    data: Any,
    window: int,
    jitted: dict[str, Any] | None = None,
) -> Any:
    """Internal logic for rolling mean calculation."""
    if pd is None or np is None:
        raise ModuleNotFoundError("pandas or numpy")

    input_is_series = isinstance(data, pd.Series)
    if isinstance(data, (pd.DataFrame, pd.Series)):
        arr = data.values
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
    else:
        arr = data

    parallel = jitted.get("parallel", False) if jitted else False
    if HAS_NUMBA:
        result = (
            _rolling_mean_parallel_nb(arr, window)
            if parallel
            else _rolling_mean_nb(arr, window)
        )
    else:
        result = pd.DataFrame(arr).rolling(window).mean().values

    if isinstance(data, pd.DataFrame):
        return pd.DataFrame(result, index=data.index, columns=data.columns)
    if input_is_series:
        return pd.Series(result.flatten(), index=data.index, name=data.name)

    return result


def rolling_mean(
    data: Any,
    window: int,
    jitted: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Compute a rolling mean with a Numba path when available.

    Use this tool for high-performance indicator calculation on large datasets.

    Args:
        data (Any): Input pandas DataFrame, Series, or NumPy array.
        window (int): Rolling window size.
        jitted (Dict[str, Any], optional): Execution options. Use
            {"parallel": True} for parallel Numba execution.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with the rolling mean result.
    """
    tool_name = "rolling_mean"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | window={}", tool_name, request_id, window)

    # 1. Input Validation
    if data is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_data",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Data is required.",
            "data": None,
            "error": {"code": "INVALID_INPUT", "details": "data cannot be None."},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _rolling_mean(data, window, jitted)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info("{} completed successfully | request_id={}", tool_name, request_id)

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Computed rolling mean (window={window}).",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Rolling mean calculation failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _chunk_worker(
    func: Callable[..., Any],
    chunk: Any,
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Execute one data chunk for thread/process chunked helpers."""
    return func(chunk, *args, **kwargs)


def _chunked(  # noqa: C901
    size: int | None = 1,
    axis: int = 1,
    engine: str = "sequential",
    merge_func: Callable[[list[Any]], Any] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Internal decorator logic for chunked execution."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a callable so its first argument is processed in chunks."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute the wrapped callable over chunks and merge the results."""
            if np is None or pd is None:
                raise ModuleNotFoundError("numpy or pandas")

            active_merge_func = merge_func or np.column_stack
            exec_kwargs = kwargs.pop("_execute_kwargs", {})
            active_engine = exec_kwargs.get("engine", engine)

            if not args:
                return func(*args, **kwargs)

            data = args[0]
            other_args = args[1:]
            if isinstance(data, np.ndarray):
                n_chunks = max(1, data.shape[axis] // size) if size else 1
                chunks = np.array_split(data, n_chunks, axis=axis)
            elif isinstance(data, (pd.DataFrame, pd.Series)):
                arr = data.values
                n_chunks = max(1, arr.shape[axis] // size) if size else 1
                chunks = np.array_split(arr, n_chunks, axis=axis)
            else:
                chunks = [data]

            if active_engine == "sequential":
                results = [func(chunk, *other_args, **kwargs) for chunk in chunks]
            elif active_engine == "threadpool":
                worker = partial(_chunk_worker, func, args=other_args, kwargs=kwargs)
                with ThreadPoolExecutor() as executor:
                    results = list(executor.map(worker, chunks))
            elif active_engine == "processpool":
                worker = partial(_chunk_worker, func, args=other_args, kwargs=kwargs)
                with ProcessPoolExecutor() as executor:
                    results = list(executor.map(worker, chunks))
            else:
                raise ValueError(f"Unknown engine: {active_engine}")

            if not results:
                return None
            return active_merge_func(results) if len(results) > 1 else results[0]

        return wrapper

    return decorator


def chunked(
    data: Any,
    func: Callable[..., Any],
    size: int | None = 1,
    axis: int = 1,
    engine: str = "sequential",
    merge_func: Callable[[list[Any]], Any] | None = None,
    request_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Execute a function over data chunks.

    Use this tool to parallelize operations over large DataFrames or arrays.

    Args:
        data (Any): The data to split and process.
        func (Callable): The function to apply to each chunk.
        size (int, optional): Rows or columns per chunk. Defaults to 1.
        axis (int): Axis to split along (0 for rows, 1 for columns). Defaults to 1.
        engine (str): Execution engine: sequential, threadpool, or processpool.
        merge_func (Callable, optional): Function to combine results.
        request_id (Optional[str], optional): Optional workflow/request ID.
        **kwargs: Additional arguments passed to func.

    Returns:
        Dict[str, Any]: Standard tool response with the merged result.
    """
    tool_name = "chunked"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | engine={}", tool_name, request_id, engine)

    # 1. Input Validation
    if data is None or func is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_inputs",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Both data and func are required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "data and func cannot be None.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        wrapper = _chunked(size, axis, engine, merge_func)(func)
        result = wrapper(data, **kwargs)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info("{} completed successfully | request_id={}", tool_name, request_id)

        # 3. Structured Return
        return {
            "status": "success",
            "message": "Chunked execution completed.",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Chunked execution failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _serialize_dataframe_records(frame: Any) -> list[dict[str, Any]]:
    """Internal logic for dataframe record serialization."""
    if pd is None:
        raise ModuleNotFoundError("pandas")
    records_json = frame.reset_index().to_json(orient="records", date_format="iso")
    records = json.loads(records_json)
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def serialize_dataframe_records(
    frame: Any,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Convert a pandas DataFrame to JSON-safe records.

    Use this tool to prepare data for network transmission or agent consumption.

    Args:
        frame (Any): The pandas DataFrame to serialize.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with serialized records in data.
    """
    tool_name = "serialize_dataframe_records"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if frame is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_frame",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Frame is required.",
            "data": None,
            "error": {"code": "INVALID_INPUT", "details": "frame cannot be None."},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _serialize_dataframe_records(frame)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "{} completed successfully | request_id={} | records={}",
            tool_name,
            request_id,
            len(result),
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Serialized {len(result)} records from DataFrame.",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Serialization failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _bars_to_records(frame: Any) -> list[dict[str, Any]]:
    """Internal logic for converting OHLCV bars to records."""
    records: list[dict[str, Any]] = []
    for timestamp, row in frame.iterrows():
        record = {"timestamp": format_timestamp_z(to_utc(timestamp)["data"])}
        record.update({column: row[column] for column in frame.columns})
        records.append(record)
    return records


def bars_to_records(
    frame: Any,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Convert indexed OHLCV bars to JSON-safe records with a UTC timestamp field.

    Use this tool when working with historical market data that needs to be
    standardized into a list of record objects.

    Args:
        frame (Any): A pandas DataFrame indexed by timestamps.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with JSON-safe bar records in data.
    """
    tool_name = "bars_to_records"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if frame is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_frame",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Frame is required.",
            "data": None,
            "error": {"code": "INVALID_INPUT", "details": "frame cannot be None."},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _bars_to_records(frame)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "{} completed successfully | request_id={} | bars={}",
            tool_name,
            request_id,
            len(result),
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Converted {len(result)} bars to records.",
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Conversion failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _clear_dataframe_cache() -> None:
    """Internal logic for clearing the dataframe cache."""
    _DATAFRAME_CACHE.clear()


def clear_dataframe_cache(
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Clear the shared in-memory dataframe cache.

    Use this tool to free up memory or force reload of cached data.

    Args:
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response.
    """
    tool_name = "clear_dataframe_cache"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        # 2. Core Execution
        _clear_dataframe_cache()
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info("{} completed successfully | request_id={}", tool_name, request_id)

        # 3. Structured Return
        return {
            "status": "success",
            "message": "Cleared dataframe cache.",
            "data": True,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Failed to clear cache.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _get_cached_dataframe(key: str, loader_func: Callable[[], Any]) -> Any:
    """Internal logic for getting a cached dataframe."""
    if key in _DATAFRAME_CACHE:
        cached = _DATAFRAME_CACHE[key]
        return cached.copy() if hasattr(cached, "copy") else cached

    loaded = loader_func()
    _DATAFRAME_CACHE[key] = loaded
    return loaded.copy() if hasattr(loaded, "copy") else loaded


def get_cached_dataframe(
    key: str,
    loader_func: Callable[[], Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Get a dataframe-like object from cache or load it.

    Use this tool to avoid expensive re-loading of the same dataset multiple times.

    Args:
        key (str): Unique cache key.
        loader_func (Callable): Loader called on cache miss.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with the cached or loaded object in data.
    """
    tool_name = "get_cached_dataframe"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={} | key={}", tool_name, request_id, key)

    # 1. Input Validation
    if not key or loader_func is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_inputs",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Both key and loader_func are required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "key and loader_func cannot be None.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        hit = key in _DATAFRAME_CACHE
        result = _get_cached_dataframe(key, loader_func)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        logger.info(
            "{} completed successfully | request_id={} | cache_hit={}",
            tool_name,
            request_id,
            hit,
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": (
                "Retrieved dataframe from cache."
                if hit
                else "Loaded and cached dataframe."
            ),
            "data": result,
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Cache retrieval failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def tool_result_envelope(
    *,
    status: str,
    tool_name: str,
    data: dict[str, Any] | None = None,
    tool_call_id: str | None = None,
    request_id: str | None = None,
    agent_name: str | None = None,
    environment: str = "development",
    dry_run: bool = False,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
    started_at: str | None = None,
    side_effects: list[str] | None = None,
    approval_required: str = "none",
    risk_level: str = "low",
) -> dict[str, Any]:
    """Build a standard HaruQuant tool result envelope.

    Normalizes a caller-supplied status and error list into the standard
    HaruQuant response envelope produced by ``standard_tool_response``.

    Args:
        status (str): Caller-reported status; coerced to ``"error"`` when
            any errors are present.
        tool_name (str): Stable public tool name for the envelope metadata.
        data (Dict[str, Any], optional): Result payload for the envelope.
        tool_call_id (str, optional): Optional tool-call identifier
            (reserved; not yet emitted).
        request_id (str, optional): Optional trace request identifier.
        agent_name (str, optional): Optional originating agent name
            (reserved).
        environment (str): Deployment environment label. Defaults to
            ``"development"`` (reserved).
        dry_run (bool): Whether the call was a dry run (reserved).
            Defaults to False.
        errors (List[str], optional): Error detail strings; any non-empty
            value forces an error envelope.
        warnings (List[str], optional): Warning strings (reserved).
        started_at (str, optional): Optional start timestamp (reserved).
        side_effects (List[str], optional): Declared side effects; when
            empty the tool is marked read-only.
        approval_required (str): Approval requirement label. Defaults to
            ``"none"`` (reserved).
        risk_level (str): Tool risk level for the envelope metadata.
            Defaults to ``"low"``.

    Returns:
        Dict[str, Any]: A standard HaruQuant tool response envelope.

    Side effects:
        Emits a debug log line. Does not mutate caller inputs.
    """
    _ = (
        tool_call_id,
        agent_name,
        environment,
        dry_run,
        warnings,
        started_at,
        side_effects,
        approval_required,
        uuid4,
    )
    error_list = errors or []
    normalized_status = "success" if status == "success" and not error_list else "error"
    result = standard_tool_response(
        spec=ToolStandardSpec(
            tool_name=tool_name,
            tool_category="utils",
            tool_risk_level=risk_level,
            read_only=not side_effects,
        ),
        status=normalized_status,
        message=(
            "Utility tool executed successfully."
            if normalized_status == "success"
            else "Utility tool execution failed."
        ),
        data=data,
        error=(
            None
            if normalized_status == "success"
            else {
                "code": "TOOL_EXECUTION_FAILED",
                "details": "; ".join(error_list) or "Utility tool failed.",
            }
        ),
        request_id=request_id,
        execution_ms=0.0,
    )
    logger.debug(f"Built tool result envelope for {tool_name} (status={status}).")
    return result


def _canonicalize(value: Any, *, redact_sensitive: bool = True) -> Any:  # noqa: C901
    """Convert arbitrary supported values into deterministic JSON-safe data."""
    sensitive_tokens = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_key",
        "private_key",
        "auth",
        "credential",
        "bearer",
    }
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in sorted(value.items(), key=lambda pair: str(pair[0])):
            key_text = str(key)
            if redact_sensitive and any(
                token in key_text.lower() for token in sensitive_tokens
            ):
                normalized[key_text] = "***REDACTED***"
            else:
                normalized[key_text] = _canonicalize(
                    item, redact_sensitive=redact_sensitive
                )
        return normalized
    if isinstance(value, (list, tuple)):
        return [
            _canonicalize(item, redact_sensitive=redact_sensitive) for item in value
        ]
    if isinstance(value, (datetime,)):
        return format_timestamp_z(value)["data"]
    if hasattr(value, "isoformat") and callable(value.isoformat):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, Path):
        return str(value)
    if pd is not None and hasattr(pd, "isna"):
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
    return value


def canonical_json(
    value: Any,
    *,
    redact_sensitive: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Serialize supported values into deterministic, JSON-safe text.

    Args:
        value: Data to serialize.
        redact_sensitive: Whether sensitive mapping keys should be redacted.
        request_id: Optional request ID for response metadata.

    Returns:
        Standard tool response containing a canonical JSON string.
    """
    tool_name = "canonical_json"
    started_at = time.perf_counter()
    spec = ToolStandardSpec(tool_name=tool_name, tool_category=TOOL_CATEGORY)
    try:
        normalized = _canonicalize(value, redact_sensitive=redact_sensitive)
        result = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
            default=str,
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "success",
            "Canonical JSON serialized.",
            data=result,
            request_id=request_id,
            execution_ms=execution_ms,
        )
    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        return standard_tool_response(
            spec,
            "error",
            "Canonical JSON serialization failed.",
            error={"code": "CANONICAL_JSON_FAILED", "details": str(error)},
            request_id=request_id,
            execution_ms=execution_ms,
        )


def _align_dataframes_by_datetime(
    df1: Any, df2: Any, verbose: bool = False
) -> dict[str, Any]:
    """Internal logic for aligning dataframes by datetime."""
    if pd is None:
        raise ModuleNotFoundError("pandas")

    df1_work = df1.copy()
    df2_work = df2.copy()

    # Remove timezone for alignment if present
    if df1_work.index.tz is not None:
        df1_work.index = df1_work.index.tz_localize(None)
    if df2_work.index.tz is not None:
        df2_work.index = df2_work.index.tz_localize(None)

    start_point = max(df1_work.index.min(), df2_work.index.min())
    end_point = min(df1_work.index.max(), df2_work.index.max())

    if start_point > end_point:
        return {"status": "error", "message": "No datetime intersection found."}

    df1_aligned = df1_work.loc[start_point:end_point]
    df2_aligned = df2_work.loc[start_point:end_point]

    common_index = df1_aligned.index.intersection(df2_aligned.index)
    if len(common_index) == 0:
        return {
            "status": "error",
            "message": "No common datetime indices found in intersection range.",
        }

    df1_aligned = df1_aligned.loc[common_index]
    df2_aligned = df2_aligned.loc[common_index]

    return {
        "status": "success",
        "data": {
            "df1_aligned": _serialize_dataframe_records(df1_aligned),
            "df2_aligned": _serialize_dataframe_records(df2_aligned),
            "rows": len(common_index),
        },
    }


def align_dataframes_by_datetime(
    df1: Any,
    df2: Any,
    verbose: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Align two dataframes by their common datetime index values.

    Use this tool when you have two datasets from different sources or
    timeframes and need to align them for direct comparison or correlation.

    Args:
        df1 (Any): The first pandas DataFrame.
        df2 (Any): The second pandas DataFrame.
        verbose (bool): Whether to enable verbose output. Defaults to False.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with aligned records in data.
    """
    tool_name = "align_dataframes_by_datetime"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if df1 is None or df2 is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_dataframes",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Both df1 and df2 are required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "df1 and df2 cannot be None.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _align_dataframes_by_datetime(df1, df2, verbose)
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        if result["status"] == "error":
            logger.warning(
                "{} failed | request_id={} | reason={}",
                tool_name,
                request_id,
                result["message"],
            )
            return {
                "status": "error",
                "message": result["message"],
                "data": None,
                "error": {"code": "DATA_NOT_FOUND", "details": result["message"]},
                "metadata": {
                    "tool_name": tool_name,
                    "tool_version": TOOL_VERSION,
                    "tool_category": TOOL_CATEGORY,
                    "tool_risk_level": TOOL_RISK_LEVEL,
                    "request_id": request_id,
                    "execution_ms": execution_ms,
                    "read_only": READ_ONLY,
                    "writes_file": WRITES_FILE,
                    "modifies_database": MODIFIES_DATABASE,
                    "places_trade": PLACES_TRADE,
                    "requires_network": REQUIRES_NETWORK,
                },
            }

        logger.info(
            "{} completed successfully | request_id={} | rows={}",
            tool_name,
            request_id,
            result["data"]["rows"],
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": f"Aligned dataframes: {result['data']['rows']} common rows found.",
            "data": result["data"],
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Dataframe alignment failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _compare_dataframes(  # noqa: C901
    df1: Any,
    df2: Any,
    columns: str | list[str] | None = None,
    tolerance: float = 1e-10,
    check_index: bool = False,
    align_by_datetime: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    """Internal logic for comparing dataframes."""
    if pd is None or np is None:
        raise ModuleNotFoundError("pandas or numpy")

    df1_work = df1.copy()
    df2_work = df2.copy()

    if align_by_datetime:
        aligned_res = _align_dataframes_by_datetime(df1_work, df2_work, verbose=verbose)
        if aligned_res["status"] == "error":
            return {
                "status": "success",
                "data": {"is_equal": False, "reason": aligned_res["message"]},
            }
        df1_records = aligned_res["data"]["df1_aligned"]
        df2_records = aligned_res["data"]["df2_aligned"]

        idx_key = "index" if df1_records and "index" in df1_records[0] else "timestamp"
        df1_work = pd.DataFrame(df1_records).set_index(idx_key)
        df2_work = pd.DataFrame(df2_records).set_index(idx_key)
        df1_work.index = pd.to_datetime(df1_work.index)
        df2_work.index = pd.to_datetime(df2_work.index)

    if columns is None:
        columns_to_compare = list(set(df1_work.columns) & set(df2_work.columns))
        if not columns_to_compare:
            return {
                "status": "success",
                "data": {"is_equal": False, "reason": "No common columns found"},
            }
        if df1_work.shape != df2_work.shape:
            return {
                "status": "success",
                "data": {
                    "is_equal": False,
                    "reason": f"Dataframes have different shapes: {df1_work.shape} vs {df2_work.shape}",
                },
            }
    else:
        columns_to_compare = [columns] if isinstance(columns, str) else columns
        missing_df1 = [c for c in columns_to_compare if c not in df1_work.columns]
        missing_df2 = [c for c in columns_to_compare if c not in df2_work.columns]
        if missing_df1 or missing_df2:
            return {
                "status": "error",
                "message": f"Missing columns in df1: {missing_df1}, df2: {missing_df2}",
            }
        if len(df1_work) != len(df2_work):
            return {
                "status": "success",
                "data": {
                    "is_equal": False,
                    "reason": f"Row mismatch: {len(df1_work)} vs {len(df2_work)}",
                },
            }

    if check_index and not df1_work.index.equals(df2_work.index):
        return {
            "status": "success",
            "data": {"is_equal": False, "reason": "Indices are not equal"},
        }

    for col in columns_to_compare:
        col1 = df1_work[col]
        col2 = df2_work[col]
        if col1.dtype != col2.dtype:
            return {
                "status": "success",
                "data": {
                    "is_equal": False,
                    "reason": f"Type mismatch in column '{col}': {col1.dtype} vs {col2.dtype}",
                },
            }
        if pd.api.types.is_numeric_dtype(col1):
            if not _compare_numeric_series(col1, col2, tolerance):
                return {
                    "status": "success",
                    "data": {
                        "is_equal": False,
                        "reason": f"Value mismatch in numeric column '{col}' (tolerance={tolerance})",
                    },
                }
        elif not col1.equals(col2):
            return {
                "status": "success",
                "data": {
                    "is_equal": False,
                    "reason": f"Value mismatch in column '{col}'",
                },
            }

    return {"status": "success", "data": {"is_equal": True}}


def compare_dataframes(
    df1: Any,
    df2: Any,
    columns: str | list[str] | None = None,
    tolerance: float = 1e-10,
    check_index: bool = False,
    align_by_datetime: bool = False,
    verbose: bool = False,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Compare two dataframes for equality across selected columns.

    Use this tool to verify that two datasets contain identical data,
    optionally ignoring floating-point noise or aligning them by time.

    Args:
        df1 (Any): The first pandas DataFrame.
        df2 (Any): The second pandas DataFrame.
        columns (str | List[str], optional): Columns to compare. Defaults to all common.
        tolerance (float): Floating-point tolerance for numeric equality.
        check_index (bool): Whether to verify index equality. Defaults to False.
        align_by_datetime (bool): Whether to align by time before comparing.
        verbose (bool): Whether to enable verbose logging. Defaults to False.
        request_id (Optional[str], optional): Optional workflow/request ID.

    Returns:
        Dict[str, Any]: Standard tool response with equality details in data.
    """
    tool_name = "compare_dataframes"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    # 1. Input Validation
    if df1 is None or df2 is None:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.warning(
            "{} failed validation | request_id={} | reason=missing_dataframes",
            tool_name,
            request_id,
        )
        return {
            "status": "error",
            "message": "Both df1 and df2 are required.",
            "data": None,
            "error": {
                "code": "INVALID_INPUT",
                "details": "df1 and df2 cannot be None.",
            },
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    try:
        # 2. Core Execution
        result = _compare_dataframes(
            df1, df2, columns, tolerance, check_index, align_by_datetime, verbose
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        if result["status"] == "error":
            logger.warning(
                "{} failed | request_id={} | reason={}",
                tool_name,
                request_id,
                result["message"],
            )
            return {
                "status": "error",
                "message": result["message"],
                "data": None,
                "error": {"code": "INVALID_INPUT", "details": result["message"]},
                "metadata": {
                    "tool_name": tool_name,
                    "tool_version": TOOL_VERSION,
                    "tool_category": TOOL_CATEGORY,
                    "tool_risk_level": TOOL_RISK_LEVEL,
                    "request_id": request_id,
                    "execution_ms": execution_ms,
                    "read_only": READ_ONLY,
                    "writes_file": WRITES_FILE,
                    "modifies_database": MODIFIES_DATABASE,
                    "places_trade": PLACES_TRADE,
                    "requires_network": REQUIRES_NETWORK,
                },
            }

        equal = result["data"]["is_equal"]
        logger.info(
            "{} completed successfully | request_id={} | is_equal={}",
            tool_name,
            request_id,
            equal,
        )

        # 3. Structured Return
        return {
            "status": "success",
            "message": (
                "Dataframes are equal."
                if equal
                else f"Dataframes differ: {result['data'].get('reason', 'unknown')}"
            ),
            "data": result["data"],
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "Comparison failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def _compare_numeric_series(series1: Any, series2: Any, tolerance: float) -> bool:
    """
    Compare two numeric series with floating point tolerance.

    Logic:
    1. Checks for NaN equality (NaNs must be in the same positions).
    2. Filters for non-NaN values and uses `np.allclose` for comparison.

    Args:
        series1 (Any): The first numeric series.
        series2 (Any): The second numeric series.
        tolerance (float): Floating-point tolerance.

    Returns:
        bool: True if equal within tolerance, False otherwise.
    """
    try:
        if series1.isna().any() or series2.isna().any():
            nan1 = series1.isna()
            nan2 = series2.isna()
            if not nan1.equals(nan2):
                return False
            non_nan = ~(nan1 | nan2)
            if non_nan.any():
                return bool(
                    np.allclose(
                        series1[non_nan],
                        series2[non_nan],
                        atol=tolerance,
                        rtol=tolerance,
                    )
                )
            return True
        return bool(np.allclose(series1, series2, atol=tolerance, rtol=tolerance))
    except Exception:
        return bool(series1.equals(series2))


def _compare_ohl_columns(
    df1: Any,
    df2: Any,
    columns: list[str],
    missing_message: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Internal helper to compare matching OHLC-style columns.

    Args:
        df1 (Any): The first DataFrame.
        df2 (Any): The second DataFrame.
        columns (List[str]): Columns to look for.
        missing_message (str): Error message if no columns match.
        **kwargs: Passed to compare_dataframes.

    Returns:
        Dict[str, Any]: Standardized comparison result.
    """
    if df1 is None or df2 is None:
        return {"status": "error", "message": "Both df1 and df2 are required."}
    try:
        df1_cols = [c.lower() for c in df1.columns]
        df2_cols = [c.lower() for c in df2.columns]
        avail = [col for col in columns if col in df1_cols and col in df2_cols]
        if not avail:
            return {"status": "error", "message": missing_message}

        df1_work = df1.copy()
        df2_work = df2.copy()
        df1_work.columns = df1_cols
        df2_work.columns = df2_cols
        return _compare_dataframes(df1_work, df2_work, columns=avail, **kwargs)
    except Exception as error:
        return {"status": "error", "message": f"Tool execution failed: {error!s}"}


def compare_ohlcv(
    df1: Any,
    df2: Any,
    request_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Compare OHLCV columns between two dataframes.

    This tool checks for equality across 'open', 'high', 'low', 'close', and
    'volume' columns.

    Args:
        df1 (Any): The first DataFrame.
        df2 (Any): The second DataFrame.
        request_id (Optional[str], optional): Optional workflow/request ID.
        **kwargs: Additional options for comparison (tolerance, alignment, etc.).

    Returns:
        Dict[str, Any]: Standard tool response with equality status.
    """
    tool_name = "compare_ohlcv"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        result = _compare_ohl_columns(
            df1,
            df2,
            ["open", "high", "low", "close", "volume"],
            "No OHLCV columns found in both dataframes",
            **kwargs,
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        if result["status"] == "error":
            return {
                "status": "error",
                "message": result["message"],
                "data": None,
                "error": {"code": "INVALID_INPUT", "details": result["message"]},
                "metadata": {
                    "tool_name": tool_name,
                    "tool_version": TOOL_VERSION,
                    "tool_category": TOOL_CATEGORY,
                    "tool_risk_level": TOOL_RISK_LEVEL,
                    "request_id": request_id,
                    "execution_ms": execution_ms,
                    "read_only": READ_ONLY,
                    "writes_file": WRITES_FILE,
                    "modifies_database": MODIFIES_DATABASE,
                    "places_trade": PLACES_TRADE,
                    "requires_network": REQUIRES_NETWORK,
                },
            }

        equal = result["data"]["is_equal"]
        logger.info(
            "{} completed successfully | request_id={} | is_equal={}",
            tool_name,
            request_id,
            equal,
        )

        return {
            "status": "success",
            "message": (
                "OHLCV columns are equal."
                if equal
                else f"OHLCV mismatch: {result['data'].get('reason', 'unknown')}"
            ),
            "data": result["data"],
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "OHLCV comparison failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


def compare_ohlc(
    df1: Any,
    df2: Any,
    request_id: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Compare OHLC columns between two dataframes.

    This tool checks for equality across 'open', 'high', 'low', and 'close'
    columns.

    Args:
        df1 (Any): The first DataFrame.
        df2 (Any): The second DataFrame.
        request_id (Optional[str], optional): Optional workflow/request ID.
        **kwargs: Additional options for comparison (tolerance, alignment, etc.).

    Returns:
        Dict[str, Any]: Standard tool response with equality status.
    """
    tool_name = "compare_ohlc"
    started_at = time.perf_counter()

    logger.info("{} called | request_id={}", tool_name, request_id)

    try:
        result = _compare_ohl_columns(
            df1,
            df2,
            ["open", "high", "low", "close"],
            "No OHLC columns found in both dataframes",
            **kwargs,
        )
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)

        if result["status"] == "error":
            return {
                "status": "error",
                "message": result["message"],
                "data": None,
                "error": {"code": "INVALID_INPUT", "details": result["message"]},
                "metadata": {
                    "tool_name": tool_name,
                    "tool_version": TOOL_VERSION,
                    "tool_category": TOOL_CATEGORY,
                    "tool_risk_level": TOOL_RISK_LEVEL,
                    "request_id": request_id,
                    "execution_ms": execution_ms,
                    "read_only": READ_ONLY,
                    "writes_file": WRITES_FILE,
                    "modifies_database": MODIFIES_DATABASE,
                    "places_trade": PLACES_TRADE,
                    "requires_network": REQUIRES_NETWORK,
                },
            }

        equal = result["data"]["is_equal"]
        logger.info(
            "{} completed successfully | request_id={} | is_equal={}",
            tool_name,
            request_id,
            equal,
        )

        return {
            "status": "success",
            "message": (
                "OHLC columns are equal."
                if equal
                else f"OHLC mismatch: {result['data'].get('reason', 'unknown')}"
            ),
            "data": result["data"],
            "error": None,
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }

    except Exception as error:
        execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.exception("{} failed | request_id={}", tool_name, request_id)
        return {
            "status": "error",
            "message": "OHLC comparison failed.",
            "data": None,
            "error": {"code": "TOOL_EXECUTION_FAILED", "details": str(error)},
            "metadata": {
                "tool_name": tool_name,
                "tool_version": TOOL_VERSION,
                "tool_category": TOOL_CATEGORY,
                "tool_risk_level": TOOL_RISK_LEVEL,
                "request_id": request_id,
                "execution_ms": execution_ms,
                "read_only": READ_ONLY,
                "writes_file": WRITES_FILE,
                "modifies_database": MODIFIES_DATABASE,
                "places_trade": PLACES_TRADE,
                "requires_network": REQUIRES_NETWORK,
            },
        }


__all__ = [
    "ErrorDescriptor",
    "InfrastructureError",
    "Param",
    "align_dataframes_by_datetime",
    "bars_to_records",
    "canonical_json",
    "chunked",
    "clear_dataframe_cache",
    "combine_params",
    "compare_dataframes",
    "compare_ohlc",
    "compare_ohlcv",
    "concat",
    "get_cached_dataframe",
    "merge",
    "rolling_mean",
    "serialize_dataframe_records",
    "tool_result_envelope",
]
