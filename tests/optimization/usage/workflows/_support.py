"""Shared, non-workflow infrastructure for Optimization workflow examples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import MarketDataset, get_market_data
from app.services.optimization.search import SearchRequest
from app.utils import canonical_digest
from tests.data.usage.workflows._support import market_request
from tests.optimization.unit.test_search_contracts import search_request

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"


def live_market_dataset() -> MarketDataset:
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return MarketDataset.model_validate_json(
            Path(captured).read_text(encoding="utf-8")
        )
    return get_market_data(market_request("bars", timeframe="M1", limit=20))


def live_search_request(dataset: MarketDataset) -> SearchRequest:
    """Bind one bounded search request to genuine Data provenance."""
    request = search_request()
    context = request.execution_context.model_copy(
        update={
            "data_ref": f"mt5:{dataset.symbol}:{dataset.timeframe}",
            "data_hash": canonical_digest(
                dataset.model_dump(mode="python", warnings=False)
            ),
            "symbol": dataset.symbol,
            "timeframe": dataset.timeframe,
            "start": dataset.start,
            "end": dataset.end,
        }
    )
    return request.model_copy(update={"execution_context": context})


__all__ = ["_DATASET_ENV", "live_market_dataset", "live_search_request"]
