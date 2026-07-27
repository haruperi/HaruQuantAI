"""Shared, non-workflow infrastructure for Research workflow examples."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import MarketDataset, get_market_data
from app.services.research import (
    CleaningConfig,
    EnrichmentConfig,
    PreparedDataset,
    ResearchResourceLimits,
)
from app.services.research.data import prepare_research_dataset
from tests.data.usage.workflows._support import market_request

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"


def live_market_dataset() -> MarketDataset:
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return MarketDataset.model_validate_json(
            Path(captured).read_text(encoding="utf-8")
        )
    return get_market_data(market_request("bars", timeframe="M1", limit=40))


def limits() -> ResearchResourceLimits:
    """Return bounded Research resource limits."""
    return ResearchResourceLimits(500_000, 600.0, 52_428_800)


def prepared_dataset() -> PreparedDataset:
    """Prepare genuine MT5 evidence through the canonical Research boundary."""
    return prepare_research_dataset(
        live_market_dataset(),
        cleaning=CleaningConfig("UTC", "error", "none", "keep_warn", "error"),
        enrichment=EnrichmentConfig("EURUSD", True, True, False, True),
        limits=limits(),
    )


__all__ = [
    "_DATASET_ENV",
    "limits",
    "live_market_dataset",
    "prepared_dataset",
]
