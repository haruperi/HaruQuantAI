"""Configuration settings for Distributed Worker Pool."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DistributedWorkerPoolConfig:
    """Configuration model for distributed worker pool execution and timeouts.

    Attributes:
        default_heartbeat_interval_seconds: Expected heartbeat interval.
        max_lease_duration_seconds: Maximum validity duration for a lease.
        default_chunk_size_bytes: Target chunk size in bytes for transfers.
    """

    default_heartbeat_interval_seconds: int = 30
    max_lease_duration_seconds: int = 300
    default_chunk_size_bytes: int = 1048576
