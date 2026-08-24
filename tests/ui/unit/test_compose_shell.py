"""Unit tests for FEAT-UI-COMPOSE_SHELL presentation logic."""

from typing import override

from app.contracts.ui.models import (
    CapabilityPresentationState,
    ShellSnapshot,
    WorkspaceRoute,
)
from app.contracts.ui.ports import ComposeShellPresentationCapability


class ShellPresentationService(ComposeShellPresentationCapability):
    """Implementation of ComposeShellPresentationCapability presentation port."""

    @override
    def assemble_shell(
        self,
        active_workspace_id: str | None,
        current_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        capability_states: dict[str, CapabilityPresentationState] | None = None,
        status_message: str = "Ready",
    ) -> ShellSnapshot:
        """Compose the top-level shell presentation state snapshot."""
        states = capability_states if capability_states is not None else {}
        is_ready = not any(
            state == CapabilityPresentationState.LOADING for state in states.values()
        )
        return ShellSnapshot(
            active_workspace_id=active_workspace_id,
            current_route=current_route,
            available_workspaces=available_workspaces,
            capability_states=states,
            is_ready=is_ready,
            status_message=status_message,
        )

    @override
    def discover_workspaces(
        self,
        registered_workspaces: tuple[WorkspaceRoute, ...],
        active_capabilities: frozenset[str],
    ) -> tuple[WorkspaceRoute, ...]:
        """Discover authorized workspace routes compatible with active capabilities."""
        discovered: list[WorkspaceRoute] = []
        for route in registered_workspaces:
            if not route.is_authorized:
                continue
            if set(route.required_capabilities).issubset(active_capabilities):
                discovered.append(route)
        return tuple(discovered)

    @override
    def switch_workspace(
        self,
        current_snapshot: ShellSnapshot,
        target_workspace_id: str,
    ) -> ShellSnapshot:
        """Switch the active workspace while preserving state and isolating input."""
        target_route = next(
            (
                ws
                for ws in current_snapshot.available_workspaces
                if ws.workspace_id == target_workspace_id
            ),
            None,
        )
        if target_route is None:
            raise ValueError(
                f"Target workspace '{target_workspace_id}' is not available"
            )

        return ShellSnapshot(
            active_workspace_id=target_workspace_id,
            current_route=target_route.route_path,
            available_workspaces=current_snapshot.available_workspaces,
            capability_states=current_snapshot.capability_states,
            is_ready=current_snapshot.is_ready,
            status_message=f"Workspace active: {target_route.display_name}",
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
        """Resolve granular presentation state for a capability."""
        priority_states: tuple[
            tuple[frozenset[str], CapabilityPresentationState], ...
        ] = (
            (unauthorized_capabilities, CapabilityPresentationState.UNAUTHORIZED),
            (incompatible_capabilities, CapabilityPresentationState.INCOMPATIBLE),
            (disabled_capabilities, CapabilityPresentationState.DISABLED),
            (degraded_capabilities, CapabilityPresentationState.DEGRADED),
            (loading_capabilities, CapabilityPresentationState.LOADING),
            (active_capabilities, CapabilityPresentationState.READY),
        )
        for cap_set, state in priority_states:
            if capability_id in cap_set:
                return state
        return CapabilityPresentationState.UNAVAILABLE

    @override
    def restore_route(
        self,
        requested_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        default_fallback: str = "/home",
    ) -> str:
        """Restore an authorized route or return a deterministic fallback."""
        authorized_paths = {
            ws.route_path for ws in available_workspaces if ws.is_authorized
        }
        if requested_route in authorized_paths:
            return requested_route
        return default_fallback


def test_fr_ui_assemble_shell() -> None:
    """FR-UI-ASSEMBLE_SHELL: Compose shell snapshot from active capability snapshot."""
    service = ShellPresentationService()
    ws1 = WorkspaceRoute(
        workspace_id="ws-main",
        route_path="/workspaces/main",
        display_name="Main Workspace",
    )
    snapshot = service.assemble_shell(
        active_workspace_id="ws-main",
        current_route="/workspaces/main",
        available_workspaces=(ws1,),
        capability_states={
            "workspace.manage-workspaces@1": CapabilityPresentationState.READY
        },
        status_message="System operational",
    )

    assert snapshot.active_workspace_id == "ws-main"
    assert snapshot.current_route == "/workspaces/main"
    assert len(snapshot.available_workspaces) == 1
    assert snapshot.is_ready is True
    assert snapshot.status_message == "System operational"


def test_fr_ui_discover_workspaces() -> None:
    """FR-UI-DISCOVER_WORKSPACES: Discover authorized workspace routes dynamically."""
    service = ShellPresentationService()
    ws_public = WorkspaceRoute(
        workspace_id="ws-public",
        route_path="/home",
        display_name="Home",
        required_capabilities=(),
        is_authorized=True,
    )
    ws_diag = WorkspaceRoute(
        workspace_id="ws-diag",
        route_path="/diagnostics",
        display_name="Diagnostics",
        required_capabilities=("workspace.build-diagnostics@1",),
        is_authorized=True,
    )
    ws_trading = WorkspaceRoute(
        workspace_id="ws-trading",
        route_path="/trading",
        display_name="Trading",
        required_capabilities=("trading.execute-orders@1",),
        is_authorized=True,
    )
    ws_restricted = WorkspaceRoute(
        workspace_id="ws-admin",
        route_path="/admin",
        display_name="Admin",
        required_capabilities=(),
        is_authorized=False,
    )

    all_routes = (ws_public, ws_diag, ws_trading, ws_restricted)
    active_caps = frozenset(["workspace.build-diagnostics@1"])

    discovered = service.discover_workspaces(all_routes, active_caps)
    discovered_ids = {ws.workspace_id for ws in discovered}

    assert "ws-public" in discovered_ids
    assert "ws-diag" in discovered_ids
    assert "ws-trading" not in discovered_ids
    assert "ws-admin" not in discovered_ids


def test_fr_ui_switch_workspaces() -> None:
    """FR-UI-SWITCH_WORKSPACES: Switch workspaces preserving scoped state."""
    service = ShellPresentationService()
    ws1 = WorkspaceRoute(workspace_id="ws-1", route_path="/ws1", display_name="WS 1")
    ws2 = WorkspaceRoute(workspace_id="ws-2", route_path="/ws2", display_name="WS 2")

    initial = service.assemble_shell(
        active_workspace_id="ws-1",
        current_route="/ws1",
        available_workspaces=(ws1, ws2),
    )

    updated = service.switch_workspace(initial, "ws-2")
    assert updated.active_workspace_id == "ws-2"
    assert updated.current_route == "/ws2"
    assert updated.status_message == "Workspace active: WS 2"


def test_fr_ui_show_capability_state() -> None:
    """FR-UI-SHOW_CAPABILITY_STATE: Distinguish all granular capability states."""
    service = ShellPresentationService()
    active = frozenset(["cap.ready@1"])
    loading = frozenset(["cap.loading@1"])
    degraded = frozenset(["cap.degraded@1"])
    disabled = frozenset(["cap.disabled@1"])
    unauthorized = frozenset(["cap.unauthorized@1"])
    incompatible = frozenset(["cap.incompatible@1"])

    assert (
        service.resolve_capability_state(
            "cap.ready@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.READY
    )

    assert (
        service.resolve_capability_state(
            "cap.loading@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.LOADING
    )

    assert (
        service.resolve_capability_state(
            "cap.degraded@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.DEGRADED
    )

    assert (
        service.resolve_capability_state(
            "cap.disabled@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.DISABLED
    )

    assert (
        service.resolve_capability_state(
            "cap.unauthorized@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.UNAUTHORIZED
    )

    assert (
        service.resolve_capability_state(
            "cap.incompatible@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.INCOMPATIBLE
    )

    assert (
        service.resolve_capability_state(
            "cap.unknown@1",
            active,
            loading_capabilities=loading,
            degraded_capabilities=degraded,
            disabled_capabilities=disabled,
            unauthorized_capabilities=unauthorized,
            incompatible_capabilities=incompatible,
        )
        == CapabilityPresentationState.UNAVAILABLE
    )


def test_fr_ui_restore_route() -> None:
    """FR-UI-RESTORE_ROUTE: Restore only authorized, compatible routes; otherwise fallback."""
    service = ShellPresentationService()
    ws_valid = WorkspaceRoute(
        workspace_id="ws-valid",
        route_path="/valid",
        display_name="Valid",
        is_authorized=True,
    )
    ws_unauthorized = WorkspaceRoute(
        workspace_id="ws-unauthorized",
        route_path="/secret",
        display_name="Secret",
        is_authorized=False,
    )

    available = (ws_valid, ws_unauthorized)

    # Valid route restored
    assert (
        service.restore_route("/valid", available, default_fallback="/home") == "/valid"
    )

    # Missing or unauthorized route falls back
    assert (
        service.restore_route("/secret", available, default_fallback="/home") == "/home"
    )
    assert (
        service.restore_route("/nonexistent", available, default_fallback="/home")
        == "/home"
    )
