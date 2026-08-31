"""Tests for UI presentation contracts."""

import inspect
import types
from dataclasses import FrozenInstanceError
from typing import override

import pytest
from app.contracts.ui.capabilities import (
    ADMINISTER_SYSTEM_CAPABILITY,
    AUTHOR_STRATEGIES_CAPABILITY,
    COMPOSE_PORTFOLIOS_CAPABILITY,
    COMPOSE_SHELL_CAPABILITY,
    EDIT_CODE_CAPABILITY,
    EDIT_INPUTS_CAPABILITY,
    EDIT_PROJECTS_CAPABILITY,
    ENSURE_ACCESS_CAPABILITY,
    EXPLORE_RESULTS_CAPABILITY,
    EXTEND_VIEWS_CAPABILITY,
    MANAGE_DATA_CAPABILITY,
    MANAGE_LAYOUTS_CAPABILITY,
    MONITOR_WORK_CAPABILITY,
    OPERATE_DATABANKS_CAPABILITY,
    OPERATE_TRADING_CAPABILITY,
    RUN_RESEARCH_CAPABILITY,
    START_WORK_CAPABILITY,
)
from app.contracts.ui.models import (
    AccessibilityPreference,
    CapabilityPresentationState,
    ChartAlternative,
    ClientPageState,
    ClientSelection,
    ConfirmationPlan,
    DraftConflict,
    DraftEnvelope,
    ErrorPresentation,
    FieldDescriptor,
    KeyboardBinding,
    LayoutSnapshot,
    NavigationContribution,
    PanelContribution,
    ProgressPresentation,
    RouteTarget,
    ShellSnapshot,
    StartWorkPresentationRequest,
    StartWorkPresentationSuccess,
    TabContribution,
    UiCommandDescriptor,
    UiFeatureDescriptor,
    UiNotification,
    ViewPreference,
    ViewProjection,
    WorkspaceRoute,
)
from app.contracts.ui.ports import (
    AdministerSystemPresentationCapability,
    AuthorStrategiesPresentationCapability,
    ComposePortfoliosPresentationCapability,
    ComposeShellPresentationCapability,
    EditCodePresentationCapability,
    EditInputsPresentationCapability,
    EditProjectsPresentationCapability,
    EnsureAccessPresentationCapability,
    ExploreResultsPresentationCapability,
    ExtendViewsPresentationCapability,
    ManageDataPresentationCapability,
    ManageLayoutsPresentationCapability,
    MonitorWorkPresentationCapability,
    OperateDatabanksPresentationCapability,
    OperateTradingPresentationCapability,
    RunResearchPresentationCapability,
    StartWorkPresentationCapability,
)


