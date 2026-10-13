"""REST API package bridging frontend UI and backend capabilities.

Description:
    Exposes FastAPI routers and REST endpoints providing structured HTTP access
    to core platform capabilities including settings, sessions, diagnostics,
    jobs, and domain workspaces.

Purpose:
    FEAT-API-CORE: Centralized REST API routing and transport bridging.

Key Capabilities:
    - FR-API-CORE-ROUTER-EXPORT: Export canonical router factories for platform
      assembly.
      Associated: `create_api_router()`, `create_settings_router()`
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

from app.api.router import create_api_router
from app.api.settings import create_settings_router

__all__ = [
    "create_api_router",
    "create_settings_router",
]
