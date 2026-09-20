"""Unit tests for Diagnostics service, health telemetry, and benchmark calibration."""

from __future__ import annotations

import asyncio

import pytest
from app.contracts.workspace import (
    WORKSPACE_DIAGNOSTICS,
    CpuCoreMode,
)
from app.kernel.bootstrapper import Runtime
from app.services.workspace.diagnostics import (
    SPEC,
    DiagnosticsConfig,
    DiagnosticsService,
    feature,
)


def test_diagnostics_config_validation() -> None:
    """Verify diagnostics configuration validation."""
    config = DiagnosticsConfig(default_benchmark_ticks=500)
    assert config.default_benchmark_ticks == 500

    with pytest.raises(ValueError, match="default_benchmark_ticks must be positive"):
        DiagnosticsConfig(default_benchmark_ticks=0)


def test_system_health_reporting() -> None:
    """Verify health telemetry snapshot properties."""
    service = DiagnosticsService(DiagnosticsConfig(version="2.1.0"))
    health = service.get_health()

    assert health.status == "healthy"
    assert health.version == "2.1.0"
    assert health.total_memory_mb > 0
    assert health.memory_used_mb >= 0
    assert 0.0 <= health.memory_pct <= 100.0


def test_hardware_benchmark_calibration() -> None:
    """Verify synthetic tick benchmark execution and speedup metrics."""
    service = DiagnosticsService(DiagnosticsConfig())
    assert service.get_last_benchmark() is None

    result = service.run_benchmark(tick_count=500, core_mode=CpuCoreMode.SINGLE_CORE)
    assert result.total_ticks == 500
    assert result.cores_used == 1
    assert result.time_per_tick_ms >= 0.0
    assert result.avg_strategies_per_hour > 0.0

    # Cached last benchmark resolves
    last = service.get_last_benchmark()
    assert last is not None
    assert last.total_ticks == 500


def test_diagnostics_lifecycle_within_runtime() -> None:
    """Verify feature mounting and capability publishing in Runtime."""
    feat = feature()
    assert feat.spec == SPEC

    async def _test() -> None:
        async with Runtime((feature,)) as runtime:
            diag = runtime.require(WORKSPACE_DIAGNOSTICS)
            health = diag.get_health()
            assert health.status in ("healthy", "degraded", "unknown")

    asyncio.run(_test())


def test_diagnostics_health_status_thresholds() -> None:
    """Verify dynamic health status calculation (FR-WORKSPACE-008)."""
    from unittest.mock import patch

    service = DiagnosticsService(DiagnosticsConfig())

    # High memory usage trips degraded status
    with patch(
        "app.services.workspace.diagnostics._sample_system_memory",
        return_value=(8800.0, 10000.0, 88.0),
    ):
        health = service.get_health()
        assert health.status == "degraded"

    # Probe failure yields unknown status
    with patch(
        "app.services.workspace.diagnostics._sample_system_memory",
        return_value=(0.0, 0.0, 0.0),
    ):
        health = service.get_health()
        assert health.status == "unknown"


def test_diagnostics_active_jobs_persistence_integration() -> None:
    """Verify live count_active_jobs integration with persistence (FR-WORKSPACE-008)."""
    from unittest.mock import MagicMock

    mock_persistence = MagicMock()
    mock_persistence.count_active_jobs.return_value = 5

    service = DiagnosticsService(DiagnosticsConfig(), persistence=mock_persistence)
    health = service.get_health()
    assert health.active_jobs == 5
    mock_persistence.count_active_jobs.assert_called_once()
