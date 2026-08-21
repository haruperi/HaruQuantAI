"""Tests for DiskStorageEngine CRUD operations, listing, and partitioning."""

from pathlib import Path

import pytest

from app.services.system.storage.engine import DiskStorageEngine


@pytest.mark.asyncio
async def test_disk_storage_crud(tmp_path: Path) -> None:
    """Test basic get, set, and delete operations."""
    engine = DiskStorageEngine(tmp_path)

    # 1. Non-existent key returns None
    assert await engine.get("missing_key") is None
    assert await engine.delete("missing_key") is False

    # 2. Set key
    await engine.set("user_settings", b'{"theme": "dark"}')
    assert await engine.get("user_settings") == b'{"theme": "dark"}'

    # 3. Overwrite key
    await engine.set("user_settings", b'{"theme": "light"}')
    assert await engine.get("user_settings") == b'{"theme": "light"}'

    # 4. List keys
    keys = await engine.list_keys()
    assert keys == ("user_settings",)

    # 5. Delete key
    assert await engine.delete("user_settings") is True
    assert await engine.get("user_settings") is None
    assert await engine.list_keys() == ()


@pytest.mark.asyncio
async def test_disk_storage_partitioning(tmp_path: Path) -> None:
    """Test that partitioned storage engines isolate keys into subdirectories."""
    root_engine = DiskStorageEngine(tmp_path)

    data_store = root_engine.partition("data.historical_bars")
    risk_store = root_engine.partition("risk.limits")

    await data_store.set("EURUSD_M1", b"bar_data_bytes")
    await risk_store.set("EURUSD_M1", b"risk_rule_bytes")

    # Data partitions have separate values under the same key name
    assert await data_store.get("EURUSD_M1") == b"bar_data_bytes"
    assert await risk_store.get("EURUSD_M1") == b"risk_rule_bytes"

    # Root engine does not directly list subpartition keys in its top level
    assert await root_engine.get("EURUSD_M1") is None
    assert await data_store.list_keys() == ("EURUSD_M1",)
    assert await risk_store.list_keys() == ("EURUSD_M1",)


@pytest.mark.asyncio
async def test_disk_storage_list_prefix(tmp_path: Path) -> None:
    """Test prefix filtering when listing stored keys."""
    engine = DiskStorageEngine(tmp_path)

    await engine.set("tick_EURUSD", b"1")
    await engine.set("tick_GBPUSD", b"2")
    await engine.set("bar_EURUSD", b"3")

    ticks = await engine.list_keys(prefix="tick_")
    assert ticks == ("tick_EURUSD", "tick_GBPUSD")

    bars = await engine.list_keys(prefix="bar_")
    assert bars == ("bar_EURUSD",)
