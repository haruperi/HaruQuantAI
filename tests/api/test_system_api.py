"""Unit tests for capability-aware SystemAPI facade and introspection."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import override

import pytest

from app.api.system import SystemAPI
from app.composition.engine import CompositionEngine
from app.contracts.system.clock import SYSTEM_CLOCK, SystemClock
from app.contracts.system.metrics import MetricsCollector
from app.contracts.system.storage import SYSTEM_STORAGE, StorageEngine
from app.kernel.capability import CapabilityUnavailableError
from app.kernel.registry import ServiceRegistry


class DummyStorageEngine(StorageEngine):
    """Test double for StorageEngine contract."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    @override
    async def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    @override
    async def set(self, key: str, value: bytes) -> None:
        self._data[key] = value

    @override
    async def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    @override
    async def list_keys(self, prefix: str = "") -> tuple[str, ...]:
        return tuple(k for k in self._data if k.startswith(prefix))

    @override
    def partition(self, namespace: str) -> StorageEngine:
        return self


class DummyClock(SystemClock):
    @override
    def now(self) -> datetime:
        return datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)

    @override
    def timestamp(self) -> float:
        return 1780315200.0


class DummyMetrics(MetricsCollector):
    @override
    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        pass

    @override
    def gauge(
        self,
        name: str,
        value: float,
        tags: Mapping[str, str] | None = None,
    ) -> None:
        pass


@pytest.mark.asyncio
async def test_system_api_storage_and_introspection() -> None:
    """Test SystemAPI resolves storage and provides capability introspection."""
    registry = ServiceRegistry()
    storage_engine = DummyStorageEngine()
    clock_service = DummyClock()

    registry.register(
        SYSTEM_STORAGE, storage_engine, owner_id="FEAT-SYS-PERSIST_STORAGE"
    )
    registry.register(SYSTEM_CLOCK, clock_service, owner_id="FEAT-SYS-SYSTEM_CLOCK")

    api = SystemAPI(registry)

    # Introspection
    assert api.is_storage_available is True
    assert api.is_clock_available is True
    assert api.is_metrics_available is False

    storage_info = api.inspect_capability(SYSTEM_STORAGE)
    assert storage_info.is_available is True
    assert storage_info.provider_feature_id == "FEAT-SYS-PERSIST_STORAGE"

    missing_info = api.inspect_capability("unknown.capability@1")
    assert missing_info.is_available is False
    assert missing_info.provider_feature_id is None

    all_caps = api.list_capabilities()
    assert "system.storage@1" in all_caps
    assert "system.clock@1" in all_caps

    # Resolved services
    storage = api.get_storage_engine()
    await storage.set("foo", b"bar")
    assert await storage.get("foo") == b"bar"

    clock = api.get_clock()
    assert clock.now() == datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)

    with pytest.raises(CapabilityUnavailableError, match=r"system\.metrics@1"):
        api.get_metrics()


@pytest.mark.asyncio
async def test_system_api_feature_diagnostics() -> None:
    """Test SystemAPI feature diagnostic inspection with and without engine."""
    registry = ServiceRegistry()
    standalone_api = SystemAPI(registry)

    # Without bound composition engine
    assert standalone_api.get_runtime_status() is None
    assert standalone_api.list_package_dependency_errors() == {}
    assert standalone_api.list_capability_dependency_errors() == {}
    standalone_diag = standalone_api.inspect_feature("FEAT-DATA-RETRIEVE_BARS")
    assert standalone_diag.is_active is False
    assert standalone_diag.package_error is None

    # With bound composition engine
    engine = CompositionEngine(registry=registry)
    api_with_engine = SystemAPI(registry, engine=engine)
    status = api_with_engine.get_runtime_status()
    assert status is not None
    assert status.profile == "research"
