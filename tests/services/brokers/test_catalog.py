"""Tests for FEAT-BROKERS-CATALOG (app/services/brokers/catalog.py)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.contracts.brokers import (
    BROKER_CATALOG,
    BrokerProfile,
)
from app.kernel.bootstrapper import Runtime
from app.services.brokers.catalog import (
    BrokerCatalog,
    feature,
)
from app.services.persistence.brokers import (
    BrokersPersistenceService,
)
from app.services.persistence.brokers import (
    feature as persistence_feature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)


def _setup_catalog(tmp_path: Path) -> BrokerCatalog:
    db_file = tmp_path / "test_cat.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    persist = BrokersPersistenceService(db)
    return BrokerCatalog(persist)


def test_symbol_postfix_resolution_and_reversibility(tmp_path: Path) -> None:
    """Verify FR-BROKERS-SYMBOL_TRANSLATION: Reversible symbol translation."""

    async def _test() -> None:
        cat = _setup_catalog(tmp_path)
        await cat._refresh_cache()

        # RoboForex has postfix '_roboforex'
        robo = await cat.get_profile_by_name("RoboForex")
        assert robo is not None
        assert robo.postfix == "_roboforex"

        # Resolve forward
        resolved = cat.resolve_broker_symbol("EURUSD", robo.id)
        assert resolved == "EURUSD_roboforex"

        # Idempotent forward
        assert (
            cat.resolve_broker_symbol("EURUSD_roboforex", robo.id) == "EURUSD_roboforex"
        )

        # Reverse backward
        stripped = cat.strip_broker_postfix(resolved, robo.id)
        assert stripped == "EURUSD"

        # Broker with no postfix (e.g. XTB)
        xtb = await cat.get_profile_by_name("XTB")
        assert xtb is not None
        assert cat.resolve_broker_symbol("EURUSD", xtb.id) == "EURUSD"
        assert cat.strip_broker_postfix("EURUSD", xtb.id) == "EURUSD"

    asyncio.run(_test())


def test_broker_timezone_resolution(tmp_path: Path) -> None:
    """Verify FR-BROKERS-SERVER_TIMEZONE: Server timezone resolution."""

    async def _test() -> None:
        cat = _setup_catalog(tmp_path)
        await cat._refresh_cache()

        robo = await cat.get_profile_by_name("RoboForex")
        assert robo is not None
        assert cat.get_broker_timezone(robo.id) == "EET"

        the5ers = await cat.get_profile_by_name("The5ers")
        assert the5ers is not None
        assert cat.get_broker_timezone(the5ers.id) == "Asia/Jerusalem"

    asyncio.run(_test())


def test_system_profile_protection(tmp_path: Path) -> None:
    """Verify system profiles cannot be deleted through catalog."""

    async def _test() -> None:
        cat = _setup_catalog(tmp_path)
        await cat._refresh_cache()

        # Try to delete Dukascopy (id=3)
        assert await cat.delete_profile(3) is False
        assert await cat.get_profile(3) is not None

        # Create and delete custom profile
        custom = BrokerProfile(
            id=0,
            name="MyDemoBroker",
            is_system=False,
            postfix=".demo",
        )
        saved = await cat.create_profile(custom)
        assert saved.id > 0
        assert await cat.delete_profile(saved.id) is True
        assert await cat.get_profile(saved.id) is None

    asyncio.run(_test())


def test_catalog_runtime_wiring(tmp_path: Path) -> None:
    """Verify runtime composition and capability publication."""

    async def _test() -> None:
        db_file = tmp_path / "cat_runtime.db"

        def db_f() -> DatabaseFeature:
            return DatabaseFeature(DatabaseConfig(database_path=db_file))

        runtime = Runtime(
            (
                db_f,
                persistence_feature,
                feature,
            )
        )

        async with runtime:
            catalog = runtime.get(BROKER_CATALOG)
            assert catalog is not None
            profiles = await catalog.get_profiles()
            assert len(profiles) >= 11

    asyncio.run(_test())
