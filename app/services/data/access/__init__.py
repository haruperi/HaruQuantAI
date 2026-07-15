"""Market evidence read-orchestration API."""

from __future__ import annotations

from app.services.data.access.context import (
    MarketContextProvider,
    get_market_context_evidence,
)
from app.services.data.access.fx import FXRateProvider, get_fx_conversion_evidence
from app.services.data.access.historical import fetch_market_dataset
from app.services.data.access.reference import (
    discover_symbols,
    fetch_symbol_metadata,
    inspect_availability,
)
from app.services.data.access.sessions import (
    fetch_historical_volume,
    get_current_schedule,
)

__all__ = [
    "FXRateProvider",
    "MarketContextProvider",
    "discover_symbols",
    "fetch_historical_volume",
    "fetch_market_dataset",
    "fetch_symbol_metadata",
    "get_current_schedule",
    "get_fx_conversion_evidence",
    "get_market_context_evidence",
    "inspect_availability",
]
