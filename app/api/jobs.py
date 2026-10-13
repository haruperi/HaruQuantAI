"""Job scheduling, worker coordination, and cooperative lease REST API endpoints.

Description:
    Exposes FastAPI routes for querying host compute capacity, submitting
    background compute workloads, tracking job progress and results, cancelling
    jobs, and managing cooperative database worker leases (acquire, renew,
    release, list).

Purpose:
    FEAT-API-JOBS: Dedicated REST API routing for job scheduling, worker pools,
    and cooperative lease coordination.

Key Capabilities:
    - FR-API-JOBS-MANAGEMENT: HTTP routes for job submission, listing, and cancellation.
      Associated: `create_jobs_router()`, `JobRouterService`
      Logging: Emits DEBUG when jobs router is constructed; INFO on job admissions.
    - FR-API-JOBS-LEASES: HTTP routes for distributed worker lease coordination.
      Associated: `create_leases_router()`, `LeaseRouterService`
      Logging: Emits DEBUG when lease router is initialized; INFO on lease mutations.

Python API Usage:
    ```python
    from app.api.jobs import create_jobs_router, create_leases_router
    from app.host.jobs import JobManager
    from app.host.persistence import DatabaseManager

    jobs_router = create_jobs_router(JobManager())
    leases_router = create_leases_router(DatabaseManager())
    ```

CLI Usage:
    Jobs REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.host.jobs import (
    Budget,
    BudgetExceededError,
    CapacityExceededError,
    DuplicateJobError,
    JobContext,
    JobManager,
    JobManagerClosedError,
    JobNotFoundError,
    JobStatus,
    LeaseManager,
    SubmitJobRequest,
)
from app.host.logging import get_logger
from app.host.persistence import (
    DatabaseManager,
    LeaseExpiredError,
    StorageBusyError,
)
from app.host.response import StandardError, StandardResponse

__all__ = [
    "AcquireLeaseRequest",
    "JobRouterService",
    "LeaseRouterService",
    "ReleaseLeaseRequest",
    "RenewLeaseRequest",
    "SubmitJobRequest",
    "create_jobs_router",
    "create_leases_router",
]

logger = get_logger(__name__)


def _default_api_task(
    payload: dict[str, Any], context: JobContext | None = None
) -> dict[str, Any]:
    """Default lightweight worker task executed for REST submissions."""
    if context is not None:
        context.report_progress(50.0, message="Executing workload")
        context.check_cancellation()
        context.report_progress(100.0, message="Workload complete")
    return {"status": "success", "echo": payload}


class JobRouterService:
    """Service encapsulating HTTP endpoint handlers for local jobs."""

    def __init__(self, manager: JobManager) -> None:
        """Initialize service with central JobManager."""
        self._manager = manager

    def list_jobs(
        self,
        request: Request,
        owner: Annotated[str | None, Query()] = None,
        status_filter: Annotated[JobStatus | None, Query(alias="status")] = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 50,
    ) -> Response:
        """Query recent job records."""
        req_id = request.headers.get("x-request-id")
        jobs = self._manager.list_jobs(owner=owner, status=status_filter, limit=limit)
        resp = StandardResponse.success(
            data=[j.model_dump() for j in jobs],
            message="Jobs retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_capacity(self, request: Request) -> Response:
        """Query host worker capacity and active reservation metrics."""
        req_id = request.headers.get("x-request-id")
        cap = self._manager.capacity_status()
        resp = StandardResponse.success(
            data=cap.model_dump(),
            message="Capacity status retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def submit_job(
        self,
        request: Request,
        body: SubmitJobRequest,
    ) -> Response:
        """Submit a new background compute task."""
        req_id = request.headers.get("x-request-id")
        budget = Budget(
            workers=body.workers,
            memory_bytes=body.memory_bytes,
            timeout_seconds=body.timeout_seconds,
        )

        handler = self._manager.get_handler(body.kind) or _default_api_task

        try:
            future = self._manager.submit(
                body.owner,
                handler,
                body.payload,
                budget=budget,
                kind=body.kind,
                dedup_key=body.dedup_key,
                parent_job_id=body.parent_job_id,
                pass_context=True,
            )
        except CapacityExceededError as exc:
            err = StandardError(code="CAPACITY_EXCEEDED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=StandardResponse.failure(
                    message="Job rejected due to capacity limits.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except DuplicateJobError as exc:
            err = StandardError(code="DUPLICATE_JOB", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=StandardResponse.failure(
                    message="Job rejected due to active duplicate.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except BudgetExceededError as exc:
            err = StandardError(code="BUDGET_EXCEEDED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content=StandardResponse.failure(
                    message="Job budget exceeds maximum allowable limits.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )
        except JobManagerClosedError as exc:
            err = StandardError(code="MANAGER_CLOSED", message=str(exc))
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=StandardResponse.failure(
                    message="Job manager is closed.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        job_id = self._manager.get_job_id_for_future(future)
        job_record = self._manager.get_job(job_id) if job_id else None
        data = job_record.model_dump() if job_record else {"status": "submitted"}
        resp = StandardResponse.success(
            data=data,
            message="Job admitted successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=resp.to_dict())

    def get_job(self, request: Request, job_id: str) -> Response:
        """Query status and metrics for a specific job."""
        req_id = request.headers.get("x-request-id")
        try:
            rec = self._manager.get_job(job_id)
        except JobNotFoundError:
            err = StandardError(code="NOT_FOUND", message=f"Job '{job_id}' not found.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=StandardResponse.failure(
                    message="Job record not found.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        resp = StandardResponse.success(
            data=rec.model_dump(),
            message="Job record retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def cancel_job(self, request: Request, job_id: str) -> Response:
        """Cancel a pending or running job."""
        req_id = request.headers.get("x-request-id")
        try:
            self._manager.get_job(job_id)
        except JobNotFoundError:
            err = StandardError(code="NOT_FOUND", message=f"Job '{job_id}' not found.")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=StandardResponse.failure(
                    message="Job record not found.",
                    error=err,
                    request_id=req_id,
                ).to_dict(),
            )

        self._manager.cancel(job_id)
        updated_rec = self._manager.get_job(job_id)
        resp = StandardResponse.success(
            data=updated_rec.model_dump(),
            message="Job cancellation requested.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_jobs_router(manager: JobManager) -> APIRouter:
    """Create and return a FastAPI APIRouter exposing jobs management endpoints.

    Args:
        manager: Central JobManager instance.

    Returns:
        Configured FastAPI APIRouter instance.
    """
    service = JobRouterService(manager)
    router = APIRouter(prefix="/jobs", tags=["jobs"])

    router.add_api_route(
        "",
        service.list_jobs,
        methods=["GET"],
        summary="List jobs",
    )
    router.add_api_route(
        "/capacity",
        service.get_capacity,
        methods=["GET"],
        summary="Get capacity status",
    )
    router.add_api_route(
        "",
        service.submit_job,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
        summary="Submit job",
    )
    router.add_api_route(
        "/{job_id}",
        service.get_job,
        methods=["GET"],
        summary="Get job by ID",
    )
    router.add_api_route(
        "/{job_id}/cancel",
        service.cancel_job,
        methods=["POST"],
        summary="Cancel job",
    )

    logger.debug(
        "FR-API-JOBS-MANAGEMENT: Constructed jobs router with prefix /jobs",
        extra={"prefix": "/jobs", "requirement": "FR-API-JOBS-MANAGEMENT"},
    )
    return router


class AcquireLeaseRequest(BaseModel):
    """Request payload for acquiring a cooperative worker lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)
    scope: str = Field(default="default")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenewLeaseRequest(BaseModel):
    """Request payload for renewing an active lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)


class ReleaseLeaseRequest(BaseModel):
    """Request payload for releasing a held lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)