def test_ui_models_instantiation_and_immutability() -> None:
    """Verify UI models are frozen dataclasses."""
    feature_desc = UiFeatureDescriptor(
        feature_id="FEAT-UI-COMPOSE_SHELL",
        name="Compose Shell",
        description="Application shell",
        required_capabilities=("workspace.manage-workspaces@1",),
    )
    assert feature_desc.feature_id == "FEAT-UI-COMPOSE_SHELL"

    with pytest.raises((FrozenInstanceError, AttributeError)):
        feature_desc.name = "Mutated"  # type: ignore[misc]

    route = RouteTarget(path="/workspace", workspace_id="ws-1", title="Workspace")
    nav = NavigationContribution(id="nav-1", label="Workspace", route=route)
    assert nav.route.path == "/workspace"

    cmd = UiCommandDescriptor(
        command_id="cmd-1", title="Save", category="File", shortcut="Ctrl+S"
    )
    assert cmd.command_id == "cmd-1"

    key = KeyboardBinding(
        key_combination="Ctrl+K", command_id="cmd-palette", description="Palette"
    )
    assert key.key_combination == "Ctrl+K"

    view = ViewProjection(view_id="view-1", title="Overview", data_source="api/data")
    assert view.title == "Overview"

    field_desc = FieldDescriptor(
        field_name="symbol", label="Symbol", field_type="string", required=True
    )
    assert field_desc.required is True

    sel = ClientSelection(selection_id="sel-1", selected_keys=("k1", "k2"))
    assert len(sel.selected_keys) == 2

    page = ClientPageState(page_index=1, page_size=25)
    assert page.page_size == 25

    chart = ChartAlternative(
        chart_id="chart-1", title="Equity", summary_text="Upward slope"
    )
    assert chart.chart_id == "chart-1"

    draft = DraftEnvelope(
        draft_id="d-1",
        schema_id="s-1",
        workspace_id="ws-1",
        actor_id="user-1",
        entity_version=1,
        payload={"foo": "bar"},
        created_at_iso="2026-08-24T00:00:00Z",
        updated_at_iso="2026-08-24T00:00:00Z",
    )
    assert draft.entity_version == 1

    conflict = DraftConflict(
        draft_id="d-1",
        base_version=1,
        current_version=2,
        conflicting_fields=("foo",),
    )
    assert conflict.base_version == 1

    confirm = ConfirmationPlan(
        action_id="act-delete",
        target_description="Item 1",
        impact_summary="Irreversible delete",
        affected_count=1,
        is_reversible=False,
        confirmation_hash="abc123hash",
    )
    assert confirm.is_reversible is False

    note = UiNotification(
        notification_id="n-1",
        title="Saved",
        message="Workspace saved",
        severity="success",
    )
    assert note.title == "Saved"

    prog = ProgressPresentation(
        task_id="t-1", stage_name="Compiling", progress_percent=45.0
    )
    assert prog.progress_percent == 45.0

    err = ErrorPresentation(
        error_code="CAPABILITY_UNAVAILABLE",
        title="Capability Unavailable",
        detail="Workspace capability is not active",
    )
    assert err.error_code == "CAPABILITY_UNAVAILABLE"

    panel = PanelContribution(panel_id="p-1", title="Tree", region="left")
    tab = TabContribution(tab_id="tab-1", title="Main.ts", content_view_id="v-1")
    layout = LayoutSnapshot(
        layout_id="l-1",
        workspace_id="ws-1",
        active_panels=(panel,),
        open_tabs=(tab,),
    )
    assert len(layout.active_panels) == 1

    vpref = ViewPreference(theme="dark", density="compact")
    assert vpref.theme == "dark"

    apref = AccessibilityPreference(high_contrast=True)
    assert apref.high_contrast is True

    ws_route = WorkspaceRoute(
        workspace_id="ws-1",
        route_path="/workspace",
        display_name="Workspace",
    )
    assert ws_route.route_path == "/workspace"

    snapshot = ShellSnapshot(
        active_workspace_id="ws-1",
        current_route="/workspace",
        available_workspaces=(ws_route,),
        capability_states={
            "workspace.manage-workspaces@1": CapabilityPresentationState.READY
        },
    )
    assert snapshot.active_workspace_id == "ws-1"
    assert snapshot.is_ready is True


def test_capability_keys() -> None:
    """Verify COMPOSE_SHELL_CAPABILITY specification."""
    assert COMPOSE_SHELL_CAPABILITY.name == "ui.compose-shell"
    assert COMPOSE_SHELL_CAPABILITY.major == 1
    assert COMPOSE_SHELL_CAPABILITY.identifier == "ui.compose-shell@1"


