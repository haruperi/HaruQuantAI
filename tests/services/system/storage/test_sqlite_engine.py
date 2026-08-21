"""Unit tests for SqliteStorageEngine CRUD, partitioning, and concurrency."""

import asyncio
from pathlib import Path

import pytest

from app.services.system.storage.sqlite_engine import SqliteStorageEngine


@pytest.mark.asyncio
async def test_sqlite_storage_crud(tmp_path: Path) -> None:
    """Test basic get, set, overwrite, and delete operations."""
    db_file = tmp_path / "haruquantai.db"
    engine = SqliteStorageEngine(db_file)

    # 1. Non-existent key
    assert await engine.get("missing_key") is None
    assert await engine.delete("missing_key") is False

    # 2. Set key
    await engine.set("theme", b"dark_mode")
    assert await engine.get("theme") == b"dark_mode"

    # 3. Overwrite key (upsert)
    await engine.set("theme", b"light_mode")
    assert await engine.get("theme") == b"light_mode"

    # 4. List keys
    keys = await engine.list_keys()
    assert keys == ("theme",)

    # 5. Delete key
    assert await engine.delete("theme") is True
    assert await engine.get("theme") is None
    assert await engine.list_keys() == ()


@pytest.mark.asyncio
async def test_sqlite_storage_partitions(tmp_path: Path) -> None:
    """Test that separate partitions isolate keys with identical names."""
    db_file = tmp_path / "haruquantai.db"
    root_engine = SqliteStorageEngine(db_file)

    data_store = root_engine.partition("data.historical_bars")
    risk_store = root_engine.partition("risk.limits")

    await data_store.set("EURUSD", b"historical_bar_data")
    await risk_store.set("EURUSD", b"risk_rule_data")

    # Values in separate namespaces do not conflict
    assert await data_store.get("EURUSD") == b"historical_bar_data"
    assert await risk_store.get("EURUSD") == b"risk_rule_data"
    assert await root_engine.get("EURUSD") is None

    assert await data_store.list_keys() == ("EURUSD",)
    assert await risk_store.list_keys() == ("EURUSD",)


@pytest.mark.asyncio
async def test_sqlite_storage_prefix_filtering(tmp_path: Path) -> None:
    """Test list_keys with prefix filtering in SQLite."""
    db_file = tmp_path / "haruquantai.db"
    engine = SqliteStorageEngine(db_file)

    await engine.set("symbol_EURUSD", b"1")
    await engine.set("symbol_GBPUSD", b"2")
    await engine.set("user_admin", b"3")

    symbols = await engine.list_keys(prefix="symbol_")
    assert symbols == ("symbol_EURUSD", "symbol_GBPUSD")

    users = await engine.list_keys(prefix="user_")
    assert users == ("user_admin",)


@pytest.mark.asyncio
async def test_sqlite_storage_concurrency(tmp_path: Path) -> None:
    """Test concurrent reads and writes with SQLite WAL mode."""
    db_file = tmp_path / "haruquantai.db"
    engine = SqliteStorageEngine(db_file)

    async def write_item(idx: int) -> None:
        await engine.set(f"key_{idx:03d}", f"val_{idx}".encode())

    # Concurrent 30 writes
    tasks = [write_item(i) for i in range(30)]
    await asyncio.gather(*tasks)

    keys = await engine.list_keys()
    assert len(keys) == 30
    assert await engine.get("key_015") == b"val_15"