class LeaseRouterService:
    """HTTP access to worker lease coordination owned by jobs."""

    def __init__(self, db: DatabaseManager) -> None:
        self._leases = LeaseManager(db)

    def list_leases(self, request: Request) -> Response:
        """List currently active cooperative leases."""
        req_id = request.headers.get("x-request-id")
        leases = self._leases.list_active()
        resp = StandardResponse.success(
            data=[lease.model_dump(mode="json") for lease in leases],
            message="Active leases retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def acquire_lease_endpoint(
        self,
        request: Request,
        req: AcquireLeaseRequest,
    ) -> Response:
        """Acquire a cooperative worker lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._leases.acquire(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
                scope=req.scope,
                metadata=req.metadata,
            )
            resp = StandardResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} acquired successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except StorageBusyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    def renew_lease_endpoint(
        self,
        request: Request,
        req: RenewLeaseRequest,
    ) -> Response:
        """Renew a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._leases.renew(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
            )
            resp = StandardResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} renewed successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except LeaseExpiredError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    def release_lease_endpoint(
        self,
        request: Request,
        req: ReleaseLeaseRequest,
    ) -> Response:
        """Release a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        released = self._leases.release(req.lease_key, req.holder_id)
        resp = StandardResponse.success(
            data={"released": released},
            message=f"Lease {req.lease_key} released: {released}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_leases_router(db: DatabaseManager) -> APIRouter:
    """Expose worker lease coordination at its existing HTTP URLs."""
    service = LeaseRouterService(db)
    router = APIRouter(prefix="/persistence/leases", tags=["persistence"])
    router.add_api_route(
        "",
        service.list_leases,
        methods=["GET"],
        summary="List active cooperative leases",
    )
    router.add_api_route(
        "/acquire",
        service.acquire_lease_endpoint,
        methods=["POST"],
        summary="Acquire a cooperative lease",
    )
    router.add_api_route(
        "/renew",
        service.renew_lease_endpoint,
        methods=["POST"],
        summary="Renew an active lease",
    )
    router.add_api_route(
        "/release",
        service.release_lease_endpoint,
        methods=["POST"],
        summary="Release an active lease",
    )
    logger.debug(
        "FR-API-JOBS-LEASES: Lease REST router initialized",
        extra={"fr_id": "FR-API-JOBS-LEASES"},
    )
    return router
