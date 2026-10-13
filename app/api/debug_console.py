"""Debug console REST API endpoints.

Description:
    Exposes FastAPI routes for querying, filtering, and clearing real-time host
    telemetry ring buffers from browser UI workspaces. Provides endpoints
    matching both `/api/v1/debugconsole` and legacy SQX `/debugconsole` paths.

Purpose:
    FEAT-API-DEBUG-CONSOLE: Dedicated REST API routing for in-memory debug console
    log inspection and ring buffer management.

Key Capabilities:
    - FR-API-DEBUG-CONSOLE-PROJECTION: HTTP endpoints for DebugConsole UI log querying.
      Associated: `get_logs()`, `get_categories()`, `clear_logs()`
      Logging: Emits INFO on log retrieval, category queries, and log clearance.

Python API Usage:
    ```python
    from app.api.debug_console import create_debug_console_router
    from app.host.logging import TelemetryEngine

    router = create_debug_console_router()
    ```

CLI Usage:
    Debug console REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.host.logging import (
    ClearResponse,
    DebugConsoleSnapshot,
    TelemetryEngine,
    get_logger,
)

__all__ = [
    "create_debug_console_router",
]

logger = get_logger(__name__)


def create_debug_console_router(
    engine: TelemetryEngine | None = None,
) -> APIRouter:
    """Create FastAPI router for the browser DebugConsole workspace.

    Provides endpoints matching the UI projection contract and legacy SQX
    plugin path `/debugconsole`.

    Args:
        engine: Optional TelemetryEngine instance. Defaults to active singleton.

    Returns:
        APIRouter configured with DebugConsole projection endpoints.
    """
    router = APIRouter(tags=["debugconsole"])

    def _get_engine() -> TelemetryEngine:
        return engine if engine is not None else TelemetryEngine.get_or_create()

    @router.get(
        "/api/v1/debugconsole/logs",
        response_model=DebugConsoleSnapshot,
        summary="Query DebugConsole logs",
    )
    @router.get(
        "/debugconsole/logs",
        response_model=DebugConsoleSnapshot,
        include_in_schema=False,
    )
    async def get_logs(
        after_cursor: int | None = Query(default=None, description="Cursor offset"),
        category: str = Query(default="All", description="Category filter"),
        query: str | None = Query(default=None, description="Message filter search"),
        limit: int = Query(default=100, ge=1, le=1000, description="Page limit"),
    ) -> DebugConsoleSnapshot:
        eng = _get_engine()
        snapshot = eng.ring_buffer.get_snapshot(
            after_cursor=after_cursor,
            category=category,
            query=query,
            limit=limit,
        )
        logger.debug(
            "FR-API-DEBUG-CONSOLE-PROJECTION: Queried logs (entries=%d, cursor=%d)",
            len(snapshot.entries),
            snapshot.newest_cursor,
            extra={
                "fr_id": "FR-API-DEBUG-CONSOLE-PROJECTION",
                "entries_count": len(snapshot.entries),
                "cursor": snapshot.newest_cursor,
            },
        )
        return snapshot

    @router.get(
        "/api/v1/debugconsole/categories",
        response_model=list[str],
        summary="List active DebugConsole categories",
    )
    @router.get(
        "/debugconsole/categories",
        response_model=list[str],
        include_in_schema=False,
    )
    async def get_categories() -> list[str]:
        eng = _get_engine()
        cats = eng.ring_buffer.get_categories()
        logger.debug(
            "FR-API-DEBUG-CONSOLE-PROJECTION: Retrieved categories (count=%d)",
            len(cats),
            extra={
                "fr_id": "FR-API-DEBUG-CONSOLE-PROJECTION",
                "categories_count": len(cats),
            },
        )
        return cats

    @router.post(
        "/api/v1/debugconsole/clear",
        response_model=ClearResponse,
        status_code=status.HTTP_200_OK,
        summary="Clear DebugConsole log buffer",
    )
    @router.post(
        "/debugconsole/clear",
        response_model=ClearResponse,
        status_code=status.HTTP_200_OK,
        include_in_schema=False,
    )
    async def clear_logs() -> ClearResponse:
        eng = _get_engine()
        cleared_cursor = eng.ring_buffer.clear()
        return ClearResponse(cleared=True, cleared_at_cursor=cleared_cursor)

    return router
