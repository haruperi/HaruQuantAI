"""FastAPI REST routes for the AppHome workspace.

Description:
    Exposes authenticated HTTP endpoints for application landing metadata,
    recent project discovery, host diagnostics, release update status,
    project settings/notes persistence with optimistic revision control,
    template application, resource resolution, engine execution controls,
    and dashboard leaderboard queries.

Purpose:
    FEAT-HOME-ROUTES: Authenticated HTTP routes for Home and shared project workspaces.

Key Capabilities:
    - FR-home-routes-landing: Serve recent projects and Getting Started metadata.
    - FR-home-routes-about: Expose host environment and license status.
    - FR-home-routes-updates: Query update availability safely.
    - FR-home-routes-diagnostics: Expose host database, memory, and directories.
    - FR-home-routes-project: Persist project settings with optimistic locking.
    - FR-home-routes-notes: Persist project notes with conflict detection.
    - FR-home-routes-template: Apply strategy templates with rollback protection.
    - FR-home-routes-resources: Resolve dataset and symbol dependencies.
    - FR-home-routes-engine: Control engine lifecycle and telemetry.
    - FR-home-routes-dashboard: Query top strategies ranked by performance metrics.

Python API Usage:
    from app.workspace.home.routes import home_router
    app.include_router(home_router)

CLI Usage:
    uv run python -m pytest tests/workspace/home/test_routes.py -q
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from app.core.host.logging import get_logger
from app.core.host.transport import TransportError, _peer, _token
from app.core.lib.errors import DomainError
from app.core.lib.responses import ErrorCode
from app.workspace.home.service import HomeService

logger = get_logger(__name__)

home_router = APIRouter(prefix="/api/v1/home", tags=["home"])


def _require_auth(request: Request) -> None:
    """Validate that the request carries an authenticated host session."""
    sessions = getattr(request.app.state, "sessions", None)
    if sessions is None:
        logger.warning(
            "FR-home-routes-landing: authentication rejected; missing session authority"
        )
        raise TransportError(
            ErrorCode.UNAUTHORIZED, "Session manager authority is absent"
        )
    token = _token(request)
    peer = _peer(request)
    session = sessions.validate_session(token, peer)
    if session is None:
        logger.warning(
            "FR-home-routes-landing: authentication rejected; missing/invalid session"
        )
        raise TransportError(ErrorCode.UNAUTHORIZED, "A UI session is required")
    request.state.authenticated_session = session


def _get_service(request: Request) -> HomeService:
    """Resolve or construct the HomeService instance for the current application."""
    service = getattr(request.app.state, "home_service", None)
    if service is None:
        persistence = getattr(request.app.state, "persistence", None)
        if persistence is None:
            raise TransportError(ErrorCode.UNAVAILABLE, "Host persistence unavailable")
        job_manager = getattr(request.app.state, "job_manager", None)
        data_catalog = getattr(request.app.state, "data_catalog", None)
        service = HomeService(
            persistence=persistence,
            job_manager=job_manager,
            data_catalog=data_catalog,
            settings_manager=getattr(request.app.state, "settings", None),
        )
        request.app.state.home_service = service
    return service


def _envelope(data: Any) -> dict[str, Any]:
    """Wrap payload in StandardResponse success envelope."""
    return {"status": "success", "data": data, "revision": None}


# --- Request Models ---


class SaveSettingsRequest(BaseModel):
    """Payload for saving task settings."""

    task_id: str = Field(..., description="Target task identifier")
    settings: dict[str, Any] = Field(
        default_factory=dict, description="Task settings map"
    )
    expected_revision: int = Field(
        ..., ge=1, strict=True, description="Expected revision for concurrency check"
    )


class SaveNotesRequest(BaseModel):
    """Payload for saving project notes."""

    notes: str = Field(..., description="Plain-text Unicode project notes")
    expected_revision: int = Field(
        ..., ge=1, strict=True, description="Expected revision for concurrency check"
    )


class ApplyTemplateRequest(BaseModel):
    """Payload for applying a strategy template."""

    task_id: str = Field(..., description="Target task identifier")
    strategy_type: str = Field(..., description="Name of template to apply")
    expected_revision: int = Field(
        ..., ge=1, strict=True, description="Expected revision for concurrency check"
    )


class ResolveResourcesRequest(BaseModel):
    """Payload for resolving missing resource dependencies."""

    resolutions: dict[str, str] = Field(
        ..., description="Map of resource keys to resolved symbols"
    )
    expected_revision: int = Field(
        ..., ge=1, strict=True, description="Expected revision for concurrency check"
    )


class EngineActionRequest(BaseModel):
    """Payload for triggering engine lifecycle actions."""

    task_id: str | None = Field(None, description="Saved task identifier")
    expected_revision: int | None = Field(None, ge=1, strict=True)
    job_id: str | None = None


# --- Endpoints ---


@home_router.get("", summary="Get recent projects list")
async def get_home_index(request: Request) -> dict[str, Any]:
    """Return recent projects and workspace summary."""
    _require_auth(request)
    logger.info("FR-home-routes-landing: handling home index request")
    service = _get_service(request)
    recent = service.get_recent_projects()
    return _envelope({"recent_projects": recent})


@home_router.get("/about", summary="Get host and license metadata")
async def get_home_about(request: Request) -> dict[str, Any]:
    """Return application version, runtime, and license information."""
    _require_auth(request)
    logger.info("FR-home-routes-about: handling home about request")
    service = _get_service(request)
    about = service.get_about_info()
    return _envelope(about)


@home_router.get("/updates", summary="Check for software updates")
async def get_home_updates(request: Request) -> dict[str, Any]:
    """Return software release information, failing closed when unconfigured."""
    _require_auth(request)
    logger.info("FR-home-routes-updates: handling release updates request")
    service = _get_service(request)
    updates = service.get_release_info()
    return _envelope(updates)


@home_router.get("/diagnostics", summary="Inspect host diagnostics and memory")
async def get_home_diagnostics(request: Request) -> dict[str, Any]:
    """Return host database status, memory headroom, and directories."""
    _require_auth(request)
    logger.info("FR-home-routes-diagnostics: handling diagnostics request")
    service = _get_service(request)
    diagnostics = service.get_host_diagnostics()
    return _envelope(diagnostics)


@home_router.get("/project/{project_id}", summary="Load project document")
async def get_project_document(project_id: str, request: Request) -> dict[str, Any]:
    """Load and return project container manifest, pipeline, and tasks."""
    _require_auth(request)
    logger.info("FR-home-routes-project: loading project %s", project_id)
    service = _get_service(request)
    try:
        doc = service.load_project(project_id)
        return _envelope(doc)
    except DomainError as err:
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.post(
    "/project/{project_id}/settings", summary="Save project task settings"
)
async def save_project_settings(
    project_id: str,
    payload: SaveSettingsRequest,
    request: Request,
) -> dict[str, Any]:
    """Save task settings with optimistic revision conflict detection."""
    _require_auth(request)
    logger.info("FR-home-routes-project: saving settings for project %s", project_id)
    service = _get_service(request)
    try:
        result = service.save_project_settings(
            project_id=project_id,
            task_id=payload.task_id,
            settings=payload.settings,
            expected_revision=payload.expected_revision,
        )
        return _envelope(result)
    except DomainError as err:
        if err.code == "CONFLICT":
            raise TransportError(ErrorCode.CONFLICT, err.message) from err
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.post("/project/{project_id}/notes", summary="Save project notes")
async def save_project_notes(
    project_id: str,
    payload: SaveNotesRequest,
    request: Request,
) -> dict[str, Any]:
    """Save project notes with revision check."""
    _require_auth(request)
    logger.info("FR-home-routes-notes: saving notes for project %s", project_id)
    service = _get_service(request)
    try:
        result = service.save_project_notes(
            project_id=project_id,
            notes=payload.notes,
            expected_revision=payload.expected_revision,
        )
        return _envelope(result)
    except DomainError as err:
        if err.code == "CONFLICT":
            raise TransportError(ErrorCode.CONFLICT, err.message) from err
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.post("/project/{project_id}/template", summary="Apply strategy template")
async def apply_template(
    project_id: str,
    payload: ApplyTemplateRequest,
    request: Request,
) -> dict[str, Any]:
    """Apply strategy template to a project task with atomic rollback on failure."""
    _require_auth(request)
    logger.info("FR-home-routes-template: applying template for project %s", project_id)
    service = _get_service(request)
    try:
        result = service.apply_template(
            project_id=project_id,
            task_id=payload.task_id,
            strategy_type=payload.strategy_type,
            expected_revision=payload.expected_revision,
        )
        return _envelope(result)
    except DomainError as err:
        if err.code == "CONFLICT":
            raise TransportError(ErrorCode.CONFLICT, err.message) from err
        if err.code == "INVALID_TEMPLATE":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        if err.code == "INVALID_PROJECT_ID":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.post(
    "/project/{project_id}/resources/resolve", summary="Resolve resource dependencies"
)
async def resolve_resources(
    project_id: str,
    payload: ResolveResourcesRequest,
    request: Request,
) -> dict[str, Any]:
    """Resolve symbol and dataset resources for a project."""
    _require_auth(request)
    logger.info(
        "FR-home-routes-resources: resolving resources for project %s", project_id
    )
    service = _get_service(request)
    try:
        result = service.resolve_resources(
            project_id=project_id,
            resolutions=payload.resolutions,
            expected_revision=payload.expected_revision,
        )
        return _envelope(result)
    except DomainError as err:
        if err.code == "CONFLICT":
            raise TransportError(ErrorCode.CONFLICT, err.message) from err
        if err.code == "DATASET_NOT_FOUND":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        if err.code == "INVALID_PROJECT_ID":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.post(
    "/engine/{project_id}/{action}", summary="Execute engine lifecycle action"
)
async def execute_engine_action(
    project_id: str,
    action: str,
    payload: EngineActionRequest,
    request: Request,
) -> dict[str, Any]:
    """Execute engine start, pause, resume, or stop action."""
    _require_auth(request)
    logger.info(
        "FR-home-routes-engine: executing engine action '%s' for %s", action, project_id
    )
    service = _get_service(request)
    try:
        result = service.engine_action(
            project_id=project_id,
            action=action,
            task_id=payload.task_id,
            expected_revision=payload.expected_revision,
            job_id=payload.job_id,
        )
        return _envelope(result)
    except DomainError as err:
        if err.code in ("ALREADY_RUNNING", "CONFLICT", "INVALID_JOB_STATE"):
            raise TransportError(ErrorCode.CONFLICT, err.message) from err
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        if err.code == "INVALID_PROJECT_ID":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        if err.code == "JOB_MANAGER_UNAVAILABLE":
            raise TransportError(ErrorCode.UNAVAILABLE, err.message) from err
        if err.code == "INVALID_ENGINE_ACTION":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.get(
    "/engine/{project_id}/status", summary="Get engine status and telemetry"
)
async def get_engine_status(
    project_id: str, request: Request, job_id: str | None = None
) -> dict[str, Any]:
    """Return engine status, progress counters, and telemetry."""
    _require_auth(request)
    logger.info("FR-home-routes-engine: fetching engine status for %s", project_id)
    service = _get_service(request)
    try:
        status = service.get_engine_status(project_id, job_id)
        return _envelope(status)
    except DomainError as err:
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        if err.code == "INVALID_PROJECT_ID":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.get("/dashboard/results", summary="Get dashboard results leaderboard")
async def get_dashboard_results(
    request: Request,
    *,
    project_id: str = Query(..., description="Project identifier"),
    databank_id: str = Query("Results", description="Databank identifier"),
    sample_type: str = Query("ALL", description="Sample partition: ALL, IS, or OOS"),
    metric: str = Query("net_profit", description="Ranking metric"),
    limit: int = Query(10, ge=1, le=100, description="Max strategies to return"),
) -> dict[str, Any]:
    """Query and rank strategies from databank for Home and dashboard panels."""
    _require_auth(request)
    logger.info(
        "FR-home-routes-dashboard: fetching dashboard results for %s", project_id
    )
    service = _get_service(request)
    try:
        results = service.get_dashboard_results(
            project_id=project_id,
            databank_id=databank_id,
            sample_type=sample_type,
            metric=metric,
            limit=limit,
        )
        return _envelope(results)
    except DomainError as err:
        if err.code in ("PROJECT_FILE_NOT_FOUND", "DATABANK_NOT_FOUND"):
            raise TransportError(ErrorCode.NOT_FOUND, err.message) from err
        if err.code == "INVALID_PROJECT_ID":
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        if err.code in ("INVALID_METRIC", "INVALID_SAMPLE_TYPE"):
            raise TransportError(ErrorCode.VALIDATION, err.message) from err
        raise TransportError(ErrorCode.VALIDATION, err.message) from err


@home_router.get("/project/{project_id}/result/{result_id}")
async def get_stored_result(
    project_id: str, result_id: str, request: Request
) -> dict[str, Any]:
    """Return project-owned stored result details."""
    _require_auth(request)
    try:
        return _envelope(_get_service(request).get_result(project_id, result_id))
    except DomainError as error:
        raise TransportError(ErrorCode.NOT_FOUND, error.message) from error


class SaveAnalysisRequest(BaseModel):
    """Bounded project-owned custom-analysis definitions."""

    names: list[str] = Field(max_length=32)
    expected_revision: int = Field(ge=1, strict=True)


@home_router.post("/project/{project_id}/analysis")
async def save_analysis(
    project_id: str, payload: SaveAnalysisRequest, request: Request
) -> dict[str, Any]:
    """Save shared analysis definitions without executing unconfigured providers."""
    _require_auth(request)
    try:
        return _envelope(
            _get_service(request).save_project_analysis(
                project_id, payload.names, payload.expected_revision
            )
        )
    except DomainError as error:
        code = ErrorCode.CONFLICT if error.code == "CONFLICT" else ErrorCode.VALIDATION
        raise TransportError(code, error.message) from error
