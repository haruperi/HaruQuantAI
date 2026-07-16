"""Unit tests for the thread-safe lazy source registry."""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts.errors import DataError
from app.services.data.contracts.sources import SourceDescriptor, SourceLicensePolicy
from app.services.data.sources.protocol import MarketDataSource
from app.services.data.sources.registry import (
    _reset_registry,
    list_registered_sources,
    register_source,
    resolve_source,
)


def _make_descriptor(source_id: str) -> SourceDescriptor:
    policy = SourceLicensePolicy(
        source_id=source_id,
        status="approved",
        permitted_workflows=("research",),
        export_allowed=True,
        attribution_required=False,
    )
    return SourceDescriptor(
        source_id=source_id,
        readiness="disabled",
        capabilities=("bars",),
        requires_credentials=False,
        requires_network=False,
        supports_writes=False,
        schema_version="1.0",
        timezone="UTC",
        revision="v1",
        license_policy=policy,
        identity_mapping_revision="v1",
    )


@pytest.fixture(autouse=True)
def _cleanup() -> None:
    _reset_registry()


def test_registry_lazy_resolution() -> None:
    """Verify registry lazily resolves and caches resolved instances."""
    descriptor = _make_descriptor("test-lazy")
    mock_source = MagicMock(spec=MarketDataSource)
    factory_calls = 0

    def factory() -> MarketDataSource:
        nonlocal factory_calls
        factory_calls += 1
        return mock_source

    register_source(descriptor, factory)
    assert factory_calls == 0  # Lazy check: no instant factory invocation

    # Resolve first time
    first = resolve_source("test-lazy")
    assert first is mock_source
    assert factory_calls == 1

    # Resolve second time (should hit cache)
    second = resolve_source("test-lazy")
    assert second is mock_source
    assert factory_calls == 1


def test_registry_rejects_duplicate_registration() -> None:
    """Verify registry raises DataError on duplicate registration."""
    descriptor = _make_descriptor("test-dup")

    def factory():
        return MagicMock(spec=MarketDataSource)

    register_source(descriptor, factory)
    with pytest.raises(DataError) as captured:
        register_source(descriptor, factory)
    assert captured.value.code == "VALIDATION_FAILED"


def test_resolve_missing_source() -> None:
    """Verify resolve_source raises DataError for non-existent source."""
    with pytest.raises(DataError) as captured:
        resolve_source("missing-source")
    assert captured.value.code == "SOURCE_UNAVAILABLE"


def test_registry_thread_safety() -> None:
    """Verify that multiple threads can resolve concurrently without race conditions."""
    descriptor = _make_descriptor("test-thread")
    mock_source = MagicMock(spec=MarketDataSource)
    call_count = 0

    def factory() -> MarketDataSource:
        nonlocal call_count
        time.sleep(0.01)  # Yield thread
        call_count += 1
        return mock_source

    register_source(descriptor, factory)

    resolved_instances: list[MarketDataSource] = []
    threads = []

    def worker() -> None:
        inst = resolve_source("test-thread")
        resolved_instances.append(inst)

    # Spawn 10 concurrent threads resolving same lazy source
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # All threads must receive the same instance, and factory must run exactly once
    assert len(resolved_instances) == 10
    assert all(inst is mock_source for inst in resolved_instances)
    assert call_count == 1


def test_list_registered_sources() -> None:
    """Verify registry lists all registered source descriptors."""
    desc1 = _make_descriptor("test-1")
    desc2 = _make_descriptor("test-2")

    register_source(desc1, lambda: MagicMock(spec=MarketDataSource))
    register_source(desc2, lambda: MagicMock(spec=MarketDataSource))

    all_desc = list_registered_sources()
    assert len(all_desc) == 2
    assert {d.source_id for d in all_desc} == {"test-1", "test-2"}
