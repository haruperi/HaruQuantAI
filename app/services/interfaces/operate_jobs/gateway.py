"""Translation-only gateway for shared job/resource/local-worker operations."""

from __future__ import annotations

from app.contracts.interfaces.operate_jobs import (
    LocalWorkerReadiness,
    OperateJobsOperation,
    OperateJobsRequest,
    OperateJobsResult,
)
from app.contracts.orchestration.jobs import ControlIntent, ManageJobsCapability
from app.contracts.orchestration.local_workers import LocalWorkersCapability
from app.contracts.orchestration.resources import ResourceAdmissionPort


class JobsGateway:
    """Translate validated interface requests without acquiring owner authority."""

    def __init__(
        self,
        jobs: ManageJobsCapability,
        resources: ResourceAdmissionPort,
        local_workers: LocalWorkersCapability,
    ) -> None:
        self._jobs = jobs
        self._resources = resources
        self._local_workers = local_workers
        self._closed = False

    async def operate_jobs(self, request: OperateJobsRequest) -> OperateJobsResult:
        """Dispatch one supported owner operation."""
        if self._closed:
            raise RuntimeError("operate-jobs gateway is closed")
        if request.operation is OperateJobsOperation.GET_JOB:
            if not request.job_id:
                raise ValueError("job_id is required")
            return await self._jobs.get_semantics(request.job_id)
        if request.operation is OperateJobsOperation.REQUEST_CONTROL:
            if not request.job_id or request.expected_version is None or request.control is None:
                raise ValueError("job_id, expected_version, and control are required")
            if request.control not in {ControlIntent.CANCEL, ControlIntent.PAUSE, ControlIntent.RESUME}:
                raise ValueError("unsupported job control")
            return await self._jobs.request_control(
                request.job_id,
                expected_version=request.expected_version,
                control=request.control,
            )
        if request.operation is OperateJobsOperation.RESOURCE_SNAPSHOT:
            return self._resources.get_snapshot()
        if request.operation is OperateJobsOperation.LOCAL_WORKER_READINESS:
            return LocalWorkerReadiness(available=not self._closed)
        raise ValueError("operation is not qualified in Phase 1")

    def close(self) -> None:
        """Dispose the gateway without changing any owner state."""
        self._closed = True
