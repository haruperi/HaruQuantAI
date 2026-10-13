"""Diagnostics, persistence, and hardware probe REST API endpoints.

Description:
    Exposes FastAPI routes for querying real-time system diagnostics (CPU,
    memory, disk, processes), executing and managing bounded CPU benchmarks,
    inspecting workspace paths configuration, and projecting database health,
    schema migrations, and PRAGMA integrity checks.

Purpose:
    FEAT-API-DIAGNOSTICS: Dedicated REST API routing for system diagnostics,
    hardware probes, workspace paths validation, and persistence inspection.

Key Capabilities:
    - FR-API-DIAG-SYSTEM-PROJECTION: HTTP routes for CPU, RAM, disk, and process probes.
      Associated: `create_diagnostics_router()`, `_mount_system_routes()`
      Logging: Emits DEBUG telemetry on routine diagnostic queries.
    - FR-API-DIAG-BENCHMARK-PROJECTION: HTTP routes for benchmark lifecycle.
      Associated: `_mount_benchmark_routes()`, `post_run_benchmark()`, `cancel()`
      Logging: Emits INFO on benchmark start and cancellation; rejects missing jobs.
    - FR-API-DIAG-PERSISTENCE-PROJECTION: HTTP routes for database health and schema.
      Associated: `DatabaseDiagnosticsService`, `create_database_diagnostics_router()`
      Logging: Emits DEBUG telemetry on database status, migrations, and integrity.
    - FR-API-DIAG-PATHS-PROJECTION: HTTP routes for configured path validation.
      Associated: `create_settings_paths_router()`
      Logging: Emits INFO/WARNING on workspace directory presence.

Python API Usage:
    ```python
    from app.api.diagnostics import (
        create_database_diagnostics_router,
        create_diagnostics_router,
        create_settings_paths_router,
    )
    from app.host.persistence import DatabaseManager
    from app.host.settings import HostSettings

    diag_router = create_diagnostics_router()
    db_router = create_database_diagnostics_router(DatabaseManager())
    paths_router = create_settings_paths_router(HostSettings())
    ```

CLI Usage:
    Diagnostics REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.host.diagnostics import (
    DEFAULT_BENCHMARK_ITERATIONS,
    BenchmarkJob,
    BenchmarkRunner,
    CpuObservation,
    DiskObservation,
    MemoryObservation,
    ProcessObservation,
    SystemDiagnosticsSnapshot,
    WorkerCapacity,
    get_worker_capacity,
    probe_cpu,
    probe_disk,
    probe_memory,
    probe_process,
    probe_system_diagnostics,
    validate_settings_paths,
)
from app.host.logging import get_logger
from app.host.persistence import DatabaseManager
from app.host.response import StandardResponse as ApiResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.host.settings import HostSettings

__all__ = [
    "DatabaseDiagnosticsService",
    "create_database_diagnostics_router",
    "create_diagnostics_router",
    "create_persistence_router",
    "create_settings_paths_router",
]

logger = get_logger(__name__)

# Global default benchmark runner
_DEFAULT_BENCHMARK_RUNNER = BenchmarkRunner()


def _mount_system_routes(router: APIRouter) -> None:
    """Mount hardware and capacity probe inspection routes."""

    @router.get(
        "/system",
        response_model=SystemDiagnosticsSnapshot,
        summary="Query system diagnostics snapshot",
    )
    async def get_system_diagnostics() -> SystemDiagnosticsSnapshot:
        return probe_system_diagnostics()

    @router.get(
        "/cpu",
        response_model=CpuObservation,
        summary="Query CPU topology and utilization",
    )
    async def get_cpu() -> CpuObservation:
        return probe_cpu()

    @router.get(
        "/memory",
        response_model=MemoryObservation,
        summary="Query memory capacity and load",
    )
    async def get_memory() -> MemoryObservation:
        return probe_memory()

    @router.get(
        "/disk",
        response_model=DiskObservation,
        summary="Query storage volume metrics",
    )
    async def get_disk() -> DiskObservation:
        return probe_disk()

    @router.get(
        "/process",
        response_model=ProcessObservation,
        summary="Query host process health",
    )
    async def get_process() -> ProcessObservation:
        return probe_process()

    @router.get(
        "/workers",
        response_model=WorkerCapacity,
        summary="Query worker capacity and limits",
    )
    async def get_workers(
        mode: str = Query(default="reserve-one", description="Core usage mode"),
        custom_cores: int = Query(default=1, ge=1, description="Custom cores limit"),
    ) -> WorkerCapacity:
        return get_worker_capacity(mode=mode, custom_cores=custom_cores)


def _mount_benchmark_routes(router: APIRouter, runner: BenchmarkRunner) -> None:
    """Mount computational benchmark lifecycle routes."""

    @router.post(
        "/benchmark/run",
        response_model=BenchmarkJob,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Initiate CPU benchmark run",
    )
    async def post_run_benchmark(
        iterations: int = Query(
            default=DEFAULT_BENCHMARK_ITERATIONS,
            ge=1000,
            le=5_000_000,
            description="Benchmark tick iterations",
        ),
    ) -> BenchmarkJob:
        return runner.start_job(iterations=iterations)

    @router.get(
        "/benchmark/{job_id}",
        response_model=BenchmarkJob,
        summary="Query benchmark job status",
    )
    async def get_benchmark_job(job_id: str) -> BenchmarkJob:
        job = runner.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark job '{job_id}' not found",
            )
        return job

    @router.post(
        "/benchmark/{job_id}/cancel",
        response_model=BenchmarkJob,
        summary="Cancel running benchmark job",
    )
    async def post_cancel_benchmark(job_id: str) -> BenchmarkJob:
        job = runner.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark job '{job_id}' not found",
            )
        runner.cancel_job(job_id)
        await asyncio.sleep(0.05)
        updated = runner.get_job(job_id)
        return updated or job


def create_diagnostics_router(
    runner: BenchmarkRunner | None = None,
) -> APIRouter:
    """Create FastAPI router providing diagnostics and benchmark REST endpoints.

    Args:
        runner: Optional BenchmarkRunner instance. Defaults to global instance.

    Returns:
        APIRouter configured under `/api/v1/diagnostics`.
    """
    router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])
    bench_runner = runner or _DEFAULT_BENCHMARK_RUNNER
    _mount_system_routes(router)
    _mount_benchmark_routes(router, bench_runner)
    return router


class DatabaseDiagnosticsService:
    """HTTP access to database operational inspection."""

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def get_status(self, request: Request) -> Response:
        """Get database operational metrics snapshot."""
        req_id = request.headers.get("x-request-id")
        status_rec = self._db.get_status()
        resp = ApiResponse.success(
            data=status_rec.model_dump(mode="json"),
            message="Database status retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_schema(self, request: Request) -> Response:
        """Get schema migration ledger records."""
        req_id = request.headers.get("x-request-id")
        migrations = self._db.schema.list_migrations()
        resp = ApiResponse.success(
            data=[m.model_dump(mode="json") for m in migrations],
            message="Schema migrations retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def check_integrity_endpoint(self, request: Request) -> Response:
        """Run physical SQLite database integrity verification."""
        req_id = request.headers.get("x-request-id")
        res = self._db.check_integrity()
        resp = ApiResponse.success(
            data={"integrity": res, "integrity_check": res},
            message=f"Database integrity verified: {res}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_database_diagnostics_router(db: DatabaseManager) -> APIRouter:
    """Expose database status, schema and integrity inspection over HTTP."""
    service = DatabaseDiagnosticsService(db)
    router = APIRouter(prefix="/persistence", tags=["persistence"])

    router.add_api_route(
        "/status",
        service.get_status,
        methods=["GET"],
        summary="Query database status and health",
    )
    router.add_api_route(
        "/schema",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations",
    )
    router.add_api_route(
        "/schema/migrations",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations alias",
    )
    router.add_api_route(
        "/integrity-check",
        service.check_integrity_endpoint,
        methods=["POST"],
        summary="Execute PRAGMA integrity_check",
    )
    logger.debug(
        "Persistence REST router initialized",
        extra={"fr_id": "FR-API-DIAG-PERSISTENCE-PROJECTION"},
    )
    return router


def create_settings_paths_router(settings_instance: HostSettings) -> APIRouter:
    """Expose configured directory inspection at its existing HTTP URL."""
    router = APIRouter()
    target_settings = settings_instance

    @router.get("/settings/paths/validate")
    async def validate_paths_endpoint() -> JSONResponse:
        """Validate configured workspace directories on disk."""
        statuses = validate_settings_paths(target_settings)
        all_valid = all(statuses.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "paths": statuses,
                    "all_valid": all_valid,
                },
            },
        )

    return router


def create_persistence_router(
    db: DatabaseManager, *, reconcile: Callable[[], dict[str, Any]]
) -> APIRouter:
    """Compose separately owned capabilities at the legacy persistence URLs."""
    from app.api.jobs import create_leases_router
    from app.api.shell import create_recovery_router

    router = APIRouter()
    router.include_router(create_database_diagnostics_router(db))
    router.include_router(create_leases_router(db))
    router.include_router(create_recovery_router(reconcile))
    logger.debug(
        "Persistence REST capabilities composed",
        extra={"fr_id": "FR-API-DIAG-PERSISTENCE-PROJECTION"},
    )
    return router