class DummyService(ComposeShellPresentationCapability):
    """Dummy implementation for testing protocol checkability."""

    @override
    def assemble_shell(
        self,
        active_workspace_id: str | None,
        current_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        capability_states: dict[str, CapabilityPresentationState] | None = None,
        status_message: str = "Ready",
    ) -> ShellSnapshot:
        return ShellSnapshot(
            active_workspace_id=active_workspace_id,
            current_route=current_route,
            available_workspaces=available_workspaces,
            capability_states=capability_states or {},
            status_message=status_message,
        )

    @override
    def discover_workspaces(
        self,
        registered_workspaces: tuple[WorkspaceRoute, ...],
        active_capabilities: frozenset[str],
    ) -> tuple[WorkspaceRoute, ...]:
        return tuple(
            ws
            for ws in registered_workspaces
            if set(ws.required_capabilities).issubset(active_capabilities)
        )

    @override
    def switch_workspace(
        self,
        current_snapshot: ShellSnapshot,
        target_workspace_id: str,
    ) -> ShellSnapshot:
        return ShellSnapshot(
            active_workspace_id=target_workspace_id,
            current_route=f"/workspaces/{target_workspace_id}",
            available_workspaces=current_snapshot.available_workspaces,
            capability_states=current_snapshot.capability_states,
        )

    @override
    def resolve_capability_state(
        self,
        capability_id: str,
        active_capabilities: frozenset[str],
        *,
        loading_capabilities: frozenset[str] = frozenset(),
        degraded_capabilities: frozenset[str] = frozenset(),
        disabled_capabilities: frozenset[str] = frozenset(),
        unauthorized_capabilities: frozenset[str] = frozenset(),
        incompatible_capabilities: frozenset[str] = frozenset(),
    ) -> CapabilityPresentationState:
        if capability_id in active_capabilities:
            return CapabilityPresentationState.READY
        return CapabilityPresentationState.UNAVAILABLE

    @override
    def restore_route(
        self,
        requested_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        default_fallback: str = "/home",
    ) -> str:
        valid_paths = {ws.route_path for ws in available_workspaces}
        if requested_route in valid_paths:
            return requested_route
        return default_fallback


def test_ports_runtime_checkable() -> None:
    """Verify runtime checkability of ComposeShellPresentationCapability."""
    service = DummyService()
    assert isinstance(service, ComposeShellPresentationCapability)


# All seventeen ratified UI capability identifiers: the frozen Compose Shell
# v1 port plus the sixteen ratified v1 wire ports.
EXPECTED_UI_CAPABILITY_IDENTIFIERS: frozenset[str] = frozenset(
    {
        "ui.compose-shell@1",
        "ui.start-work@1",
        "ui.manage-layouts@1",
        "ui.edit-inputs@1",
        "ui.author-strategies@1",
        "ui.run-research@1",
        "ui.edit-projects@1",
        "ui.manage-data@1",
        "ui.operate-databanks@1",
        "ui.explore-results@1",
        "ui.compose-portfolios@1",
        "ui.edit-code@1",
        "ui.monitor-work@1",
        "ui.administer-system@1",
        "ui.operate-trading@1",
        "ui.ensure-access@1",
        "ui.extend-views@1",
    }
)


def test_all_ui_capability_keys_exist_with_exact_identifiers() -> None:
    """Verify every UI CapabilityKey constant resolves to its exact identifier."""
    keys = {
        COMPOSE_SHELL_CAPABILITY,
        START_WORK_CAPABILITY,
        MANAGE_LAYOUTS_CAPABILITY,
        EDIT_INPUTS_CAPABILITY,
        AUTHOR_STRATEGIES_CAPABILITY,
        RUN_RESEARCH_CAPABILITY,
        EDIT_PROJECTS_CAPABILITY,
        MANAGE_DATA_CAPABILITY,
        OPERATE_DATABANKS_CAPABILITY,
        EXPLORE_RESULTS_CAPABILITY,
        COMPOSE_PORTFOLIOS_CAPABILITY,
        EDIT_CODE_CAPABILITY,
        MONITOR_WORK_CAPABILITY,
        ADMINISTER_SYSTEM_CAPABILITY,
        OPERATE_TRADING_CAPABILITY,
        ENSURE_ACCESS_CAPABILITY,
        EXTEND_VIEWS_CAPABILITY,
    }
    identifiers = {key.identifier for key in keys}
    assert identifiers == EXPECTED_UI_CAPABILITY_IDENTIFIERS
    assert len(keys) == 17


def _protocol_methods(protocol: type) -> dict[str, types.FunctionType]:
    """Collect the declared public protocol methods of a runtime protocol.

    Args:
        protocol: Protocol class declared under ``app.contracts.ui.ports``.

    Returns:
        Mapping of method name to the declared function object.
    """
    return {
        name: member
        for name, member in vars(protocol).items()
        if isinstance(member, types.FunctionType) and not name.startswith("_")
    }


