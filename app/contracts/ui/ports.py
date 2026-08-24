"""UI domain presentation ports and protocols."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.ui.models import (
        CapabilityPresentationState,
        ShellSnapshot,
        WorkspaceRoute,
    )


@runtime_checkable
class ComposeShellPresentationCapability(Protocol):
    """Presentation port for assembling and controlling the UI client shell."""

    def assemble_shell(
        self,
        active_workspace_id: str | None,
        current_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        capability_states: dict[str, CapabilityPresentationState] | None = None,
        status_message: str = "Ready",
    ) -> ShellSnapshot:
        """Compose the top-level shell presentation state snapshot.

        Args:
            active_workspace_id: ID of the currently active workspace.
            current_route: Current client route path.
            available_workspaces: Discovered authorized workspace routes.
            capability_states: Mapping of capability IDs to their presentation state.
            status_message: Overall system status description.

        Returns:
            Assembled immutable ShellSnapshot.
        """
        ...

    def discover_workspaces(
        self,
        registered_workspaces: tuple[WorkspaceRoute, ...],
        active_capabilities: frozenset[str],
    ) -> tuple[WorkspaceRoute, ...]:
        """Discover authorized workspace routes compatible with active capabilities.

        Args:
            registered_workspaces: All candidate workspace routes.
            active_capabilities: Set of active capability identifiers.

        Returns:
            Tuple of authorized, compatible workspace routes.
        """
        ...

    def switch_workspace(
        self,
        current_snapshot: ShellSnapshot,
        target_workspace_id: str,
    ) -> ShellSnapshot:
        """Switch the active workspace while preserving state and isolating input.

        Args:
            current_snapshot: Current shell state.
            target_workspace_id: Target workspace identifier.

        Returns:
            Updated ShellSnapshot with new active workspace.
        """
        ...

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
        """Resolve granular presentation state for a capability.

        Args:
            capability_id: Capability identifier to evaluate.
            active_capabilities: Set of active capabilities.
            loading_capabilities: Set of capabilities currently preparing.
            degraded_capabilities: Set of degraded capabilities.
            disabled_capabilities: Set of disabled capabilities.
            unauthorized_capabilities: Set of unauthorized capabilities.
            incompatible_capabilities: Set of incompatible capabilities.

        Returns:
            Resolved CapabilityPresentationState enum value.
        """
        ...

    def restore_route(
        self,
        requested_route: str,
        available_workspaces: tuple[WorkspaceRoute, ...],
        default_fallback: str = "/home",
    ) -> str:
        """Restore an authorized route or return a deterministic fallback.

        Args:
            requested_route: Stored or requested route path.
            available_workspaces: Available authorized workspaces.
            default_fallback: Fallback route when requested is unavailable.

        Returns:
            Valid route path string.
        """
        ...
