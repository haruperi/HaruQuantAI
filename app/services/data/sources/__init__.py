"""Canonical Data domain sources surface exports."""

from __future__ import annotations

from app.services.data.sources.composition import (
    close_data_provider_sessions,
    ensure_source,
    ensure_source_access,
    list_composable_sources,
)
from app.services.data.sources.policy import (
    compute_source_trust_score,
    evaluate_source_policy,
    promote_source,
    register_source_policy,
)
from app.services.data.sources.protocol import MarketDataSource
from app.services.data.sources.registry import (
    get_source_descriptor,
    list_registered_sources,
    register_source,
    resolve_source,
)

__all__ = [
    "MarketDataSource",
    "close_data_provider_sessions",
    "compute_source_trust_score",
    "ensure_source",
    "ensure_source_access",
    "evaluate_source_policy",
    "get_source_descriptor",
    "list_composable_sources",
    "list_registered_sources",
    "promote_source",
    "register_source",
    "register_source_policy",
    "resolve_source",
]
