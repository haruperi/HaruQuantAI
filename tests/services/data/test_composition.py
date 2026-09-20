"""Composition, runtime topology, and feature removal tests for the Data domain.

Feature:
    D-DATA Composition & Topology (FIP-01, FIP-02)

Requirements Verified:
    * All 9 domain features assemble cleanly into a topological Runtime.
    * Named profile 'data' boots deterministically via get_features(profile='data').
    * Physical removal of optional features allows the runtime to start without errors.
    * Missing mandatory dependencies fail fast with CapabilityUnavailableError.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.data import (
    DATA_DATASETS,
    DATA_IMPORTS_EXPORTS,
    DATA_INSTRUMENTS,
    DATA_MARKET_DATA,
    DATA_PERSISTENCE,
    DATA_QUALITY,
    DATA_RESAMPLING,
    DATA_SESSIONS,
    DATA_SYNC,
    DATA_UNIVERSES,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.registry import get_features
from app.services.data.datasets import feature as datasets_feature
from app.services.data.imports_exports import feature as imports_exports_feature
from app.services.data.instruments import feature as instruments_feature
from app.services.data.market_data import feature as market_data_feature
from app.services.data.quality import feature as quality_feature
from app.services.data.resampling import feature as resampling_feature
from app.services.data.sessions import feature as sessions_feature
from app.services.data.universes import feature as universes_feature
from app.services.persistence.data import feature as data_persistence_feature
from app.services.persistence.database import DatabaseConfig, DatabaseFeature


def test_data_full_composition(tmp_path: Path) -> None:
    """Verify that all data domain features assemble and start cleanly in Runtime."""
    db_path = tmp_path / "data_full_comp.db"

    factories = (
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
        data_persistence_feature,
        instruments_feature,
        sessions_feature,
        datasets_feature,
        quality_feature,
        imports_exports_feature,
        resampling_feature,
        universes_feature,
        market_data_feature,
    )

    async def _run() -> None:
        runtime = Runtime(factories)
        async with runtime:
            assert runtime.get(DATA_PERSISTENCE) is not None
            assert runtime.get(DATA_INSTRUMENTS) is not None
            assert runtime.get(DATA_SESSIONS) is not None
            assert runtime.get(DATA_DATASETS) is not None
            assert runtime.get(DATA_QUALITY) is not None
            assert runtime.get(DATA_IMPORTS_EXPORTS) is not None
            assert runtime.get(DATA_RESAMPLING) is not None
            assert runtime.get(DATA_UNIVERSES) is not None
            assert runtime.get(DATA_MARKET_DATA) is not None
            assert runtime.get(DATA_SYNC) is not None

    asyncio.run(_run())


def test_data_profile_from_registry(tmp_path: Path) -> None:
    """Verify that get_features(profile='data') boots all data capabilities."""
    factories, enabled_names = get_features(profile="data")
    assert enabled_names is not None
    assert "data.instruments" in enabled_names

    async def _run() -> None:
        runtime = Runtime(factories, enabled=enabled_names)
        async with runtime:
            assert runtime.get(DATA_INSTRUMENTS) is not None
            assert runtime.get(DATA_SESSIONS) is not None
            assert runtime.get(DATA_DATASETS) is not None

    asyncio.run(_run())


def test_data_feature_removal(tmp_path: Path) -> None:
    """Verify physical removal of optional features without breaking the runtime."""
    db_path = tmp_path / "data_partial.db"

    # Assemble WITHOUT market_data and WITHOUT quality
    factories = (
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
        data_persistence_feature,
        instruments_feature,
        sessions_feature,
        datasets_feature,
        resampling_feature,
        universes_feature,
    )

    async def _run() -> None:
        runtime = Runtime(factories)
        async with runtime:
            assert runtime.get(DATA_INSTRUMENTS) is not None
            assert runtime.get(DATA_SESSIONS) is not None
            assert runtime.get(DATA_DATASETS) is not None
            assert runtime.get(DATA_RESAMPLING) is not None
            assert runtime.get(DATA_UNIVERSES) is not None
            # Verify removed capabilities are not present
            assert runtime.get(DATA_MARKET_DATA) is None
            assert runtime.get(DATA_QUALITY) is None

    asyncio.run(_run())


def test_dependency_loss_fail_closed(tmp_path: Path) -> None:
    """Verify runtime fails closed when required dependency is missing."""
    # instruments_feature requires DATA_PERSISTENCE; omitting data_persistence_feature
    factories = (instruments_feature,)

    async def _run() -> None:
        runtime = Runtime(factories)
        with pytest.raises(CapabilityUnavailableError):
            async with runtime:
                pass

    asyncio.run(_run())
