"""Central API router aggregating platform and domain REST routers.

Description:
    Composes and coordinates all dedicated REST API routers across platform
    domains (settings, and in subsequent phases sessions, jobs, resources,
    diagnostics, and workspaces). Serves as the single root router mount point
    for the FastAPI application lifecycle during bootstrap.

Purpose:
    FEAT-API-ROUTER: Centralized API router composition and mounting.

Key Capabilities:
    - FR-API-ROUTER-COMPOSITION: Compose individual domain routers into root router.
      Associated: `create_api_router()`
      Logging: DEBUG composition counts and mounted route prefixes.

Python API Usage:
    ```python
    from app.api.router import create_api_router
    from app.host.settings import settings

    root_router = create_api_router(settings)
    ```

CLI Usage:
    The central API router is composed by host bootstrap:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Request

from app.api.settings import create_settings_router
from app.host.logging import get_logger
from app.host.settings import HostSettings
from app.host.settings import settings as default_settings

__all__ = [
    "create_api_router",
]

logger = get_logger(__name__)


def create_api_router(
    settings_instance: HostSettings | None = None,
    *,
    require_session: Callable[[Request], None] | None = None,
    on_settings_updated: Callable[[int], None] | None = None,
    prefix: str | None = None,
) -> APIRouter:
    """Create and assemble the unified root REST API router.

    Args:
        settings_instance: HostSettings instance. Defaults to global singleton.
        require_session: Optional session access dependency for protected routes.
        on_settings_updated: Optional callback triggered on settings revision commit.
        prefix: Optional URL prefix override. Defaults to settings.api_prefix.

    Returns:
        Configured FastAPI APIRouter containing all registered domain endpoints.
    """
    resolved_settings = (
        settings_instance if settings_instance is not None else default_settings
    )
    resolved_prefix = prefix if prefix is not None else resolved_settings.api_prefix

    router = APIRouter(prefix=resolved_prefix)

    # Mount Settings domain router
    settings_router = create_settings_router(
        resolved_settings,
        require_session=require_session,
        on_updated=on_settings_updated,
    )
    router.include_router(settings_router)

    logger.debug(
        "FR-API-ROUTER-COMPOSITION: Composed central API router with prefix %s",
        resolved_prefix,
        extra={
            "fr_id": "FR-API-ROUTER-COMPOSITION",
            "prefix": resolved_prefix,
        },
    )
    return router
