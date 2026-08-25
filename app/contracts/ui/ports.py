"""UI domain presentation ports and protocols."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.ui.models import (
        CapabilityPresentationState,
        ShellSnapshot,
        WorkspaceRoute,
    )

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.contracts.common.events import DomainEvent
    from app.contracts.ui.errors import UiFailure
    from app.contracts.ui.models import (
        AdministerSystemPresentationRequest,
        AdministerSystemPresentationSuccess,
        AuthorStrategiesPresentationRequest,
        AuthorStrategiesPresentationSuccess,
        ComposePortfoliosPresentationRequest,
        ComposePortfoliosPresentationSuccess,
        EditCodePresentationRequest,
        EditCodePresentationSuccess,
        EditInputsPresentationRequest,
        EditInputsPresentationSuccess,
        EditProjectsPresentationRequest,
        EditProjectsPresentationSuccess,
        EnsureAccessPresentationRequest,
        EnsureAccessPresentationSuccess,
        ExploreResultsPresentationRequest,
        ExploreResultsPresentationSuccess,
        ExtendViewsPresentationRequest,
        ExtendViewsPresentationSuccess,
        ManageDataPresentationRequest,
        ManageDataPresentationSuccess,
        ManageLayoutsPresentationRequest,
        ManageLayoutsPresentationSuccess,
        MonitorWorkPresentationEventSubscription,
        MonitorWorkPresentationRequest,
        MonitorWorkPresentationSuccess,
        OperateDatabanksPresentationRequest,
        OperateDatabanksPresentationSuccess,
        OperateTradingPresentationEventSubscription,
        OperateTradingPresentationRequest,
        OperateTradingPresentationSuccess,
        RunResearchPresentationRequest,
        RunResearchPresentationSuccess,
        StartWorkPresentationRequest,
        StartWorkPresentationSuccess,
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


# ---------------------------------------------------------------------------
# Ratified v1 wire ports (additive; the frozen five-method synchronous
# ComposeShellPresentationCapability above stays byte-for-byte unchanged).
# Each port method name equals the capability action; the shared failure
# envelope is UiFailure. The two owner-required event subscriptions yield
# common DomainEvent records.


@runtime_checkable
class StartWorkPresentationCapability(Protocol):
    """Presentation port for the start-work home and shortcut surface."""

    async def start_work(
        self,
        request: StartWorkPresentationRequest,
    ) -> StartWorkPresentationSuccess | UiFailure:
        """Present home, recent work, shortcuts, and product news.

        Args:
            request: Operation-discriminated start-work presentation
                request.

        Returns:
            The recent routes, shortcuts, or news on success, otherwise a
            structured UI failure.
        """
        ...


@runtime_checkable
class ManageLayoutsPresentationCapability(Protocol):
    """Presentation port for workstation layouts and templates."""

    async def manage_layouts(
        self,
        request: ManageLayoutsPresentationRequest,
    ) -> ManageLayoutsPresentationSuccess | UiFailure:
        """Compose, persist, restore, and scale widget layouts.

        Args:
            request: Operation-discriminated manage-layouts presentation
                request.

        Returns:
            The layout snapshot, migration outcome, or template on
            success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class EditInputsPresentationCapability(Protocol):
    """Presentation port for schema-driven inputs, drafts, and confirmations."""

    async def edit_inputs(
        self,
        request: EditInputsPresentationRequest,
    ) -> EditInputsPresentationSuccess | UiFailure:
        """Render fields, validate, preserve drafts, and confirm impact.

        Args:
            request: Operation-discriminated edit-inputs presentation
                request.

        Returns:
            The fields, findings, draft, conflict, or confirmation plan on
            success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class AuthorStrategiesPresentationCapability(Protocol):
    """Presentation port for strategy authoring views."""

    async def author_strategies(
        self,
        request: AuthorStrategiesPresentationRequest,
    ) -> AuthorStrategiesPresentationSuccess | UiFailure:
        """Edit strategy trees, browse blocks, configure, and validate.

        Args:
            request: Operation-discriminated author-strategies
                presentation request.

        Returns:
            The projection, validation findings, or committed strategy
            version on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class RunResearchPresentationCapability(Protocol):
    """Presentation port for research run configuration and control."""

    async def run_research(
        self,
        request: RunResearchPresentationRequest,
    ) -> RunResearchPresentationSuccess | UiFailure:
        """Select modes, configure, preview, control, and compare research.

        Args:
            request: Operation-discriminated run-research presentation
                request.

        Returns:
            The Interfaces-owned preview, Research-owned run reference, or
            pinned versions on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class EditProjectsPresentationCapability(Protocol):
    """Presentation port for project editing and control views."""

    async def edit_projects(
        self,
        request: EditProjectsPresentationRequest,
    ) -> EditProjectsPresentationSuccess | UiFailure:
        """Manage, edit, compare, control, and inspect projects.

        Args:
            request: Operation-discriminated edit-projects presentation
                request.

        Returns:
            The Interfaces-owned project graph projection, version, or
            progress on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class ManageDataPresentationCapability(Protocol):
    """Presentation port for dataset management views."""

    async def manage_data(
        self,
        request: ManageDataPresentationRequest,
    ) -> ManageDataPresentationSuccess | UiFailure:
        """Browse, import, sync, export, edit, and administer data.

        Args:
            request: Operation-discriminated manage-data presentation
                request.

        Returns:
            The projection, findings, or Interfaces-owned job reference on
            success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class OperateDatabanksPresentationCapability(Protocol):
    """Presentation port for databank queries and bulk actions."""

    async def operate_databanks(
        self,
        request: OperateDatabanksPresentationRequest,
    ) -> OperateDatabanksPresentationSuccess | UiFailure:
        """Query, configure, select, filter, and act on databanks.

        Args:
            request: Operation-discriminated operate-databanks
                presentation request.

        Returns:
            The Analytics-owned result page, selection, bulk token, or
            confirmation on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class ExploreResultsPresentationCapability(Protocol):
    """Presentation port for result exploration and export."""

    async def explore_results(
        self,
        request: ExploreResultsPresentationRequest,
    ) -> ExploreResultsPresentationSuccess | UiFailure:
        """Summarize, plot, analyze, inspect, and export results.

        Args:
            request: Operation-discriminated explore-results presentation
                request.

        Returns:
            The summary, page state, chart alternative, or temporal
            context on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class ComposePortfoliosPresentationCapability(Protocol):
    """Presentation port for portfolio composition views."""

    async def compose_portfolios(
        self,
        request: ComposePortfoliosPresentationRequest,
    ) -> ComposePortfoliosPresentationSuccess | UiFailure:
        """Select constituents, edit, inspect, run, and compare portfolios.

        Args:
            request: Operation-discriminated compose-portfolios
                presentation request.

        Returns:
            The Interfaces-owned portfolio builder projection or version
            reference on success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class EditCodePresentationCapability(Protocol):
    """Presentation port for extension code editing."""

    async def edit_code(
        self,
        request: EditCodePresentationRequest,
    ) -> EditCodePresentationSuccess | UiFailure:
        """Navigate, edit, search, diagnose, and test extension code.

        Args:
            request: Operation-discriminated edit-code presentation
                request.

        Returns:
            The files, diagnostics, or test job reference on success,
            otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class MonitorWorkPresentationCapability(Protocol):
    """Presentation port for work monitoring and outcome notices."""

    async def monitor_work(
        self,
        request: MonitorWorkPresentationRequest,
    ) -> MonitorWorkPresentationSuccess | UiFailure:
        """Track progress, control jobs, present failures, and notify.

        Args:
            request: Operation-discriminated monitor-work presentation
                request.

        Returns:
            The progress, notification, or error presentation on success,
            otherwise a structured UI failure.
        """
        ...

    def subscribe_monitor_work_events(
        self,
        request: MonitorWorkPresentationEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver work monitoring events as domain events.

        Args:
            request: Owner-required subscription selector carrying the
                workspace or job binding, resume position, and bounded
                replay limit.

        Returns:
            An asynchronous iterator of work monitoring events wrapped in
            the common domain event envelope with ordered replay and
            resync semantics.
        """
        ...


