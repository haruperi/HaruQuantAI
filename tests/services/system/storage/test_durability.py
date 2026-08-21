"""Tests verifying durable SQLite state retention across unmount and remount cycles."""

from pathlib import Path

import pytest

from app.composition.discovery import DiscoveryResult, FeatureDiscoverer
from app.composition.engine import CompositionEngine
from app.contracts.system.storage import SYSTEM_STORAGE
from app.services.system.storage.feature import StorageFeature


@pytest.mark.asyncio
async def test_state_retained_across_unmount_and_remount(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that stored SQLite data survives feature unmount and remount."""
    db_file = tmp_path / "db" / "haruquantai.db"

    storage_feat = StorageFeature()
    engine = CompositionEngine()
    monkeypatch.setattr(
        FeatureDiscoverer,
        "discover",
        lambda _self: DiscoveryResult(
            discovered={
                "FEAT-SYS-PERSIST_STORAGE": storage_feat,
            }
        ),
    )

    # 1. Mount storage feature with SQLite driver
    toml_cfg_mount = f"""
    [profile]
    name = "research"

    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = true
    db_path = "{db_file.as_posix()}"
    driver = "sqlite"
    """
    report = await engine.load_and_reconcile_toml(toml_cfg_mount)
    assert "FEAT-SYS-PERSIST_STORAGE" in report.started

    # 2. Get storage instance and write data into a feature namespace partition
    storage = engine.registry.resolve(SYSTEM_STORAGE)
    assert storage is not None

    data_partition = storage.partition("data.historical_bars")
    await data_partition.set("EURUSD_D1", b"persisted_historical_bars_binary")

    # Verify write
    assert await data_partition.get("EURUSD_D1") == b"persisted_historical_bars_binary"
    assert db_file.is_file()

    # 3. Unmount storage feature
    toml_cfg_unmount = """
    [profile]
    name = "research"

    [features.FEAT-SYS-PERSIST_STORAGE]
    enabled = false
    """
    report_unmount = await engine.load_and_reconcile_toml(toml_cfg_unmount)
    assert "FEAT-SYS-PERSIST_STORAGE" in report_unmount.stopped
    assert engine.registry.resolve(SYSTEM_STORAGE) is None

    # 4. Remount storage feature
    report_remount = await engine.load_and_reconcile_toml(toml_cfg_mount)
    assert "FEAT-SYS-PERSIST_STORAGE" in report_remount.started

    # 5. Verify data in partition was retained across unmount in SQLite DB
    storage_remounted = engine.registry.resolve(SYSTEM_STORAGE)
    assert storage_remounted is not None

    data_partition_remounted = storage_remounted.partition("data.historical_bars")
    persisted_val = await data_partition_remounted.get("EURUSD_D1")
    assert persisted_val == b"persisted_historical_bars_binary"

    await engine.reconciler.stop_all()
