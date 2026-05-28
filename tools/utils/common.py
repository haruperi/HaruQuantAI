"""Shared utility helpers for HaruQuantAI modules.

This module contains small internal helpers used across production tools. It is
not an official AI-tool module and does not expose agent-callable functions.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

import pandas as pd

from tools.utils.logger import logger

_DATAFRAME_CACHE: dict[str, pd.DataFrame] = {}


def clear_dataframe_cache() -> None:
    """Clear the process-local DataFrame cache."""
    _DATAFRAME_CACHE.clear()
    logger.info("DataFrame cache cleared")


def get_cached_dataframe(
    key: str,
    loader_func: Callable[[], pd.DataFrame],
) -> pd.DataFrame:
    """Return a cached DataFrame or load and cache it.

    Args:
        key: Unique cache key.
        loader_func: Callable that returns a DataFrame on cache miss.

    Returns:
        pd.DataFrame: Cached or freshly loaded DataFrame.

    Raises:
        ValueError: If the cache key is empty or the loader is not callable.
        TypeError: If the loader does not return a DataFrame.
    """
    if not isinstance(key, str) or not key.strip():
        raise ValueError("cache key must be a non-empty string.")
    if not callable(loader_func):
        raise ValueError("loader_func must be callable.")

    if key not in _DATAFRAME_CACHE:
        loaded = loader_func()
        if not isinstance(loaded, pd.DataFrame):
            raise TypeError("loader_func must return a pandas DataFrame.")
        _DATAFRAME_CACHE[key] = loaded.copy()

    return _DATAFRAME_CACHE[key].copy()


def bars_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Serialize a bar DataFrame into JSON-safe row dictionaries."""
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame must be a pandas DataFrame.")
    return cast(list[dict[str, Any]], frame.reset_index().to_dict(orient="records"))


__all__ = [
    "bars_to_records",
    "clear_dataframe_cache",
    "get_cached_dataframe",
]