@runtime_checkable
class AdministerSystemPresentationCapability(Protocol):
    """Presentation port for client administration surfaces."""

    async def administer_system(
        self,
        request: AdministerSystemPresentationRequest,
    ) -> AdministerSystemPresentationSuccess | UiFailure:
        """Set language and appearance and administer client capabilities.

        Args:
            request: Operation-discriminated administer-system
                presentation request.

        Returns:
            The preferences, accessibility settings, or Interfaces-owned
            administration projection on success, otherwise a structured
            UI failure.
        """
        ...


@runtime_checkable
class OperateTradingPresentationCapability(Protocol):
    """Presentation port for governed trading operation views."""

    async def operate_trading(
        self,
        request: OperateTradingPresentationRequest,
    ) -> OperateTradingPresentationSuccess | UiFailure:
        """Manage sessions, preview and commit actions, and watch markets.

        Args:
            request: Operation-discriminated operate-trading presentation
                request.

        Returns:
            The readiness or action preview projection, Trading-owned
            receipt, Risk-owned kill switch state, or Broker-owned market
            state on success, otherwise a structured UI failure.
        """
        ...

    def subscribe_operate_trading_events(
        self,
        request: OperateTradingPresentationEventSubscription,
    ) -> AsyncIterator[DomainEvent]:
        """Deliver trading and market presentation events as domain events.

        Args:
            request: Owner-required subscription selector carrying the
                session binding, scope filter, resume position, and
                bounded replay limit.

        Returns:
            An asynchronous iterator of trading and market events wrapped
            in the common domain event envelope with ordered replay and
            resync semantics.
        """
        ...


@runtime_checkable
class EnsureAccessPresentationCapability(Protocol):
    """Presentation port for accessibility guarantees."""

    async def ensure_access(
        self,
        request: EnsureAccessPresentationRequest,
    ) -> EnsureAccessPresentationSuccess | UiFailure:
        """Operate by keyboard, manage focus, and provide alternatives.

        Args:
            request: Operation-discriminated ensure-access presentation
                request.

        Returns:
            The chart alternatives, keyboard bindings, or focus target on
            success, otherwise a structured UI failure.
        """
        ...


@runtime_checkable
class ExtendViewsPresentationCapability(Protocol):
    """Presentation port for widget view contribution lifecycle."""

    async def extend_views(
        self,
        request: ExtendViewsPresentationRequest,
    ) -> ExtendViewsPresentationSuccess | UiFailure:
        """Declare, validate, scope, replace, and remove view contributions.

        Args:
            request: Operation-discriminated extend-views presentation
                request.

        Returns:
            The widget type descriptor, removal outcome, or migration
            outcome on success, otherwise a structured UI failure.
        """
        ...
