"""REST API package bridging frontend UI and backend capabilities.

Description:
    Exposes FastAPI routers and REST endpoints providing structured HTTP access
    to core platform capabilities including settings, sessions, diagnostics,
    jobs, resources, discovery, debug console, event streams, and shell runtime.

Purpose:
    FEAT-API-CORE: Centralized REST API routing and transport bridging.

Key Capabilities:
    - FR-API-CORE-ROUTER-EXPORT: Export canonical router factories for platform
      assembly.
      Associated: `create_api_router()`, `create_settings_router()`, etc.
      Logging: DEBUG export inspection during bootstrap composition.

Python API Usage:
    ```python
    from app.api import create_api_router, create_settings_router

    api_router = create_api_router()
    ```

CLI Usage:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from app.api.debug_console import create_debug_console_router
from app.api.diagnostics import (
    create_database_diagnostics_router,
    create_diagnostics_router,
    create_persistence_router,
    create_settings_paths_router,
)
from app.api.discovery import create_discovery_router
from app.api.jobs import create_jobs_router, create_leases_router
from app.api.resources import create_resources_router
from app.api.router import create_api_router
from app.api.sessions import create_auth_router, create_sessions_router
from app.api.settings import create_settings_router
from app.api.shell import create_recovery_router, create_shell_router
from app.api.transport import create_transport_router

__all__ = [
    "create_api_router",
    "create_auth_router",
    "create_database_diagnostics_router",
    "create_debug_console_router",
    "create_diagnostics_router",
    "create_discovery_router",
    "create_jobs_router",
    "create_leases_router",
    "create_persistence_router",
    "create_recovery_router",
    "create_resources_router",
    "create_sessions_router",
    "create_settings_paths_router",
    "create_settings_router",
    "create_shell_router",
    "create_transport_router",
]
