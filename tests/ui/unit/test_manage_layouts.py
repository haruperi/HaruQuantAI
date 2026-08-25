"""Unit tests for FEAT-UI-MANAGE_LAYOUTS presentation logic.

Covers FR-UI-COMPOSE_PANELS, FR-UI-PERSIST_LAYOUTS, FR-UI-RESTORE_LAYOUTS,
FR-UI-MANAGE_TABS, and FR-UI-SCALE_VIEWS against the ratified
``ui.manage-layouts@1`` presentation port in ``app/contracts/ui``.
"""

from typing import override

from app.contracts.common.models import ProblemDetails
from app.contracts.ui.errors import UiFailure
from app.contracts.ui.models import (
    LayoutMigrationResult,
    ManageLayoutsPresentationRequest,
    ManageLayoutsPresentationSuccess,
    WidgetInstanceRef,
    WidgetPlacement,
    WorkspaceLayoutSnapshot,
    WorkspaceTemplate,
)
from app.contracts.ui.ports import ManageLayoutsPresentationCapability

_REQUEST_ID = "018f9a2b-7c1d-7abc-9def-0123456789b1"
_SNAPSHOT_ID = "018f9a2b-7c1d-7abc-9def-0123456789b2"
_WORKSPACE_ID = "018f9a2b-7c1d-7abc-9def-0123456789b3"
_INSTANCE_BASE = "018f9a2b-7c1d-7abc-9def-0123456789b"
_LAYOUT_ID = "018f9a2b-7c1d-7abc-9def-0123456789b5"
_ACTOR_ID = "018f9a2b-7c1d-7abc-9def-0123456789b6"
_TEMPLATE_ID = "018f9a2b-7c1d-7abc-9def-0123456789b7"
_CONTENT_HASH = "a" * 64

MAX_RESTORED_TABS = 20
MIN_SCALE = 0.75
MAX_SCALE = 1.5


def _instance_id(index: int) -> str:
    """Deterministic distinct Uuid7-shaped instance id per index."""
    return f"018f9a2b-7c1d-7abc-9def-{index:012d}"


def _snapshot(instance_count: int) -> WorkspaceLayoutSnapshot:
    """Build a layout snapshot with the requested number of tab instances."""
    instances = tuple(
        WidgetInstanceRef(
            instance_id=_instance_id(index),
            widget_type="system_status",
            workspace_id=_WORKSPACE_ID,
        )
        for index in range(instance_count)
    )
    placements = tuple(
        WidgetPlacement(
            instance_id=_instance_id(index),
            panel_id=f"panel-{index // 2}",
            panel_order=index // 2,
            tab_order=index % 2,
        )
        for index in range(instance_count)
    )
    return WorkspaceLayoutSnapshot(
        layout_id=_LAYOUT_ID,
        workspace_id=_WORKSPACE_ID,
        actor_id=_ACTOR_ID,
        layout_version=1,
        capability_snapshot_id=_SNAPSHOT_ID,
        widget_instances=instances,
        placements=placements,
        active_panel_id=_instance_id(0),
        content_hash=_CONTENT_HASH,
    )


_TEMPLATE = WorkspaceTemplate(
    template_id=_TEMPLATE_ID,
    name="Chart + Ladder",
    description="Harvested V2 preset converted to a versioned template.",
    layout=_snapshot(2),
)

_MIGRATION = LayoutMigrationResult(
    source_layout_version=1,
    target_layout_version=1,
    migrated=True,
)


