"""Tests for the finite resource governor feature (FR-WORKSPACE-RESOURCE_GOVERNOR)."""

from __future__ import annotations

import asyncio
import os

import pytest
from app.contracts.workspace import (
    WORKSPACE_RESOURCES,
    CpuCoreMode,
)
from app.kernel.bootstrapper import Runtime
from app.services.workspace.resource_governor import (
    SPEC,
    ResourceGovernorConfig,
    ResourceGovernorService,
    feature,
)


def test_cpu_core_modes() -> None:
    """Verify max thread calculation across all CPU core profiles."""
    detected = os.cpu_count() or 4

    # Single core
    cfg_single = ResourceGovernorConfig(cpu_mode=CpuCoreMode.SINGLE_CORE)
    gov_single = ResourceGovernorService(cfg_single)
    assert gov_single.get_quota().max_threads == 1

    # Reserve 1 core
    cfg_res = ResourceGovernorConfig(cpu_mode=CpuCoreMode.RESERVE_1_CORE)
    gov_res = ResourceGovernorService(cfg_res)
    assert gov_res.get_quota().max_threads == max(1, detected - 1)

    # Custom cores
    cfg_custom = ResourceGovernorConfig(
        cpu_mode=CpuCoreMode.CUSTOM_CORES,
        custom_cores=6,
    )
    gov_custom = ResourceGovernorService(cfg_custom)
    assert gov_custom.get_quota().max_threads == 6

    # Max performance
    cfg_max = ResourceGovernorConfig(cpu_mode=CpuCoreMode.MAX_PERFORMANCE)
    gov_max = ResourceGovernorService(cfg_max)
    assert gov_max.get_quota().max_threads == max(1, detected)


def test_watchdog_tripwire_and_admission() -> None:
    """Verify 85% memory watchdog trips and blocks admission."""
    # Under limit (60% RAM)
    normal_probe = lambda: (6000.0, 10000.0, 60.0)  # noqa: E731
    cfg_normal = ResourceGovernorConfig(
        max_memory_mb=8000,
        memory_probe=normal_probe,
    )
    gov_normal = ResourceGovernorService(cfg_normal)
    assert not gov_normal.is_watchdog_tripped()
    assert gov_normal.check_admission(required_threads=1, required_memory_mb=1000)

    # Over 85% limit (88% RAM)
    trip_probe = lambda: (8800.0, 10000.0, 88.0)  # noqa: E731
    cfg_trip = ResourceGovernorConfig(
        max_memory_mb=8000,
        memory_watchdog_threshold_pct=85.0,
        memory_probe=trip_probe,
    )
    gov_trip = ResourceGovernorService(cfg_trip)
    assert gov_trip.is_watchdog_tripped()
    # Watchdog trip denies admission immediately
    assert not gov_trip.check_admission(required_threads=1, required_memory_mb=500)
    usage = gov_trip.get_usage()
    assert usage.watchdog_tripped is True
    assert usage.memory_pct == 88.0


def test_resource_allocation_and_release() -> None:
    """Verify thread and memory capacity tracking with allocate and release."""
    normal_probe = lambda: (2000.0, 10000.0, 20.0)  # noqa: E731
    cfg = ResourceGovernorConfig(
        cpu_mode=CpuCoreMode.CUSTOM_CORES,
        custom_cores=2,
        max_memory_mb=2000,
        memory_probe=normal_probe,
    )
    gov = ResourceGovernorService(cfg)

    # Allocate within limits
    assert gov.allocate(required_threads=1, required_memory_mb=1000)
    assert gov.get_usage().active_workers == 1

    # Second allocation fits exactly
    assert gov.allocate(required_threads=1, required_memory_mb=1000)
    assert gov.get_usage().active_workers == 2

    # Third allocation exceeds both thread and memory capacity
    assert not gov.allocate(required_threads=1, required_memory_mb=500)

    # Release worker resources
    gov.release(threads=1, memory_mb=1000)
    assert gov.get_usage().active_workers == 1

    # Now a 1-thread 500MB allocation succeeds
    assert gov.allocate(required_threads=1, required_memory_mb=500)
    assert gov.get_usage().active_workers == 2


def test_cleanup_memory() -> None:
    """Verify cleanup_memory invokes gc.collect and returns non-negative count."""
    gov = ResourceGovernorService(ResourceGovernorConfig())
    freed = gov.cleanup_memory()
    assert isinstance(freed, int)
    assert freed >= 0


def test_resource_governor_lifecycle() -> None:
    """Verify feature boots inside Runtime and provides WORKSPACE_RESOURCES."""
    feat = feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime((feature,)) as runtime:
            svc = runtime.require(WORKSPACE_RESOURCES)
            quota = svc.get_quota()
            assert quota.max_threads >= 1
            assert not svc.is_watchdog_tripped()

    asyncio.run(_test())


def test_resource_governor_config_validation() -> None:
    """Verify bounds validation on ResourceGovernorConfig."""
    with pytest.raises(ValueError, match="custom_cores"):
        ResourceGovernorConfig(custom_cores=0)

    with pytest.raises(ValueError, match="max_memory_mb"):
        ResourceGovernorConfig(max_memory_mb=0)

    with pytest.raises(ValueError, match="memory_watchdog_threshold_pct"):
        ResourceGovernorConfig(memory_watchdog_threshold_pct=5.0)

    with pytest.raises(ValueError, match="memory_watchdog_threshold_pct"):
        ResourceGovernorConfig(memory_watchdog_threshold_pct=99.5)

    valid = ResourceGovernorConfig(
        custom_cores=2, max_memory_mb=4096, memory_watchdog_threshold_pct=80.0
    )
    assert valid.custom_cores == 2
    assert valid.max_memory_mb == 4096
    assert valid.memory_watchdog_threshold_pct == 80.0
