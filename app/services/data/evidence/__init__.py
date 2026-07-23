"""Normalized cross-domain evidence.

Three capabilities that turn provider reads into contracts other domains govern on:
market context for Risk, FX conversion paths for Risk, Simulation, Analytics and
Portfolio, and read-only account state.

They were split across ``gateway/`` and ``sources/`` for no reason other than where
their inputs came from. What they share is more important than what fetches them: each
normalizes evidence, states missingness explicitly, and fails closed rather than
substituting a plausible value. None of them decides anything — interpretation belongs
to the consuming domain.

Every provider and adapter is injected by the caller. This package opens no connection
and resolves no credential.
"""

from app.services.data.evidence.account_state import get_account_state_snapshot
from app.services.data.evidence.fx_conversion import (
    FXRateProvider,
    get_fx_conversion_evidence,
)
from app.services.data.evidence.market_context import (
    MarketContextProvider,
    get_market_context_evidence,
)

__all__ = [
    "FXRateProvider",
    "MarketContextProvider",
    "get_account_state_snapshot",
    "get_fx_conversion_evidence",
    "get_market_context_evidence",
]
