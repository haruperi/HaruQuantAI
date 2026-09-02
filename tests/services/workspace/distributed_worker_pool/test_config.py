"""Unit tests for DistributedWorkerPoolConfig."""

from app.services.workspace.distributed_worker_pool.config import (
    DistributedWorkerPoolConfig,
)


def test_distributed_worker_pool_config_defaults() -> None:
    """Verify default configuration values."""
    config = DistributedWorkerPoolConfig()
    assert config.default_heartbeat_interval_seconds == 30
    assert config.max_lease_duration_seconds == 300
    assert config.default_chunk_size_bytes == 1048576


def test_distributed_worker_pool_config_custom() -> None:
    """Verify custom configuration instantiation."""
    config = DistributedWorkerPoolConfig(
        default_heartbeat_interval_seconds=60,
        max_lease_duration_seconds=600,
        default_chunk_size_bytes=2097152,
    )
    assert config.default_heartbeat_interval_seconds == 60
    assert config.max_lease_duration_seconds == 600
    assert config.default_chunk_size_bytes == 2097152
