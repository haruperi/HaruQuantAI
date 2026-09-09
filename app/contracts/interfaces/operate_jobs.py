"""Public Interfaces contract for job, resource, and local-worker translation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.contracts.orchestration.jobs import ControlIntent, JobSemanticRecord
from app.contracts.orchestration.resources import ResourceLedgerSnapshot


class OperateJobsOperation(StrEnum):
    """Supported Phase-1 job interface operations."""

    GET_JOB = "GET_JOB"
    REQUEST_CONTROL = "REQUEST_CONTROL"
    RESOURCE_SNAPSHOT = "RESOURCE_SNAPSHOT"
    LOCAL_WORKER_READINESS = "LOCAL_WORKER_READINESS"


@dataclass(frozen=True, slots=True)
class OperateJobsRequest:
    """One bounded request translated onto orchestration owners."""

    operation: OperateJobsOperation
    job_id: str | None = None
    expected_version: int | None = None
    control: ControlIntent | None = None


@dataclass(frozen=True, slots=True)
class LocalWorkerReadiness:
    """Owner-safe projection of the local-worker capability."""

    available: bool
    capability: str = "orchestration.local-workers@1"
    reason_code: str = "READY"


OperateJobsResult = JobSemanticRecord | ResourceLedgerSnapshot | LocalWorkerReadiness


@runtime_checkable
class OperateJobsCapability(Protocol):
    """Translation-only job/resource/worker interface."""

    async def operate_jobs(self, request: OperateJobsRequest) -> OperateJobsResult:
        """Translate one validated operation to its owning capability."""
        ...


__all__ = [
    "LocalWorkerReadiness",
    "OperateJobsCapability",
    "OperateJobsOperation",
    "OperateJobsRequest",
    "OperateJobsResult",
]
