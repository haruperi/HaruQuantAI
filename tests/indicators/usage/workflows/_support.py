"""Shared, non-workflow infrastructure for Indicators workflow examples."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from typing import Any

from app.services.data import (
    build_market_data_request,
    get_market_data,
    unwrap_data_response,
)
from app.services.indicators import build_indicator_config
from app.utils import generate_id


def market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    end = datetime.now(UTC)
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=end - timedelta(days=5),
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


MarketDataset = Any


@lru_cache(maxsize=4)
def live_bars(timeframe: str = "M1", limit: int = 80) -> MarketDataset:
    """Read bounded genuine MT5 bars through the Data public boundary."""
    response = get_market_data(market_request("bars", timeframe=timeframe, limit=limit))
    return unwrap_data_response(
        response,
        operation="indicators.usage.workflow.live_bars",
        request_id=response.metadata.request_id,
    )


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
