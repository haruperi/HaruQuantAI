"""Composition, physical removal, and dependency loss tests for the Brokers domain.

Feature:
    D-BROKERS Composition & Topology (FIP-01, FIP-02)

Requirements Verified:
    * All 12 domain features assemble cleanly into a topological Runtime.
    * Physical removal of optional features (reconciliation, ctrader) allows the
      runtime to start without errors, proving loose coupling.
    * Dependency loss (removing required BROKER_PERSISTENCE from BROKER_CATALOG)
      fails closed at bootstrapper startup before side-effecting code executes.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.brokers import (
    BROKER_CATALOG,
    BROKER_CRYPTO,
    BROKER_CTRADER,
    BROKER_DARWINEX,
    BROKER_DUKASCOPY,
    BROKER_EQUITY,
    BROKER_FENCING,
    BROKER_FUTURES,
    BROKER_MT5,
    BROKER_PERSISTENCE,
    BROKER_RECONCILIATION,
    BROKER_YAHOO,
)
from app.kernel.bootstrapper import Runtime
from app.kernel.capability import CapabilityUnavailableError
from app.services.brokers.catalog import feature as catalog_feature
from app.services.brokers.crypto import feature as crypto_feature
from app.services.brokers.ctrader import feature as ctrader_feature
from app.services.brokers.darwinex import feature as darwinex_feature
from app.services.brokers.dukascopy import feature as dukascopy_feature
from app.services.brokers.equity import feature as equity_feature
from app.services.brokers.futures import feature as futures_feature
from app.services.brokers.isolation_fencing import feature as fencing_feature
from app.services.brokers.mt5 import feature as mt5_feature
from app.services.brokers.reconciliation import feature as reconciliation_feature
from app.services.brokers.yahoo import feature as yahoo_feature
from app.services.persistence.brokers import feature as persistence_feature
from app.services.persistence.database import DatabaseConfig, DatabaseFeature


def test_brokers_full_composition(tmp_path: Path) -> None:
    """Verify that all 12 broker features assemble and start cleanly."""
    db_path = tmp_path / "brokers_full_comp.db"

    factories = (
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
        persistence_feature,
        catalog_feature,
        dukascopy_feature,
        equity_feature,
        futures_feature,
        darwinex_feature,
        crypto_feature,
        yahoo_feature,
        mt5_feature,
        ctrader_feature,
        fencing_feature,
        reconciliation_feature,
    )

    async def _run() -> None:
        runtime = Runtime(factories)
        async with runtime:
            assert runtime.get(BROKER_PERSISTENCE) is not None
            assert runtime.get(BROKER_CATALOG) is not None
            assert runtime.get(BROKER_DUKASCOPY) is not None
            assert runtime.get(BROKER_EQUITY) is not None
            assert runtime.get(BROKER_FUTURES) is not None
            assert runtime.get(BROKER_DARWINEX) is not None
            assert runtime.get(BROKER_CRYPTO) is not None
            assert runtime.get(BROKER_YAHOO) is not None
            assert runtime.get(BROKER_MT5) is not None
            assert runtime.get(BROKER_CTRADER) is not None
            assert runtime.get(BROKER_FENCING) is not None
            assert runtime.get(BROKER_RECONCILIATION) is not None

    asyncio.run(_run())


def test_brokers_physical_removal(tmp_path: Path) -> None:
    """Verify physical removal of optional features without breaking the runtime."""
    db_path = tmp_path / "brokers_partial_comp.db"

    # Assemble WITHOUT reconciliation and WITHOUT ctrader
    factories = (
        lambda: DatabaseFeature(DatabaseConfig(database_path=db_path)),
        persistence_feature,
        catalog_feature,
        dukascopy_feature,
        fencing_feature,
    )

    async def _run() -> None:
        runtime = Runtime(factories)
        async with runtime:
            assert runtime.get(BROKER_CATALOG) is not None
            assert runtime.get(BROKER_DUKASCOPY) is not None
            assert runtime.get(BROKER_FENCING) is not None
            # Removed capabilities return None
            assert runtime.get(BROKER_RECONCILIATION) is None
            assert runtime.get(BROKER_CTRADER) is None

    asyncio.run(_run())


def test_brokers_dependency_loss_fail_closed() -> None:
    """Verify fail-closed graph closure when a mandatory dependency is missing."""
    # catalog requires BROKER_PERSISTENCE; omitting persistence raises CapabilityUnavailableError
    factories = (catalog_feature,)

    async def _run() -> None:
        runtime = Runtime(factories)
        with pytest.raises(CapabilityUnavailableError) as exc_info:
            async with runtime:
                pass
        assert "brokers.catalog" in str(exc_info.value)
        assert "persistence.brokers" in str(exc_info.value)

    asyncio.run(_run())
