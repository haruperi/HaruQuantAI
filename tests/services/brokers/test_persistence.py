"""Tests for Brokers domain persistence (brokers.v1)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.brokers import (
    BROKER_PERSISTENCE,
    BrokerConnectionConfig,
    BrokerError,
    BrokerProfile,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.brokers import (
    BrokersPersistenceService,
    feature,
)
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)


def _setup_service(tmp_path: Path) -> BrokersPersistenceService:
    db_file = tmp_path / "test_brokers.db"
    db = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    return BrokersPersistenceService(db)


def test_preseeded_system_brokers(tmp_path: Path) -> None:
    """Verify FR-BROKERS-SYSTEM_PROTECTION: all 11 StrategyQuant X system brokers are pre-seeded correctly."""

    async def _test() -> None:
        service = _setup_service(tmp_path)
        profiles = await service.list_profiles()

        assert len(profiles) >= 11
        names = {p.name for p in profiles}
        expected = {
            "XTB",
            "RoboForex",
            "Dukascopy",
            "Darwinex",
            "ICMarkets",
            "Pepperstone",
            "OANDA",
            "FTMO",
            "The5ers",
            "Monevis",
            "Darwinex Zero",
        }
        assert expected.issubset(names)

        robo = await service.get_profile_by_name("RoboForex")
        assert robo is not None
        assert robo.is_system is True
        assert robo.postfix == "_roboforex"
        assert robo.server_timezone == "EET"
        assert robo.mt_use is True

    asyncio.run(_test())


def test_custom_profile_lifecycle(tmp_path: Path) -> None:
    """Verify creating, querying, updating, and deleting custom profiles."""

    async def _test() -> None:
        service = _setup_service(tmp_path)

        custom = BrokerProfile(
            id=0,
            name="CustomBroker",
            is_system=False,
            description="My custom broker",
            stockpicker_use=False,
            mt_use=True,
            server_timezone="UTC+3",
            postfix=".custom",
        )
        saved = await service.save_profile(custom)
        assert saved.id > 0
        assert saved.name == "CustomBroker"
        assert saved.postfix == ".custom"

        # Cannot delete a system broker
        assert await service.delete_profile(1) is False

        # Can delete custom broker
        assert await service.delete_profile(saved.id) is True
        assert await service.get_profile(saved.id) is None

    asyncio.run(_test())


def test_cannot_downgrade_system_broker(tmp_path: Path) -> None:
    """Ensure system brokers cannot have system flag cleared."""

    async def _test() -> None:
        service = _setup_service(tmp_path)
        xtb = await service.get_profile(1)
        assert xtb is not None

        downgraded = BrokerProfile(
            id=xtb.id,
            name=xtb.name,
            is_system=False,  # Attempt downgrade
            description="Modified",
        )
        with pytest.raises(BrokerError, match="Cannot downgrade"):
            await service.save_profile(downgraded)

    asyncio.run(_test())


def test_connection_config_roundtrip(tmp_path: Path) -> None:
    """Verify FR-BROKERS-CREDENTIAL_ISOLATION: connection configs store secret references without plaintext."""

    async def _test() -> None:
        service = _setup_service(tmp_path)

        config = BrokerConnectionConfig(
            connection_id="conn-mt5-01",
            broker_id=2,
            provider_name="mt5",
            environment="demo",
            endpoint="127.0.0.1:443",
            secret_key_ref="sec_broker_roboforex_demo",  # pragma: allowlist secret
            timeout_s=15.0,
            rate_limit_rps=20.0,
            settings={"server": "RoboForex-Demo", "portable": True},
        )
        await service.save_connection_config(config)

        retrieved = await service.get_connection_config("conn-mt5-01")
        assert retrieved is not None
        assert retrieved.connection_id == "conn-mt5-01"
        assert (
            retrieved.secret_key_ref
            == "sec_broker_roboforex_demo"  # pragma: allowlist secret
        )
        assert retrieved.settings["server"] == "RoboForex-Demo"
        assert retrieved.settings["portable"] is True

    asyncio.run(_test())


def test_feature_runtime_lifecycle(tmp_path: Path) -> None:
    """Verify BrokersPersistenceFeature wires correctly into the kernel Runtime."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_brokers.db"

        def db_factory() -> DatabaseFeature:
            return DatabaseFeature(DatabaseConfig(database_path=db_file))

        runtime = Runtime(
            (
                db_factory,
                feature,
            )
        )

        async with runtime:
            svc = runtime.get(BROKER_PERSISTENCE)
            assert svc is not None
            profiles = await svc.list_profiles()
            assert len(profiles) >= 11

    asyncio.run(_test())
