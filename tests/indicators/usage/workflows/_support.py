"""Shared, non-workflow infrastructure for Indicators workflow examples."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import MarketDataset, get_market_data, unwrap_data_response
from app.services.indicators import IndicatorConfig
from tests.data.usage.workflows._support import market_request


@lru_cache(maxsize=4)
def live_bars(timeframe: str = "M1", limit: int = 80) -> MarketDataset:
    """Read bounded genuine MT5 bars through the Data public boundary."""
    response = get_market_data(market_request("bars", timeframe=timeframe, limit=limit))
    return unwrap_data_response(
        response,
        operation="indicators.usage.workflow.live_bars",
        request_id=response.metadata.request_id,
    )


def indicator_config(indicator_id: str, period: int) -> IndicatorConfig:
    """Build one immutable values-only indicator configuration."""
    return IndicatorConfig(
        indicator_id=indicator_id,
        parameters=(("period", period),),
        source="close",
        formula_version="1.0.0",
        output_mode="values",
        column_conflict_policy="error",
        precision_dtype="float64",
        availability_policy="source_available_at",
        quality_policy="propagate_dataset",
        error_mode="raise",
    )


__all__ = ["indicator_config", "live_bars"]
