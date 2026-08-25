"""Unit tests for D-UI spatiotemporal workstation foundation wire models."""

from app.contracts.common.models import ValidationIssue
from app.contracts.ui.events import WidgetLifecycleEventPayload
from app.contracts.ui.models import (
    ClientSelectionWire,
    LayoutMigrationResult,
    TemporalContext,
    TemporalCursor,
    TemporalFreshness,
    TemporalGap,
    TemporalResynchronization,
    TemporalSourceRef,
    WidgetInstanceRef,
    WidgetPlacement,
    WidgetRemovalResult,
    WidgetTypeDescriptor,
    WorkspaceLayoutSnapshot,
)

UUID_1 = "01910000-0000-7000-8000-000000000001"
UUID_2 = "01910000-0000-7000-8000-000000000002"
UUID_3 = "01910000-0000-7000-8000-000000000003"
UUID_4 = "01910000-0000-7000-8000-000000000004"
CONTENT_HASH_64 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # pragma: allowlist secret


def test_widget_type_descriptor_validation() -> None:
    """Verify WidgetTypeDescriptor schema version and owning feature requirements."""
    desc = WidgetTypeDescriptor(
        widget_type="research_builder",
        owning_feature="FEAT-UI-RUN_RESEARCH",
        type_version=1,
        time_domains=("LIVE", "PLAYBACK"),
        schema_version=1,
    )
    assert desc.widget_type == "research_builder"
    assert desc.owning_feature == "FEAT-UI-RUN_RESEARCH"
    assert desc.type_version == 1
    assert desc.time_domains == ("LIVE", "PLAYBACK")
    assert desc.schema_version == 1


def test_workspace_layout_snapshot_round_trip() -> None:
    """Verify WorkspaceLayoutSnapshot model structure and content hash integrity."""
    instance = WidgetInstanceRef(
        instance_id=UUID_1,
        widget_type="research_builder",
        workspace_id=UUID_2,
        configuration_version=1,
        state_version=1,
        schema_version=1,
    )
    placement = WidgetPlacement(
        instance_id=UUID_1,
        panel_id="panel-left",
        panel_order=0,
        tab_order=0,
        size_ratio="0.5",
        is_minimized=False,
        is_maximized=False,
        schema_version=1,
    )
    snapshot = WorkspaceLayoutSnapshot(
        layout_id=UUID_3,
        workspace_id=UUID_2,
        actor_id=UUID_4,
        layout_version=1,
        capability_snapshot_id=UUID_1,
        widget_instances=(instance,),
        placements=(placement,),
        active_panel_id=UUID_1,
        content_hash=CONTENT_HASH_64,
        schema_version=1,
    )

    dumped = snapshot.model_dump(mode="json")
    loaded = WorkspaceLayoutSnapshot.model_validate(dumped)
    assert loaded == snapshot
    assert len(loaded.widget_instances) == 1
    assert loaded.widget_instances[0].widget_type == "research_builder"


def test_layout_migration_result_diagnostics() -> None:
    """Verify LayoutMigrationResult model with incompatible widgets and diagnostics."""
    issue = ValidationIssue(
        path=("widget_instances", "unknown_widget"),
        code="INCOMPATIBLE_WIDGET",
        message="Widget type unknown_widget is not registered",
    )
    migration = LayoutMigrationResult(
        source_layout_version=1,
        target_layout_version=2,
        migrated=True,
        incompatible_widgets=("unknown_widget",),
        defaulted_widgets=(),
        diagnostics=(issue,),
        schema_version=1,
    )
    assert migration.migrated is True
    assert "unknown_widget" in migration.incompatible_widgets
    assert len(migration.diagnostics) == 1
    assert migration.diagnostics[0].code == "INCOMPATIBLE_WIDGET"


def test_temporal_context_and_gaps() -> None:
    """Verify spatiotemporal models including cursor, freshness, and gaps."""
    source = TemporalSourceRef(
        source_id=UUID_1,
        source_kind="market_depth",
        clock_id="clock-utc",
        schema_version=1,
    )
    cursor = TemporalCursor(
        source=source,
        sequence=1050,
        cursor_token="tok-1050",
        as_of="2026-08-25T12:00:00.000000Z",
        schema_version=1,
    )
    freshness = TemporalFreshness(
        source=source,
        last_event_at="2026-08-25T12:00:00.000000Z",
        observed_at="2026-08-25T12:00:01.000000Z",
        is_stale=False,
        staleness_reason="",
        schema_version=1,
    )
    gap = TemporalGap(
        source=source,
        from_sequence=1000,
        to_sequence=1049,
        reason="Network packet loss during reconnect",
        schema_version=1,
    )
    resync = TemporalResynchronization(
        context_id=UUID_2,
        outcome="RESYNCED",
        started_at="2026-08-25T12:00:01.000000Z",
        completed_at="2026-08-25T12:00:02.000000Z",
        replayed_from_sequence=1000,
        schema_version=1,
    )

    temporal_ctx = TemporalContext(
        context_id=UUID_2,
        workspace_id=UUID_3,
        domain="LIVE",
        bound_source=source,
        cursor=cursor,
        freshness=freshness,
        open_gaps=(gap,),
        resynchronization=resync,
        schema_version=1,
    )

    assert temporal_ctx.domain == "LIVE"
    assert temporal_ctx.cursor is not None
    assert temporal_ctx.cursor.sequence == 1050
    assert len(temporal_ctx.open_gaps) == 1
    assert temporal_ctx.resynchronization is not None
    assert temporal_ctx.resynchronization.outcome == "RESYNCED"


def test_widget_lifecycle_and_removal_result() -> None:
    """Verify WidgetLifecycleEventPayload and WidgetRemovalResult models."""
    event = WidgetLifecycleEventPayload(
        instance_id=UUID_1,
        widget_type="research_builder",
        phase="REGISTERED",
        schema_version=1,
    )
    assert event.phase == "REGISTERED"

    removal = WidgetRemovalResult(
        instance_id=UUID_1,
        widget_type="research_builder",
        removal_state="REMOVED",
        reversed_effects=("cleanup_subscriptions", "unregistered_widget"),
        focused_fallback="shell-workspace-outlet",
        schema_version=1,
    )
    assert removal.removal_state == "REMOVED"
    assert len(removal.reversed_effects) == 2


def test_client_selection_model() -> None:
    """Verify ClientSelectionWire multi-key and select-all flags."""
    selection = ClientSelectionWire(
        selection_id="sel-grid",
        selected_keys=("row-1", "row-2", "row-3"),
        is_all_selected=False,
        schema_version=1,
    )
    assert len(selection.selected_keys) == 3
    assert selection.is_all_selected is False
