"""Shared, non-workflow infrastructure for Indicators workflow examples."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


from typing import Any

from app.services.indicators import build_indicator_config
from tests.indicators.usage._support import get_mt5_usage_dataset

MarketDataset = Any


@lru_cache(maxsize=4)
def live_bars(timeframe: str = "M1", limit: int = 80) -> MarketDataset:
    """Read bounded genuine MT5 bars through the Data public boundary."""
    del limit
    return get_mt5_usage_dataset(timeframe=timeframe)


def indicator_config(
    indicator_id: str,
    period: int | None = None,
    *,
    source: str | None = "close",
    parameters: tuple[tuple[str, int | float | str], ...] = (),
) -> object:
    """Build one immutable values-only indicator configuration."""
    resolved_parameters = parameters
    if period is not None:
        resolved_parameters = (("period", period), *resolved_parameters)
    resolved_parameters = tuple(sorted(resolved_parameters))
    return build_indicator_config(
        indicator_id=indicator_id,
        parameters=resolved_parameters,
        source=source,
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


__all__ = ["indicator_config", "live_bars"]
