"""Home workspace package.

Description:
    Exports the Home workspace router, service coordinator, and navigation metadata.
Purpose:
    FEAT-HOME-WORKSPACE: Landing, environment diagnostics, and shared project workflows.
Key Capabilities:
    - FR-home-workspace-export: Export router and services for host integration.
Python API Usage:
    from app.workspace.home import home_router, HomeService, HomeNavigation
CLI Usage:
    uv run python -m pytest tests/workspace/home/ -q
"""

from app.workspace.home.navigation import HomeNavigation
from app.workspace.home.routes import home_router
from app.workspace.home.service import HomeService

__all__ = ["HomeNavigation", "HomeService", "home_router"]
