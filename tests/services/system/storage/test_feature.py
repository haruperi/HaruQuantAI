"""Tests for StorageFeature lifecycle and capability provision."""

from pathlib import Path

import pytest

from app.contracts.system.storage import SYSTEM_STORAGE, StorageEngine
from app.kernel.context import DefaultFeatureContext
from app.kernel.scope import FeatureScope
from app.services.system.storage.config import StorageConfig
from app.services.system.storage.feature import StorageFeature, create_feature


@pytest.mark.asyncio
async def test_storage_feature_mount_sqlite(tmp_path: Path) -> None:
    """Test mounting StorageFeature registers SQLite storage engine."""
    feature = create_feature()
    assert isinstance(feature, StorageFeature)
    assert feature.spec.feature_id == "FEAT-SYS-PERSIST_STORAGE"

    scope = FeatureScope(owner_id=feature.spec.feature_id)
    provided: dict[object, object] = {}

    def registrar(cap: object, impl: object, _scope: FeatureScope) -> None:
        provided[cap] = impl

    ctx = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        provider_registrar=registrar,
    )

    db_file = tmp_path / "haruquantai.db"
    config = StorageConfig(db_path=str(db_file), driver="sqlite")
    await feature.mount(ctx, config)

    assert SYSTEM_STORAGE in provided
    engine = provided[SYSTEM_STORAGE]
    assert isinstance(engine, StorageEngine)

    await engine.set("test_key", b"test_sqlite_payload")
    assert await engine.get("test_key") == b"test_sqlite_payload"

    # Verify db file was created on disk
    assert db_file.is_file()

    await scope.close()


@pytest.mark.asyncio
async def test_storage_feature_mount_disk(tmp_path: Path) -> None:
    """Test mounting StorageFeature with disk driver."""
    feature = create_feature()
    scope = FeatureScope(owner_id=feature.spec.feature_id)
    provided: dict[object, object] = {}

    def registrar(cap: object, impl: object, _scope: FeatureScope) -> None:
        provided[cap] = impl

    ctx = DefaultFeatureContext(
        spec=feature.spec,
        scope=scope,
        provider_registrar=registrar,
    )

    config = StorageConfig(base_path=str(tmp_path), driver="disk")
    await feature.mount(ctx, config)

    assert SYSTEM_STORAGE in provided
    engine = provided[SYSTEM_STORAGE]
    await engine.set("disk_key", b"disk_payload")
    assert await engine.get("disk_key") == b"disk_payload"

    await scope.close()
