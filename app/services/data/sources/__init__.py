"""Canonical Data domain sources surface exports."""

from __future__ import annotations

from app.services.data.sources.broker import get_account_state_snapshot
from app.services.data.sources.policy import evaluate_source_policy, promote_source
from app.services.data.sources.protocol import MarketDataSource
from app.services.data.sources.registry import (
    get_source_descriptor,
    list_registered_sources,
    register_source,
    resolve_source,
)

__all__ = [
    "MarketDataSource",
    "evaluate_source_policy",
    "get_account_state_snapshot",
    "get_source_descriptor",
    "list_registered_sources",
    "promote_source",
    "register_source",
    "resolve_source",
]
