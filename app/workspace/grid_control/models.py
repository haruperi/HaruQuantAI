"""Data models and serialization contracts for AppGridControl.

Description:
    Defines immutable data models representing compute job snapshots
    (running, waiting, finished) and wire envelopes matching the donor
    DescriptionsSerializer specification.

Purpose:
    FEAT-GRID-CONTROL: Canonical data contracts for distributed grid management.

Key Capabilities:
    - FR-GRID-MODELS-SERIALIZATION: Serialize job queue snapshots to camelCase
      wire format matching donor DescriptionsSerializer contracts.

Python API Usage:
    from app.workspace.grid_control.models import RunningJobSnapshot, GridDataPayload
    job = RunningJobSnapshot(
        job_id="job-1",
        job_group_id="default",
        create_time_ms=1000,
        progress=50,
        duration_ms=500,
        duration_with_wait_ms=1500,
        start_time_ms=1500,
        waiting=False,
    )
    payload = GridDataPayload(running=(job,), waiting=(), finished=())

CLI Usage:
    uv run python -m app.workspace.grid_control.models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.host.logging import get_logger

__all__ = [
    "FinishedJobSnapshot",
    "GridDataPayload",
    "GridDataResponse",
    "RunningJobSnapshot",
    "WaitingJobSnapshot",
]

_logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class RunningJobSnapshot:
    """Snapshot of an actively running compute job."""

    job_id: str
    job_group_id: str
    create_time_ms: int
    progress: int = 0
    duration_ms: int = 0
    duration_with_wait_ms: int = 0
    start_time_ms: int = 0
    waiting: bool = False

    def to_wire_dict(self) -> dict[str, Any]:
        """Convert to camelCase wire dictionary."""
        _logger.debug("Serializing RunningJobSnapshot: %s", self.job_id)
        return {
            "jobId": self.job_id,
            "jobGroupId": self.job_group_id,
            "createTime": self.create_time_ms,
            "progress": self.progress,
            "duration": self.duration_ms,
            "durationWithWait": self.duration_with_wait_ms,
            "startTime": self.start_time_ms,
            "waiting": self.waiting,
        }


@dataclass(frozen=True, slots=True)
class WaitingJobSnapshot:
    """Snapshot of a queued compute job waiting for execution."""

    job_id: str
    job_group_id: str
    create_time_ms: int

    def to_wire_dict(self) -> dict[str, Any]:
        """Convert to camelCase wire dictionary."""
        _logger.debug("Serializing WaitingJobSnapshot: %s", self.job_id)
        return {
            "jobId": self.job_id,
            "jobGroupId": self.job_group_id,
            "createTime": self.create_time_ms,
        }


@dataclass(frozen=True, slots=True)
class FinishedJobSnapshot:
    """Snapshot of a completed or failed compute job."""

    job_id: str
    job_group_id: str
    create_time_ms: int
    duration_ms: int = 0
    duration_with_wait_ms: int = 0
    start_time_ms: int = 0
    finish_time_ms: int = 0
    success: bool = True
    message: str | None = None

    def to_wire_dict(self) -> dict[str, Any]:
        """Convert to camelCase wire dictionary."""
        _logger.debug("Serializing FinishedJobSnapshot: %s", self.job_id)
        result: dict[str, Any] = {
            "jobId": self.job_id,
            "jobGroupId": self.job_group_id,
            "createTime": self.create_time_ms,
            "duration": self.duration_ms,
            "durationWithWait": self.duration_with_wait_ms,
            "startTime": self.start_time_ms,
            "finishTime": self.finish_time_ms,
            "success": self.success,
        }
        if not self.success and self.message is not None:
            result["message"] = self.message
        return result


@dataclass(frozen=True, slots=True)
class GridDataPayload:
    """Snapshot container for running, waiting, and finished compute jobs."""

    running: tuple[RunningJobSnapshot, ...] = field(default_factory=tuple)
    waiting: tuple[WaitingJobSnapshot, ...] = field(default_factory=tuple)
    finished: tuple[FinishedJobSnapshot, ...] = field(default_factory=tuple)

    def to_wire_dict(self) -> dict[str, Any]:
        """Convert to camelCase wire dictionary with job arrays."""
        _logger.debug(
            "Serializing GridDataPayload: %d running, %d waiting, %d finished",
            len(self.running),
            len(self.waiting),
            len(self.finished),
        )
        return {
            "running": [job.to_wire_dict() for job in self.running],
            "waiting": [job.to_wire_dict() for job in self.waiting],
            "finished": [job.to_wire_dict() for job in self.finished],
        }


@dataclass(frozen=True, slots=True)
class GridDataResponse:
    """Response envelope matching the /gridControl/getData contract."""

    grid_data: GridDataPayload = field(default_factory=GridDataPayload)
    success: str = "Databanks listed."

    def to_wire_dict(self) -> dict[str, Any]:
        """Convert to root wire response dictionary."""
        _logger.debug("Serializing GridDataResponse envelope")
        return {
            "gridData": self.grid_data.to_wire_dict(),
            "success": self.success,
        }
