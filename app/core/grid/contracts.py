"""Canonical data contracts for distributed grid compute execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

__all__ = [
    "GridTopologyInfo",
    "RemoteJobResult",
    "RemoteJobSpec",
    "RemoteWorkerNode",
]


@dataclass(frozen=True, slots=True)
class RemoteJobSpec:
    """Specification of a distributed compute job to be dispatched to a worker."""

    job_id: str
    job_group_id: str = "default"
    operation_id: str = "compute"
    payload: dict[str, Any] = field(default_factory=dict)
    blocking: bool = False
    priority: int = 0
    timeout_ms: int = 60000


@dataclass(frozen=True, slots=True)
class RemoteJobResult:
    """Execution result produced by a remote worker for a compute job."""

    job_id: str
    job_group_id: str = "default"
    worker_id: str = ""
    success: bool = True
    data: dict[str, Any] | None = None
    duration_ms: int = 0
    error_message: str | None = None
    stopped: bool = False


@dataclass
class RemoteWorkerNode:
    """State and capability snapshot of a cluster worker node."""

    worker_id: str
    ip: str
    total_cores: int = 1
    used_cores: int = 0
    running_threads: int = 0
    total_memory_mb: float = 1024.0
    used_memory_mb: float = 0.0
    cpu_usage_pct: int = 0
    last_heartbeat_utc: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: str = "HEALTHY"

    def is_healthy(
        self, now_utc: datetime | None = None, timeout_sec: float = 10.0
    ) -> bool:
        """Check if worker has sent a heartbeat within the expiry window."""
        if self.status == "DISCONNECTED":
            return False
        now = now_utc or datetime.now(UTC)
        return (now - self.last_heartbeat_utc).total_seconds() < timeout_sec


@dataclass
class GridTopologyInfo:
    """Aggregate topology information across all registered worker nodes."""

    nodes: list[RemoteWorkerNode] = field(default_factory=list)
    running_threads: int = 0
    total_cores: int = 0
