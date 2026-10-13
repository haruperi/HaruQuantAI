"""Plugin and workspace discovery REST API endpoints.

Description:
    Exposes FastAPI routes for inspecting discovered dynamic plugins, querying
    plugin records, filtering extension slots, and executing runtime plugin
    lifecycle actions (enable, disable, reload). Acts as the dedicated API
    bridge between browser UI workspaces and the backend discovery engine.

Purpose:
    FEAT-API-DISCOVERY: Dedicated REST API routing for plugin discovery and
    extension slots.

Key Capabilities:
    - FR-API-DISCOVERY-PLUGINS: Query and filter discovered plugins and states.
      Associated: `_DiscoveryEndpointHandler.list_plugins()`, `get_plugin()`
      Logging: DEBUG query telemetry with totals and filters.
    - FR-API-DISCOVERY-ACTIONS: Execute runtime lifecycle transitions over HTTP.
      Associated: `enable_plugin()`, `disable_plugin()`, `reload_plugin()`
      Logging: INFO action status; WARNING failed transitions.
    - FR-API-DISCOVERY-SLOTS: List registered extension slots and attached plugins.
      Associated: `list_slots()`
      Logging: DEBUG slot inventory inspection.

Python API Usage:
    ```python
    from app.api.discovery import create_discovery_router
    from app.host.discovery import default_lifecycle_manager

    router = create_discovery_router(default_lifecycle_manager)
    ```

CLI Usage:
    Discovery REST endpoints are mounted by the host bootstrap runtime:
    ```bash
    uv run python -m app.main
    ```
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.host.discovery import (
    PluginLifecycleManager,
    PluginListResponse,
    PluginRecord,
    PluginState,
    PluginSummary,
    SlotSummary,
    default_lifecycle_manager,
)
from app.host.logging import get_logger

__all__ = [
    "create_discovery_router",
]

logger = get_logger(__name__)


class _DiscoveryEndpointHandler:
    """REST endpoint handlers for plugin discovery projections."""

    def __init__(self, manager: PluginLifecycleManager) -> None:
        self.manager: PluginLifecycleManager = manager

    async def list_plugins(
        self,
        slot: Annotated[str | None, Query(description="Filter by slot ID")] = None,
        state: Annotated[
            PluginState | None, Query(description="Filter by state")
        ] = None,
    ) -> PluginListResponse:
        """List all discovered plugins with optional filtering."""
        records = self.manager.records.values()
        summaries: list[PluginSummary] = []
        states_count: dict[str, int] = {}

        for rec in records:
            s_name = rec.state.value
            states_count[s_name] = states_count.get(s_name, 0) + 1

            if slot is not None and rec.manifest.slot != slot:
                continue
            if state is not None and rec.state != state:
                continue

            summaries.append(
                PluginSummary(
                    id=rec.manifest.id,
                    name=rec.manifest.name,
                    version=rec.manifest.version,
                    slot=rec.manifest.slot,
                    state=rec.state,
                    enabled=rec.manifest.enabled,
                    description=rec.manifest.description,
                    package_dir=rec.package_dir,
                    error_message=rec.error_message,
                    discovered_at=rec.discovered_at,
                    attached_at=rec.attached_at,
                )
            )

        logger.debug(
            "FR-API-DISCOVERY-PLUGINS: Queried plugins list (total=%d, filtered=%d)",
            len(records),
            len(summaries),
            extra={
                "fr_id": "FR-API-DISCOVERY-PLUGINS",
                "total": len(records),
                "filtered": len(summaries),
            },
        )
        return PluginListResponse(
            total=len(summaries),
            states_count=states_count,
            plugins=summaries,
        )

    async def get_plugin(self, plugin_id: str) -> PluginRecord:
        """Retrieve full details of a specific plugin."""
        record = self.manager.get_record(plugin_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        return record

    async def enable_plugin(self, plugin_id: str) -> PluginRecord:
        """Enable and attach a plugin."""
        success = self.manager.enable(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=rec.error_message or "Failed to enable plugin",
            )
        return rec

    async def disable_plugin(self, plugin_id: str) -> PluginRecord:
        """Disable a plugin and release its attached resources."""
        success = self.manager.disable(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to disable plugin",
            )
        return rec

    async def reload_plugin(self, plugin_id: str) -> PluginRecord:
        """Reload a plugin by disabling, re-reading manifest, and re-attaching."""
        success = self.manager.reload(plugin_id)
        rec = self.manager.get_record(plugin_id)
        if rec is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin '{plugin_id}' not found",
            )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=rec.error_message or "Failed to reload plugin",
            )
        return rec

    async def list_slots(self) -> list[SlotSummary]:
        """List all extension slots and currently attached plugins."""
        slots = self.manager.engine.slot_registry.list_slots()
        records = self.manager.records.values()

        summaries: list[SlotSummary] = []
        for s in slots:
            attached = [
                r.manifest.id
                for r in records
                if r.manifest.slot == s.slot_id and r.state == PluginState.ATTACHED
            ]
            summaries.append(
                SlotSummary(
                    slot_id=s.slot_id,
                    description=s.description,
                    multi_instance=s.multi_instance,
                    required_capabilities=s.required_capabilities,
                    attached_plugins=attached,
                )
            )
        return summaries


def create_discovery_router(
    manager: PluginLifecycleManager | None = None,
) -> APIRouter:
    """Create and return FastAPI router for browser plugin queries.

    Fires FR-API-DISCOVERY-PLUGINS.
    """
    mgr = manager or default_lifecycle_manager
    handler = _DiscoveryEndpointHandler(mgr)
    router = APIRouter(prefix="/discovery", tags=["Discovery"])

    router.add_api_route(
        "/plugins",
        handler.list_plugins,
        methods=["GET"],
        response_model=PluginListResponse,
        summary="List discovered plugins",
    )
    router.add_api_route(
        "/plugins/{plugin_id}",
        handler.get_plugin,
        methods=["GET"],
        response_model=PluginRecord,
        summary="Get plugin details",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/enable",
        handler.enable_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Enable and attach plugin",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/disable",
        handler.disable_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Disable and teardown plugin",
    )
    router.add_api_route(
        "/plugins/{plugin_id}/reload",
        handler.reload_plugin,
        methods=["POST"],
        response_model=PluginRecord,
        summary="Reload plugin",
    )
    router.add_api_route(
        "/slots",
        handler.list_slots,
        methods=["GET"],
        response_model=list[SlotSummary],
        summary="List extension slots",
    )

    return router
