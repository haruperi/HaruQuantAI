"""Resource custody, safe archive, and artifact staging REST API endpoints.

Description:
    Exposes FastAPI routes for staging file uploads, JSON payload staging,
    fetching bounded remote HTTP artifacts, publishing staged resources to
    content-addressed immutable storage, querying metadata, downloading raw
    content, tombstoning resources, archive safety inspection, safe contained
    extraction, and staging cache cleanup.

Purpose:
    FEAT-API-RESOURCES: Dedicated REST API routing for host resource custody and
    artifact lifecycle operations.

Key Capabilities:
    - FR-API-RESOURCES-STAGING: HTTP routes for binary file and JSON staging.
      Associated: `ResourceRouterService.stage_upload()`, `stage_json()`
      Logging: Emits INFO on resource staging.
    - FR-API-RESOURCES-ACQUISITION: HTTP route for remote URL fetching into staging.
      Associated: `ResourceRouterService.acquire_remote_endpoint()`
      Logging: Emits INFO on remote artifact acquisition.
    - FR-API-RESOURCES-LIFECYCLE: HTTP routes for publishing, downloading, tombstoning.
      Associated: `publish_resource()`, `get_metadata()`, `get_content()`, `tombstone()`
      Logging: Emits INFO on lifecycle mutations; raises HTTP 404/422 on failure.
    - FR-API-RESOURCES-ARCHIVES: HTTP routes for inspecting and safely
      extracting archives.
      Associated: `inspect_archive_endpoint()`, `extract_archive_endpoint()`
      Logging: Emits INFO on archive operations; rejects Zip-Slip or bomb archives.
    - FR-API-RESOURCES-CLEANUP: HTTP routes for cache status and staging purge.
      Associated: `cache_status()`, `cleanup_staging_endpoint()`
      Logging: Emits INFO on staging garbage collection.

Python API Usage:
    ```python
    from app.api.resources import create_resources_router
    from app.host.resources import ResourceManager

    manager = ResourceManager(base_dir=Path("data/resources"))
    router = create_resources_router(manager)
    ```

CLI Usage:
    Resources REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

import mimetypes
import urllib.parse
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.responses import FileResponse, JSONResponse

from app.host.logging import get_logger
from app.host.resources import (
    AcquireRemoteRequest,
    AcquisitionError,
    ArchiveBombError,
    CorruptResourceError,
    ExtractArchiveRequest,
    InspectArchiveRequest,
    PublishRequest,
    ResourceConflictError,
    ResourceManager,
    ResourceMetadata,
    ResourceNotFoundError,
    ResourceScope,
    ResourceSecurityError,
    ResourceStatus,
    StagingRequest,
    acquire_remote,
)
from app.host.response import StandardResponse as ApiResponse

__all__ = [
    "ResourceRouterService",
    "create_resources_router",
]

logger = get_logger(__name__)


class ResourceRouterService:
    """Internal service adapter translating HTTP requests to ResourceManager actions."""

    def __init__(self, manager: ResourceManager) -> None:
        self._manager = manager

    async def stage_upload(
        self,
        request: Request,
        name: Annotated[str | None, Query()] = None,
        scope: Annotated[ResourceScope, Query()] = ResourceScope.WORKSPACE,
        expires_in_seconds: Annotated[int | None, Query()] = None,
    ) -> Response:
        """Stage an uploaded binary payload."""
        req_id = request.headers.get("x-request-id")
        data = await request.body()
        filename = (
            name or request.headers.get("x-file-name") or f"upload_{uuid.uuid4().hex}"
        )
        meta = self._manager.stage_bytes(
            data,
            name=filename,
            scope=scope,
            expires_in_seconds=expires_in_seconds,
        )
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Resource {meta.resource_id} staged successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def stage_json(
        self,
        request: Request,
        req: StagingRequest,
    ) -> Response:
        """Stage an empty or initialized resource via JSON payload."""
        req_id = request.headers.get("x-request-id")
        meta = self._manager.stage_bytes(
            b"",
            name=req.name,
            scope=req.scope,
            tags=req.tags,
            attributes=req.attributes,
            expires_in_seconds=req.expires_in_seconds,
        )
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Resource {meta.resource_id} staged successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def acquire_remote_endpoint(
        self,
        request: Request,
        req: AcquireRemoteRequest,
    ) -> Response:
        """Fetch remote artifact via HTTP and stage in custody."""
        req_id = request.headers.get("x-request-id")
        res_id = f"res_{uuid.uuid4().hex}"
        url_path = urllib.parse.urlparse(req.url).path
        file_name = req.name or Path(url_path).name or f"remote_{res_id}"

        stage_sub = self._manager.staging_dir / res_id
        stage_sub.mkdir(parents=True, exist_ok=True)
        dest_path = stage_sub / file_name

        try:
            size_bytes, digest = acquire_remote(
                req.url,
                dest_path,
                max_bytes=req.max_bytes,
                timeout_seconds=req.timeout_seconds,
            )
        except (ResourceSecurityError, AcquisitionError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

        mime, _ = mimetypes.guess_type(file_name)
        mime_type = mime or "application/octet-stream"

        meta = ResourceMetadata(
            resource_id=res_id,
            scope=req.scope,
            name=file_name,
            content_hash=digest,
            size_bytes=size_bytes,
            mime_type=mime_type,
            status=ResourceStatus.STAGED,
            created_at_utc=datetime.now(UTC),
            tags=req.tags,
            attributes=req.attributes,
        )
        self._manager.register_resource(meta)
        resp = ApiResponse.success(
            data=meta.model_dump(mode="json"),
            message=f"Remote artifact acquired and staged as {res_id}.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def publish_resource(
        self,
        request: Request,
        resource_id: str,
        req: PublishRequest | None = None,
    ) -> Response:
        """Publish a staged resource to immutable store."""
        req_id = request.headers.get("x-request-id")
        expected = req.expected_hash if req else None
        extra_tags = req.tags if req else None
        try:
            meta = self._manager.publish(
                resource_id, expected_hash=expected, tags=extra_tags
            )
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Resource {resource_id} published successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except (ResourceConflictError, CorruptResourceError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def get_metadata(
        self,
        request: Request,
        resource_id: str,
    ) -> Response:
        """Query metadata for a resource."""
        req_id = request.headers.get("x-request-id")
        try:
            meta = self._manager.get_metadata(resource_id)
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Retrieved metadata for {resource_id}.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def get_content(
        self,
        resource_id: str,
    ) -> Response:
        """Download raw binary content of a resource."""
        try:
            meta = self._manager.get_metadata(resource_id)
            path = self._manager.get_content_path(resource_id)
            return FileResponse(
                path=path,
                media_type=meta.mime_type,
                filename=meta.name,
            )
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def tombstone_resource(
        self,
        request: Request,
        resource_id: str,
    ) -> Response:
        """Tombstone / delete a resource."""
        req_id = request.headers.get("x-request-id")
        try:
            meta = self._manager.tombstone(resource_id)
            resp = ApiResponse.success(
                data=meta.model_dump(mode="json"),
                message=f"Resource {resource_id} tombstoned successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    def inspect_archive_endpoint(
        self,
        request: Request,
        req: InspectArchiveRequest,
    ) -> Response:
        """Safely inspect archive metadata without full unpacking."""
        req_id = request.headers.get("x-request-id")
        try:
            inspection = self._manager.inspect_resource_archive(
                req.resource_id, limits=req.limits
            )
            resp = ApiResponse.success(
                data=inspection.model_dump(mode="json"),
                message=f"Archive {req.resource_id} inspected successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except (ArchiveBombError, ResourceSecurityError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def extract_archive_endpoint(
        self,
        request: Request,
        req: ExtractArchiveRequest,
    ) -> Response:
        """Safely unpack an archive resource within containment."""
        req_id = request.headers.get("x-request-id")
        try:
            dest = self._manager.extract_resource_archive(
                req.resource_id,
                target_subpath=req.target_subpath,
                limits=req.limits,
            )
            resp = ApiResponse.success(
                data={"count": len(dest), "extracted_to": [str(p) for p in dest]},
                message=f"Archive {req.resource_id} extracted successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except ResourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        except (ArchiveBombError, ResourceSecurityError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(exc),
            ) from exc

    def cache_status(
        self,
        request: Request,
    ) -> Response:
        """Return memory cache utilization metrics."""
        req_id = request.headers.get("x-request-id")
        stats = self._manager.cache.get_stats()
        resp = ApiResponse.success(
            data=stats.model_dump(mode="json"),
            message="Cache telemetry retrieved.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def cleanup_staging_endpoint(
        self,
        request: Request,
        max_age_seconds: Annotated[float, Query(ge=0.0)] = 3600.0,
    ) -> Response:
        """Purge expired or orphaned staging directories."""
        req_id = request.headers.get("x-request-id")
        cleaned = self._manager.cleanup_staging(max_age_seconds=max_age_seconds)
        resp = ApiResponse.success(
            data={"purged_count": cleaned},
            message=f"Purged {cleaned} orphaned staging directories.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_resources_router(manager: ResourceManager) -> APIRouter:
    """Create and configure FastAPI APIRouter exposing resource endpoints.

    Args:
        manager: Central host ResourceManager instance.

    Returns:
        Configured FastAPI APIRouter.
    """
    service = ResourceRouterService(manager)
    router = APIRouter(prefix="/resources", tags=["resources"])

    router.add_api_route(
        "/stage/upload",
        service.stage_upload,
        methods=["POST"],
        summary="Stage an uploaded multipart file",
    )
    router.add_api_route(
        "/stage",
        service.stage_json,
        methods=["POST"],
        summary="Stage an artifact via JSON",
    )
    router.add_api_route(
        "/acquire",
        service.acquire_remote_endpoint,
        methods=["POST"],
        summary="Acquire and stage a remote artifact via HTTP",
    )
    router.add_api_route(
        "/{resource_id}/publish",
        service.publish_resource,
        methods=["POST"],
        summary="Publish a staged resource into immutable storage",
    )
    router.add_api_route(
        "/{resource_id}",
        service.get_metadata,
        methods=["GET"],
        summary="Retrieve resource metadata",
    )
    router.add_api_route(
        "/{resource_id}/content",
        service.get_content,
        methods=["GET"],
        summary="Download raw resource binary content",
    )
    router.add_api_route(
        "/{resource_id}",
        service.tombstone_resource,
        methods=["DELETE"],
        summary="Tombstone a resource",
    )
    router.add_api_route(
        "/archive/inspect",
        service.inspect_archive_endpoint,
        methods=["POST"],
        summary="Inspect an archive resource",
    )
    router.add_api_route(
        "/archive/extract",
        service.extract_archive_endpoint,
        methods=["POST"],
        summary="Safely extract an archive resource",
    )
    router.add_api_route(
        "/cache/status",
        service.cache_status,
        methods=["GET"],
        summary="Get artifact cache telemetry",
    )
    router.add_api_route(
        "/staging/cleanup",
        service.cleanup_staging_endpoint,
        methods=["POST"],
        summary="Purge orphaned staging directories",
    )

    logger.debug(
        "Resources REST router initialized",
        extra={"fr_id": "FR-API-RESOURCES-REST-PROJECTION"},
    )
    return router