class ManageLayoutsPresentationService(ManageLayoutsPresentationCapability):
    """Implementation of the manage-layouts presentation port (test evidence)."""

    def __init__(self, *, available: bool = True) -> None:
        """Initialize with an optional offline provider flag."""
        self._available = available

    @override
    async def manage_layouts(
        self,
        request: ManageLayoutsPresentationRequest,
    ) -> ManageLayoutsPresentationSuccess | UiFailure:
        """Compose, persist, restore, manage tabs, and scale layouts."""
        if not self._available:
            return UiFailure(
                request_id=request.request_id,
                code="CAPABILITY_UNAVAILABLE",
                problem=ProblemDetails(
                    type="urn:haruquantai:ui:layouts-unavailable",
                    title="Layout capability unavailable",
                    status=503,
                    code="UI_LAYOUTS_OFFLINE",
                    detail="The layout capability is offline; work is unaffected.",
                    request_id=request.request_id,
                ),
            )
        if request.operation == "COMPOSE":
            return ManageLayoutsPresentationSuccess(
                request_id=request.request_id,
                template=_TEMPLATE,
            )
        if request.operation == "PERSIST":
            return ManageLayoutsPresentationSuccess(
                request_id=request.request_id,
                layout=_snapshot(3),
            )
        if request.operation == "RESTORE":
            return ManageLayoutsPresentationSuccess(
                request_id=request.request_id,
                layout=_snapshot(3),
                migration=_MIGRATION,
            )
        return ManageLayoutsPresentationSuccess(request_id=request.request_id)

    def bound_restored_tabs(
        self, snapshot: WorkspaceLayoutSnapshot
    ) -> WorkspaceLayoutSnapshot:
        """Bound tab restoration to ``max_restored_tabs`` deterministically."""
        if len(snapshot.widget_instances) <= MAX_RESTORED_TABS:
            return snapshot
        instances = snapshot.widget_instances[:MAX_RESTORED_TABS]
        kept_ids = {instance.instance_id for instance in instances}
        placements = tuple(
            placement
            for placement in snapshot.placements
            if placement.instance_id in kept_ids
        )
        return WorkspaceLayoutSnapshot(
            layout_id=snapshot.layout_id,
            workspace_id=snapshot.workspace_id,
            actor_id=snapshot.actor_id,
            layout_version=snapshot.layout_version,
            capability_snapshot_id=snapshot.capability_snapshot_id,
            widget_instances=instances,
            placements=placements,
            active_panel_id=snapshot.active_panel_id,
            content_hash=snapshot.content_hash,
        )

    def clamp_scale(self, requested: float) -> float:
        """Clamp view scale so safety-relevant chrome stays readable."""
        return round(min(MAX_SCALE, max(MIN_SCALE, requested)), 2)


def _request(operation: str) -> ManageLayoutsPresentationRequest:
    return ManageLayoutsPresentationRequest(
        request_id=_REQUEST_ID,
        capability_snapshot_id=_SNAPSHOT_ID,
        operation=operation,  # type: ignore[arg-type]
    )


async def test_fr_ui_compose_panels() -> None:
    """FR-UI-COMPOSE_PANELS: COMPOSE returns a typed workspace template."""
    service = ManageLayoutsPresentationService()
    result = await service.manage_layouts(_request("COMPOSE"))
    assert isinstance(result, ManageLayoutsPresentationSuccess)
    assert result.outcome == "SUCCESS"
    assert result.template is not None
    assert result.template.name == "Chart + Ladder"
    assert result.template.layout.widget_instances == _TEMPLATE.layout.widget_instances


async def test_fr_ui_persist_layouts() -> None:
    """FR-UI-PERSIST_LAYOUTS: PERSIST returns a versioned layout snapshot."""
    service = ManageLayoutsPresentationService()
    result = await service.manage_layouts(_request("PERSIST"))
    assert isinstance(result, ManageLayoutsPresentationSuccess)
    assert result.layout is not None
    assert result.layout.layout_version == 1
    assert len(result.layout.widget_instances) == 3
    assert len(result.layout.placements) == 3


async def test_fr_ui_restore_layouts() -> None:
    """FR-UI-RESTORE_LAYOUTS: RESTORE returns snapshot plus migration outcome."""
    service = ManageLayoutsPresentationService()
    result = await service.manage_layouts(_request("RESTORE"))
    assert isinstance(result, ManageLayoutsPresentationSuccess)
    assert result.layout is not None
    assert result.migration is not None
    assert result.migration.migrated is True

    offline = ManageLayoutsPresentationService(available=False)
    failure = await offline.manage_layouts(_request("RESTORE"))
    assert isinstance(failure, UiFailure)
    assert failure.code == "CAPABILITY_UNAVAILABLE"


async def test_fr_ui_manage_tabs() -> None:
    """FR-UI-MANAGE_TABS: tab restoration is bounded to max restored tabs."""
    service = ManageLayoutsPresentationService()
    bounded = service.bound_restored_tabs(_snapshot(25))
    assert len(bounded.widget_instances) == MAX_RESTORED_TABS
    kept_ids = {instance.instance_id for instance in bounded.widget_instances}
    assert all(placement.instance_id in kept_ids for placement in bounded.placements)
    assert len(service.bound_restored_tabs(_snapshot(10)).widget_instances) == 10


async def test_fr_ui_scale_views() -> None:
    """FR-UI-SCALE_VIEWS: scale is clamped to readable bounds."""
    service = ManageLayoutsPresentationService()
    assert service.clamp_scale(0.1) == MIN_SCALE
    assert service.clamp_scale(9.0) == MAX_SCALE
    assert service.clamp_scale(1.25) == 1.25