def test_compose_shell_capability_retains_five_synchronous_methods() -> None:
    """Verify the frozen five-method synchronous Compose Shell v1 port."""
    methods = _protocol_methods(ComposeShellPresentationCapability)
    assert set(methods) == {
        "assemble_shell",
        "discover_workspaces",
        "switch_workspace",
        "resolve_capability_state",
        "restore_route",
    }
    assert all(not inspect.iscoroutinefunction(m) for m in methods.values())


# The sixteen ratified v1 wire ports and their single async request method
# named after the capability action. The two ports whose owner requires
# event delivery additionally declare their subscription method.
ASYNC_PORTS: tuple[tuple[type, str], ...] = (
    (StartWorkPresentationCapability, "start_work"),
    (ManageLayoutsPresentationCapability, "manage_layouts"),
    (EditInputsPresentationCapability, "edit_inputs"),
    (AuthorStrategiesPresentationCapability, "author_strategies"),
    (RunResearchPresentationCapability, "run_research"),
    (EditProjectsPresentationCapability, "edit_projects"),
    (ManageDataPresentationCapability, "manage_data"),
    (OperateDatabanksPresentationCapability, "operate_databanks"),
    (ExploreResultsPresentationCapability, "explore_results"),
    (ComposePortfoliosPresentationCapability, "compose_portfolios"),
    (EditCodePresentationCapability, "edit_code"),
    (MonitorWorkPresentationCapability, "monitor_work"),
    (AdministerSystemPresentationCapability, "administer_system"),
    (OperateTradingPresentationCapability, "operate_trading"),
    (EnsureAccessPresentationCapability, "ensure_access"),
    (ExtendViewsPresentationCapability, "extend_views"),
)

SUBSCRIPTION_PORTS: tuple[tuple[type, str, str], ...] = (
    (
        MonitorWorkPresentationCapability,
        "monitor_work",
        "subscribe_monitor_work_events",
    ),
    (
        OperateTradingPresentationCapability,
        "operate_trading",
        "subscribe_operate_trading_events",
    ),
)

SINGLE_METHOD_PORTS: tuple[tuple[type, str], ...] = tuple(
    (port, request_method)
    for port, request_method in ASYNC_PORTS
    if port not in {subscription_port for subscription_port, _, _ in SUBSCRIPTION_PORTS}
)


@pytest.mark.parametrize(("port", "request_method"), SINGLE_METHOD_PORTS)
def test_async_port_declares_exactly_one_async_request_method(
    port: type, request_method: str
) -> None:
    """Verify each wire port is a runtime-checkable single-method async protocol."""
    assert getattr(port, "_is_runtime_protocol", False) is True
    methods = _protocol_methods(port)
    assert set(methods) == {request_method}
    assert inspect.iscoroutinefunction(methods[request_method])


@pytest.mark.parametrize(("port", "request_method", "subscription"), SUBSCRIPTION_PORTS)
def test_subscription_ports_declare_domain_event_iterator(
    port: type, request_method: str, subscription: str
) -> None:
    """Verify the two owner-required event subscription methods."""
    assert getattr(port, "_is_runtime_protocol", False) is True
    methods = _protocol_methods(port)
    assert set(methods) == {request_method, subscription}
    assert inspect.iscoroutinefunction(methods[request_method])
    assert not inspect.iscoroutinefunction(methods[subscription])
    # ``ports.py`` uses PEP 563 annotations, so the declared return type of
    # the subscription methods is the exact string ``AsyncIterator[DomainEvent]``.
    assert methods[subscription].__annotations__.get("return") == (
        "AsyncIterator[DomainEvent]"
    )


class DummyStartWorkService(StartWorkPresentationCapability):
    """Dummy implementation proving runtime checkability of a wire port."""

    @override
    async def start_work(
        self,
        request: StartWorkPresentationRequest,
    ) -> StartWorkPresentationSuccess:
        return StartWorkPresentationSuccess(request_id=request.request_id)


def test_async_port_runtime_checkable_instance() -> None:
    """Verify a minimal implementation satisfies the async protocol."""
    assert isinstance(DummyStartWorkService(), StartWorkPresentationCapability)
