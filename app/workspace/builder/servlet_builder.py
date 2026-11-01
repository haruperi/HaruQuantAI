"""Servlet builder HTTP/RPC request dispatcher and controller.

Description:
    Bridges frontend builderClient requests to typed AppBuilderService and
    TaskBuildRunner operations, routing start, pause, resume, stop, status,
    and indicator calibration actions with standardized error codes and envelopes.

Purpose:
    FEAT-BUILDER-SERVLET-DISPATCHER: HTTP/RPC action routing and request handling.

Key Capabilities:
    - FR-builder-dispatch-actions: Route build lifecycle commands to AppBuilderService.
    - FR-builder-dispatch-calibrate: Route indyTester/calibrate requests to
      TaskBuildRunner.
    - FR-builder-action-guard: Reject unrecognized actions with BUILDER_UNKNOWN_ACTION.

Python API Usage:
    from app.workspace.builder.servlet_builder import ServletBuilderDispatcher
    dispatcher = ServletBuilderDispatcher()
    resp = dispatcher.dispatch("build/status", {"project_id": "proj_1"})

CLI Usage:
    python -c "from app.workspace.builder.servlet_builder import (
        ServletBuilderDispatcher,
    ); print(ServletBuilderDispatcher())"
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.builder.app_builder import AppBuilderService
from app.workspace.builder.common import wrap_response
from app.workspace.builder.settings_blocks import BlocksSelectionSettings
from app.workspace.builder.task_build import TaskBuildRunner

logger = get_logger(__name__)


class ServletBuilderDispatcher:
    """HTTP/RPC dispatcher for Builder workspace controller actions."""

    def __init__(self, service: AppBuilderService | None = None) -> None:
        """Initialize dispatcher with AppBuilderService instance."""
        self._service = service or AppBuilderService()

    def dispatch(
        self, action: str, payload: Mapping[str, Any]
    ) -> StandardResponse[Any]:
        """Dispatch incoming action request to appropriate service method.

        Args:
            action: Command identifier string.
            payload: Request arguments mapping.

        Returns:
            StandardResponse containing action result.

        Raises:
            DomainError: If action is unrecognized.
        """
        logger.debug(
            "Dispatching action '%s' with payload keys: %s",
            action,
            list(payload.keys()),
        )
        project_id = str(payload.get("project_id", "default_project"))

        if action == "build/status":
            return self._service.get_state(project_id)

        if action == "build/start":
            return self._service.start(project_id)

        if action == "build/pause":
            return self._service.pause(project_id)

        if action == "build/resume":
            return self._service.resume(project_id)

        if action == "build/stop":
            return self._service.stop(project_id)

        if action == "indyTester/calibrate":
            blocks_raw = payload.get("blocks")
            blocks = (
                BlocksSelectionSettings(**blocks_raw)
                if isinstance(blocks_raw, dict)
                else BlocksSelectionSettings()
            )
            bars = payload.get("bars", ())
            ranges = TaskBuildRunner.calibrate_indicators(blocks, bars)
            json_ranges = {k: list(v) for k, v in ranges.items()}
            return wrap_response(
                request_id=f"calibrate-{project_id}",
                data=ranges,
                json_payload=json_ranges,
            )

        raise DomainError(
            code="BUILDER_UNKNOWN_ACTION",
            message=f"Unrecognized Builder action: '{action}'",
        )
