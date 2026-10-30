"""Workspace integration facade for AppGridControl.

Description:
    Provides the primary workspace service entrypoint for grid computing management,
    consuming the core RemoteComputeCoordinator and exposing cluster topology and
    job execution query APIs without implementing a redundant scheduler.

Purpose:
    FEAT-GRID-CONTROL: Canonical workspace service for distributed compute management.

Key Capabilities:
    - FR-GRID-WORKSPACE-FACADE: Provide unified workspace interface for grid status
      and cluster compute management.

Python API Usage:
    from app.workspace.grid_control.workspace import GridControlWorkspaceService
    workspace = GridControlWorkspaceService()
    data = workspace.get_data()

CLI Usage:
    uv run python -m app.workspace.grid_control.workspace
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.host.logging import get_logger
from app.workspace.grid_control.service import GridControlService

if TYPE_CHECKING:
    from datetime import datetime

    from app.core.grid.contracts import GridTopologyInfo, RemoteWorkerNode
    from app.workspace.grid_control.models import GridDataPayload

__all__ = ["GridControlWorkspaceService"]

_logger = get_logger(__name__)


class GridControlWorkspaceService:
    """Workspace service facade for AppGridControl."""

    def __init__(self, service: GridControlService | None = None) -> None:
        """Initialize workspace service with underlying GridControlService."""
        self.service = service or GridControlService()
        _logger.info(
            "FR-GRID-WORKSPACE-FACADE: Initialized GridControlWorkspaceService"
        )

    def get_data(self, now_utc: datetime | None = None) -> GridDataPayload:
        """Fetch current grid job queues snapshot."""
        _logger.debug("FR-GRID-WORKSPACE-FACADE: Fetching grid data snapshot")
        return self.service.get_grid_data(now_utc)

    def get_topology(self, now_utc: datetime | None = None) -> GridTopologyInfo:
        """Fetch active cluster compute topology."""
        _logger.debug("FR-GRID-WORKSPACE-FACADE: Fetching cluster topology")
        return self.service.get_topology(now_utc)

    def register_node(self, node: RemoteWorkerNode) -> None:
        """Register a worker node with the compute cluster."""
        _logger.info(
            "FR-GRID-WORKSPACE-FACADE: Registering worker node %s", node.worker_id
        )
        self.service.register_worker(node)
