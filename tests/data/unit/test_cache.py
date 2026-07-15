"""Unit tests for cache persistence operations."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from app.services.data.contracts import (
    CACHE_CLEAR_MAX_ENTRIES,
    CACHE_TTL_MAX_SECONDS,
    CacheClearRequest,
    CacheReadRequest,
    CacheWriteRequest,
    DataError,
)
from app.services.data.storage.cache import get_cache_entry, put_cache_entry

from tests.data.helpers import make_dataset


def test_cache_requests_reject_unbounded_work() -> None:
    """Reject unsafe cache TTL and clear bounds before persistence access."""
    request_id = "req-f1d43d6cdf224820bc9c7ec74e69952972cda2fd582048189aeaf32dfd75d18b"
    with pytest.raises(DataError) as ttl_error:
        CacheWriteRequest(
            key="unsafe-ttl",
            dataset=make_dataset(),
            ttl_seconds=CACHE_TTL_MAX_SECONDS + 1,
            source_revision="rev-1",
            raw_data_hash="hash-1",
            request_id=request_id,
        )
    assert ttl_error.value.code == "INVALID_INPUT"

    with pytest.raises(DataError) as clear_error:
        CacheClearRequest(
            namespace="data",
            dry_run=True,
            max_entries=CACHE_CLEAR_MAX_ENTRIES + 1,
            request_id=request_id,
        )
    assert clear_error.value.code == "INVALID_INPUT"


def _configure_cache(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Helper to configure database and data directories."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1.0")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "10")
    from app.services.data.storage.migrations import run_data_migrations

    run_data_migrations(
        "req-60d56de3ff8bb20750e936377422e90f785e5ecfef35c15300af6cade7ff5e9d"
    )


def test_put_and_get_cache_entry_hit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify standard active cache write and read hit."""
    _configure_cache(monkeypatch, tmp_path)

    dataset = make_dataset()
    write_req = CacheWriteRequest(
        key="cache-key-1",
        dataset=dataset,
        ttl_seconds=60,
        source_revision="rev-1",
        raw_data_hash="hash-1",
        request_id="req-2ae03bafcccbab9ee63678442e848f30e0fa769b9620e3bc932ef55a253447f2",
    )

    result = put_cache_entry(write_req)
    assert result.written
    assert result.key == "cache-key-1"

    read_req = CacheReadRequest(
        key="cache-key-1",
        allow_stale=False,
        request_id="req-c7756479b1fb11e0f56ab97a6b8a728e63123618e2f2f0216ae0b427103f13c6",
    )

    entry = get_cache_entry(read_req)
    assert entry is not None
    assert entry.key == "cache-key-1"
    assert entry.source_revision == "rev-1"
    assert entry.dataset.cache_status == "hit"


def test_cache_miss_when_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify cache read miss for non-existent key."""
    _configure_cache(monkeypatch, tmp_path)

    read_req = CacheReadRequest(
        key="missing-key",
        allow_stale=False,
        request_id="req-44515035a1d649bff8d8bc34f5853053646eb028920cb1d9c22b7286e21ed00a",
    )

    entry = get_cache_entry(read_req)
    assert entry is None


def test_cache_expiration_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify that expired cache entries are handled based on stale policy."""
    _configure_cache(monkeypatch, tmp_path)

    dataset = make_dataset()
    # Write with immediate expiration
    write_req = CacheWriteRequest(
        key="cache-key-expire",
        dataset=dataset,
        ttl_seconds=1,
        source_revision="rev-1",
        raw_data_hash="hash-1",
        request_id="req-d28c2b51880bae5db4771a0284035b4dafaace830c3ddc87098e3f98636d3444",
    )
    put_cache_entry(write_req)

    # Wait for entry to expire
    time.sleep(1.1)

    # 1. Reading with allow_stale=False -> Miss
    read_req_miss = CacheReadRequest(
        key="cache-key-expire",
        allow_stale=False,
        request_id="req-b0d723e3ba8d92fec6d6cdb73d9b86e95b5be57a8e04efe5524a241b6c7d5d03",
    )
    entry_miss = get_cache_entry(read_req_miss)
    assert entry_miss is None

    # 2. Reading with allow_stale=True -> Hit with warning status
    read_req_stale = CacheReadRequest(
        key="cache-key-expire",
        allow_stale=True,
        request_id="req-137083e33c90538abb67fc8925817bf77ede5ab669e2ea39bfc4987e28ebcdae",
    )
    entry_stale = get_cache_entry(read_req_stale)
    assert entry_stale is not None
    assert entry_stale.dataset.cache_status == "stale_warning"


def test_cache_write_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify database write error mapping in put_cache_entry."""
    _configure_cache(monkeypatch, tmp_path)

    import app.services.data.storage.cache as cache_mod
    from app.services.data.contracts.errors import DataError

    def mock_execute(*args, **kwargs):
        raise ValueError("Mock DB write error")

    monkeypatch.setattr(cache_mod, "execute_transaction", mock_execute)

    dataset = make_dataset()
    write_req = CacheWriteRequest(
        key="error-key",
        dataset=dataset,
        ttl_seconds=60,
        source_revision="rev-1",
        raw_data_hash="hash-1",
        request_id="req-21a1fad252673e68d97261e2fa7a19009e3ae1c4e8ea30c42dac0da63a6fcdaa",
    )

    with pytest.raises(DataError) as captured:
        put_cache_entry(write_req)
    assert captured.value.code == "DB_WRITE_FAILED"


def test_cache_read_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify database query error mapping in get_cache_entry."""
    _configure_cache(monkeypatch, tmp_path)

    import app.services.data.storage.cache as cache_mod
    from app.services.data.contracts.errors import DataError

    def mock_execute(*args, **kwargs):
        raise ValueError("Mock DB read error")

    monkeypatch.setattr(cache_mod, "execute_transaction", mock_execute)

    read_req = CacheReadRequest(
        key="error-key",
        allow_stale=False,
        request_id="req-55021baa8a82e4df27c6953c578dbf5a0de2d6d366325afe3266b6706cf5685a",
    )

    with pytest.raises(DataError) as captured:
        get_cache_entry(read_req)
    assert captured.value.code == "DATABASE_ERROR"
