"""UI presentation and shell contract models."""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import Field, StringConstraints, model_validator

# Cross-namespace reference records are annotation-only for readers, but
# Pydantic resolves them at class-creation time, so they must remain runtime
# imports.
from app.contracts.analytics.models import ResultPage  # noqa: TC001
from app.contracts.broker.models import BrokerMarketState  # noqa: TC001
from app.contracts.common.models import (
    CapabilityIdentifier,
    ContentHash,
    DecimalValue,
    FeatureIdentifier,
    JsonObject,
    JsonValue,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)
from app.contracts.interfaces.models import (  # noqa: TC001
    AsyncJobRefWire,
    BulkRequestToken,
    CapabilityAdministrationProjection,
    PortfolioBuilderProjection,
    ProjectGraphProjection,
    ResearchPreview,
    TradingActionPreview,
    TradingReadinessProjection,
)
from app.contracts.research.models import ResearchRunRef  # noqa: TC001
from app.contracts.risk.models import KillSwitchState  # noqa: TC001
from app.contracts.trading.models import DispatchReceipt  # noqa: TC001


class CapabilityPresentationState(StrEnum):
    """Presentation state classification for capabilities in the UI."""

    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    INCOMPATIBLE = "incompatible"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    UNAUTHORIZED = "unauthorized"
    READY = "ready"


@dataclass(frozen=True, slots=True)
class UiFeatureDescriptor:
    """Descriptor for a registered UI feature."""

    feature_id: str
    name: str
    description: str
    required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouteTarget:
    """Route location and destination parameters in the UI."""

    path: str
    workspace_id: str
    title: str
    icon: str | None = None
    required_permission: str | None = None


@dataclass(frozen=True, slots=True)
class NavigationContribution:
    """Declared navigation entry contributed by a UI feature."""

    id: str
    label: str
    route: RouteTarget
    order: int = 0
    parent_id: str | None = None
    badge: str | None = None


@dataclass(frozen=True, slots=True)
class UiCommandDescriptor:
    """Action or command invokable from the UI shell."""

    command_id: str
    title: str
    category: str
    shortcut: str | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class KeyboardBinding:
    """Keyboard binding descriptor for accessibility and shortcuts."""

    key_combination: str
    command_id: str
    description: str
    scope: str = "global"


@dataclass(frozen=True, slots=True)
class ViewProjection:
    """Read-only presentation projection rendered inside a view."""

    view_id: str
    title: str
    data_source: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FieldDescriptor:
    """Typed field metadata for form rendering and validation."""

    field_name: str
    label: str
    field_type: str
    required: bool = False
    default_value: Any = None
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ClientSelection:
    """Active row or entity selection in a table or list view."""

    selection_id: str
    selected_keys: tuple[str, ...] = ()
    is_all_selected: bool = False


@dataclass(frozen=True, slots=True)
class ClientPageState:
    """Pagination and sorting state for bounded data views."""

    page_index: int = 0
    page_size: int = 50
    sort_column: str | None = None
    sort_ascending: bool = True
    total_count: int | None = None


@dataclass(frozen=True, slots=True)
class ChartAlternative:
    """Accessible tabular or descriptive alternative for a chart."""

    chart_id: str
    title: str
    summary_text: str
    table_data: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class DraftEnvelope:
    """Envelope for client-persisted non-secret form drafts."""

    draft_id: str
    schema_id: str
    workspace_id: str
    actor_id: str
    entity_version: int
    payload: dict[str, Any]
    created_at_iso: str
    updated_at_iso: str
    contract_version: int = 1


@dataclass(frozen=True, slots=True)
class DraftConflict:
    """Conflict between a local draft and remote authoritative version."""

    draft_id: str
    base_version: int
    current_version: int
    conflicting_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConfirmationPlan:
    """Plan presented before high-impact or destructive user actions."""

    action_id: str
    target_description: str
    impact_summary: str
    affected_count: int
    is_reversible: bool
    confirmation_hash: str


@dataclass(frozen=True, slots=True)
class UiNotification:
    """In-client visual notice or toast."""

    notification_id: str
    title: str
    message: str
    severity: str = "info"
    timestamp_iso: str = ""
    owning_task_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProgressPresentation:
    """Progress feedback descriptor for async jobs."""

    task_id: str
    stage_name: str
    progress_percent: float | None = None
    is_indeterminate: bool = False
    message: str = ""


@dataclass(frozen=True, slots=True)
class ErrorPresentation:
    """Structured error presentation for display."""

    error_code: str
    title: str
    detail: str
    causal_reference: str | None = None
    is_retryable: bool = False
    suggested_action: str | None = None


@dataclass(frozen=True, slots=True)
class PanelContribution:
    """Panel contribution into a composite layout."""

    panel_id: str
    title: str
    region: str
    is_closable: bool = True


@dataclass(frozen=True, slots=True)
class TabContribution:
    """Tab contribution within a panel or editor."""

    tab_id: str
    title: str
    content_view_id: str
    is_dirty: bool = False


@dataclass(frozen=True, slots=True)
class LayoutSnapshot:
    """Snapshot of workspace layout, panel sizes, and open tabs."""

    layout_id: str
    workspace_id: str
    active_panels: tuple[PanelContribution, ...] = ()
    open_tabs: tuple[TabContribution, ...] = ()
    version: int = 1


@dataclass(frozen=True, slots=True)
class ViewPreference:
    """Client presentation preference."""

    theme: str = "system"
    density: str = "comfortable"
    font_scale: float = 1.0
    locale: str = "en-US"


@dataclass(frozen=True, slots=True)
class AccessibilityPreference:
    """Client accessibility settings."""

    high_contrast: bool = False
    reduced_motion: bool = False
    screen_reader_optimized: bool = False


@dataclass(frozen=True, slots=True)
class WorkspaceRoute:
    """Authorized route descriptor for an active workspace."""

    workspace_id: str
    route_path: str
    display_name: str
    icon_name: str | None = None
    required_capabilities: tuple[str, ...] = ()
    is_authorized: bool = True


@dataclass(frozen=True, slots=True)
class ShellSnapshot:
    """Composite state snapshot of the UI shell."""

    active_workspace_id: str | None
    current_route: str
    available_workspaces: tuple[WorkspaceRoute, ...] = ()
    capability_states: dict[str, CapabilityPresentationState] = field(
        default_factory=dict
    )
    is_ready: bool = True
    status_message: str = "Ready"


# ---------------------------------------------------------------------------
# Ratified v1 wire contracts (additive; the frozen v1 dataclasses above stay
# unchanged as process contracts). Wire projections of the frozen records are
# named ``<Record>Wire``; the widget-workstation records are wire-native and
# keep their inventory names. The frozen Compose Shell process types
# (``WorkspaceRoute``, ``ShellSnapshot``, ``CapabilityPresentationState``)
# never become wire records. UI presentation records never become
# authoritative business state; secrets, approval tokens, and credentials
# never enter wire schemas. ``typing`` names stay qualified because the
# frozen import block above must remain byte-for-byte unchanged.

# Constrained local string aliases reused across UI wire records.
type NonEmptyStr = typing.Annotated[str, StringConstraints(min_length=1)]
# Domain assumption: client routes start at the root segment and continue
# with letters, digits, underscore, hyphen, and slash only; destination
# authorization is resolved by the shell, not by this syntactic check.
type RoutePath = typing.Annotated[str, StringConstraints(pattern=r"^/[A-Za-z0-9_/-]*$")]
# Domain assumption: presented error codes are single uppercase snake-case
# tokens matching the spelling of the ratified shared failure envelope.
type UiErrorCode = typing.Annotated[
    str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")
]
type TimeDomain = typing.Literal["LIVE", "PLAYBACK", "SIMULATION", "JOB_STREAM"]


class UiFeatureDescriptorWire(WireModel):
    """Wire projection of a registered UI feature (record R1)."""

    feature_id: FeatureIdentifier
    name: NonEmptyStr
    description: str
    required_capabilities: tuple[CapabilityIdentifier, ...] = ()
    optional_capabilities: tuple[CapabilityIdentifier, ...] = ()
    schema_version: typing.Literal[1] = 1


class RouteTargetWire(WireModel):
    """Wire projection of a navigable route destination (record R2).

    Removed routes cannot be resurrected by saved client state; the shell
    restores only still-authorized compatible routes.
    """

    path: RoutePath
    workspace_id: Uuid7
    title: NonEmptyStr
    icon: str | None = None
    required_permission: str | None = None
    schema_version: typing.Literal[1] = 1


class NavigationContributionWire(WireModel):
    """Wire projection of a declared navigation entry (record R3)."""

    id: NonEmptyStr
    label: NonEmptyStr
    route: RouteTargetWire
    order: int = Field(default=0, ge=0)
    parent_id: str | None = None
    badge: str | None = None
    schema_version: typing.Literal[1] = 1


class UiCommandDescriptorWire(WireModel):
    """Wire projection of a shell-invokable command (record R4)."""

    command_id: NonEmptyStr
    title: NonEmptyStr
    category: NonEmptyStr
    shortcut: str | None = None
    enabled: bool = True
    schema_version: typing.Literal[1] = 1


class KeyboardBindingWire(WireModel):
    """Wire projection of a keyboard binding (record R5)."""

    key_combination: NonEmptyStr
    command_id: NonEmptyStr
    description: str
    scope: str = "global"
    schema_version: typing.Literal[1] = 1


class ViewProjectionWire(WireModel):
    """Wire projection of a read-only presentation view (record R6)."""

    view_id: NonEmptyStr
    title: NonEmptyStr
    data_source: NonEmptyStr
    parameters: JsonObject = Field(default_factory=dict)
    schema_version: typing.Literal[1] = 1


class FieldDescriptorWire(WireModel):
    """Wire projection of typed form field metadata (record R7)."""

    field_name: NonEmptyStr
    label: NonEmptyStr
    field_type: NonEmptyStr
    required: bool = False
    default_value: JsonValue = None
    constraints: JsonObject = Field(default_factory=dict)
    schema_version: typing.Literal[1] = 1


class ClientSelectionWire(WireModel):
    """Wire projection of an active selection (record R8)."""

    selection_id: NonEmptyStr
    selected_keys: tuple[NonEmptyStr, ...] = ()
    is_all_selected: bool = False
    schema_version: typing.Literal[1] = 1


class ClientPageStateWire(WireModel):
    """Wire projection of bounded pagination state (record R9).

    Domain assumption: page sizes are capped at 500 rows per the
    PROJECT §15.7 500-row wire bound.
    """

    page_index: int = Field(default=0, ge=0)
    page_size: int = Field(default=50, ge=1, le=500)
    sort_column: str | None = None
    sort_ascending: bool = True
    total_count: int | None = Field(default=None, ge=0)
    schema_version: typing.Literal[1] = 1


class ChartAlternativeWire(WireModel):
    """Wire projection of an accessible chart alternative (record R10)."""

    chart_id: NonEmptyStr
    title: NonEmptyStr
    summary_text: NonEmptyStr
    table_data: tuple[JsonObject, ...] = ()
    schema_version: typing.Literal[1] = 1


class DraftEnvelopeWire(WireModel):
    """Wire projection of a client-persisted draft envelope (record R11).

    Payloads are non-secret presentation state only; secrets, approval
    tokens, and credentials never appear in a draft payload.
    """

    draft_id: Uuid7
    schema_id: NonEmptyStr
    workspace_id: Uuid7
    actor_id: Uuid7
    entity_version: int = Field(ge=1)
    payload: JsonObject
    created_at_iso: UtcTimestamp
    updated_at_iso: UtcTimestamp
    contract_version: int = Field(default=1, ge=1)
    schema_version: typing.Literal[1] = 1


class DraftConflictWire(WireModel):
    """Wire projection of a draft-versus-authority conflict (record R12).

    An explicit discard/merge/reload/retry choice is required before the
    draft can proceed.
    """

    draft_id: Uuid7
    base_version: int = Field(ge=1)
    current_version: int = Field(ge=1)
    conflicting_fields: tuple[NonEmptyStr, ...] = ()
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_conflict(self) -> DraftConflictWire:
        """Reject conflicts that do not advance the authoritative version.

        Returns:
            The validated conflict.

        Raises:
            ValueError: ``current_version`` is not greater than
                ``base_version``.
        """
        if self.current_version <= self.base_version:
            raise ValueError("current_version must be greater than base_version")
        return self


class ConfirmationPlanWire(WireModel):
    """Wire projection of a pre-action confirmation plan (record R13)."""

    action_id: Uuid7
    target_description: NonEmptyStr
    impact_summary: NonEmptyStr
    affected_count: int = Field(ge=0)
    is_reversible: bool
    confirmation_hash: ContentHash
    schema_version: typing.Literal[1] = 1


class UiNotificationWire(WireModel):
    """Wire projection of an in-client notice (record R14).

    Notifications are deduplicated and linked to their owning work; the
    v1 lowercase severity values are preserved as-is.
    """

    notification_id: Uuid7
    title: NonEmptyStr
    message: NonEmptyStr
    severity: typing.Literal["info", "warning", "error", "success"] = "info"
    timestamp_iso: UtcTimestamp
    owning_task_id: Uuid7 | None = None
    schema_version: typing.Literal[1] = 1


class ProgressPresentationWire(WireModel):
    """Wire projection of an async progress presentation (record R15).

    Progress carries no fabricated precision: ``progress_percent`` is an
    exact decimal string or the stage is indeterminate.
    """

    task_id: Uuid7
    stage_name: NonEmptyStr
    progress_percent: DecimalValue | None = None
    is_indeterminate: bool = False
    message: str = ""
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_progress_percent(self) -> ProgressPresentationWire:
        """Reject progress percentages outside the closed unit hundred range.

        Returns:
            The validated progress presentation.

        Raises:
            ValueError: ``progress_percent`` is not within [0, 100].
        """
        # The wire ratio is an exact decimal string, so compare it as a
        # Decimal rather than converting through a binary float.
        if self.progress_percent is not None and not (
            Decimal(0) <= Decimal(self.progress_percent) <= Decimal(100)
        ):
            raise ValueError("progress_percent must be within [0, 100]")
        return self


class ErrorPresentationWire(WireModel):
    """Wire projection of a structured error presentation (record R16)."""

    error_code: UiErrorCode
    title: NonEmptyStr
    detail: NonEmptyStr
    causal_reference: str | None = None
    is_retryable: bool = False
    suggested_action: str | None = None
    schema_version: typing.Literal[1] = 1


class PanelContributionWire(WireModel):
    """Wire projection of a panel contribution (record R18).

    Defined before ``LayoutSnapshotWire`` because the layout embeds it;
    registry order still follows the README inventory.
    """

    panel_id: NonEmptyStr
    title: NonEmptyStr
    region: NonEmptyStr
    is_closable: bool = True
    schema_version: typing.Literal[1] = 1


class TabContributionWire(WireModel):
    """Wire projection of a tab contribution (record R19).

    Closing a dirty tab requires an explicit resolution.
    """

    tab_id: NonEmptyStr
    title: NonEmptyStr
    content_view_id: NonEmptyStr
    is_dirty: bool = False
    schema_version: typing.Literal[1] = 1


class LayoutSnapshotWire(WireModel):
    """Wire projection of the legacy shell layout (record R17).

    Retained for the frozen Compose Shell v1; the widget workstation uses
    the wire-native ``WorkspaceLayoutSnapshot`` instead.
    """

    layout_id: Uuid7
    workspace_id: Uuid7
    active_panels: tuple[PanelContributionWire, ...] = ()
    open_tabs: tuple[TabContributionWire, ...] = ()
    version: int = Field(default=1, ge=1)
    schema_version: typing.Literal[1] = 1


class ViewPreferenceWire(WireModel):
    """Wire projection of client presentation preferences (record R20).

    The v1 lowercase theme strings are preserved as-is; the wire font
    scale is a ``DecimalValue`` string, not a binary float.
    """

    theme: str = "system"
    density: str = "comfortable"
    font_scale: DecimalValue = "1"
    locale: str = "en-US"
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_font_scale(self) -> ViewPreferenceWire:
        """Reject nonpositive font scale factors.

        Returns:
            The validated preferences.

        Raises:
            ValueError: ``font_scale`` is not greater than zero.
        """
        # The wire factor is an exact decimal string, so compare it as a
        # Decimal rather than converting through a binary float.
        if Decimal(self.font_scale) <= Decimal(0):
            raise ValueError("font_scale must be greater than zero")
        return self


class AccessibilityPreferenceWire(WireModel):
    """Wire projection of client accessibility settings (record R21)."""

    high_contrast: bool = False
    reduced_motion: bool = False
    screen_reader_optimized: bool = False
    schema_version: typing.Literal[1] = 1


class WidgetPlacement(WireModel):
    """Wire-native widget placement record (record R24).

    Defined before ``WidgetTypeDescriptor`` because the descriptor's
    default placement embeds it; registry order still follows the README
    inventory. Panel removal leaves no orphan region.
    """

    instance_id: Uuid7
    panel_id: NonEmptyStr
    panel_order: int = Field(default=0, ge=0)
    tab_order: int = Field(default=0, ge=0)
    size_ratio: DecimalValue = "1"
    is_minimized: bool = False
    is_maximized: bool = False
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_size_ratio(self) -> WidgetPlacement:
        """Reject size ratios outside the half-open unit interval.

        Returns:
            The validated placement.

        Raises:
            ValueError: ``size_ratio`` is not within (0, 1].
        """
        # The wire ratio is an exact decimal string, so compare it as a
        # Decimal rather than converting through a binary float.
        if not (Decimal(0) < Decimal(self.size_ratio) <= Decimal(1)):
            raise ValueError("size_ratio must be within (0, 1]")
        return self


class WidgetTypeDescriptor(WireModel):
    """Wire-native widget type registration record (record R22).

    ``widget_type`` is the stable module slug; widget type identity is
    never a product feature identity, which is carried by
    ``owning_feature``.
    """

    widget_type: NonEmptyStr
    owning_feature: FeatureIdentifier
    type_version: int = Field(ge=1)
    default_placement: WidgetPlacement | None = None
    configuration_schema: JsonObject = Field(default_factory=dict)
    state_schema: JsonObject = Field(default_factory=dict)
    required_capabilities: tuple[CapabilityIdentifier, ...] = ()
    subscriptions: tuple[CapabilityIdentifier, ...] = ()
    time_domains: tuple[TimeDomain, ...] = ()
    schema_version: typing.Literal[1] = 1


class WidgetInstanceRef(WireModel):
    """Wire-native widget instance identity record (record R23).

    Widget instance identity is never a feature identity.
    """

    instance_id: Uuid7
    widget_type: NonEmptyStr
    workspace_id: Uuid7
    configuration_version: int = Field(default=1, ge=1)
    state_version: int = Field(default=1, ge=1)
    schema_version: typing.Literal[1] = 1


class WidgetConfigurationEnvelope(WireModel):
    """Wire-native widget configuration envelope (record R25).

    The ``configuration`` payload is bounded by the widget type's
    ``configuration_schema``.
    """

    instance_id: Uuid7
    configuration_version: int = Field(default=1, ge=1)
    configuration: JsonObject = Field(default_factory=dict)
    schema_version: typing.Literal[1] = 1


class WidgetStateEnvelope(WireModel):
    """Wire-native widget presentation-state envelope (record R26).

    Presentation state only, never authoritative business state; the
    ``state`` payload is bounded by the widget type's ``state_schema``.
    """

    instance_id: Uuid7
    state_version: int = Field(default=1, ge=1)
    state: JsonObject = Field(default_factory=dict)
    updated_at: UtcTimestamp
    schema_version: typing.Literal[1] = 1


class WorkspaceLayoutSnapshot(WireModel):
    """Wire-native workstation layout snapshot (record R27).

    Scoped to one actor, workspace, capability snapshot, and layout
    schema; immutable per layout version.
    """

    layout_id: Uuid7
    workspace_id: Uuid7
    actor_id: Uuid7
    layout_version: int = Field(ge=1)
    capability_snapshot_id: Uuid7
    widget_instances: tuple[WidgetInstanceRef, ...] = ()
    placements: tuple[WidgetPlacement, ...] = ()
    active_panel_id: str | None = None
    content_hash: ContentHash
    schema_version: typing.Literal[1] = 1


class WorkspaceTemplate(WireModel):
    """Wire-native workspace template record (record R28)."""

    template_id: Uuid7
    name: NonEmptyStr
    description: str = ""
    layout: WorkspaceLayoutSnapshot
    schema_version: typing.Literal[1] = 1


class LayoutMigrationResult(WireModel):
    """Wire-native layout migration outcome (record R29).

    Incompatible widgets are diagnosed and never silently remapped.
    """

    source_layout_version: int = Field(ge=1)
    target_layout_version: int = Field(ge=1)
    migrated: bool
    incompatible_widgets: tuple[NonEmptyStr, ...] = ()
    defaulted_widgets: tuple[NonEmptyStr, ...] = ()
    diagnostics: tuple[ValidationIssue, ...] = ()
    schema_version: typing.Literal[1] = 1


class TemporalSourceRef(WireModel):
    """Wire-native temporal source and clock identity (record R31).

    Defined before the temporal records that embed it; registry order
    still follows the README inventory. Source and clock identity are
    preserved and never make presentation state authoritative.
    """

    source_id: Uuid7
    source_kind: NonEmptyStr
    clock_id: NonEmptyStr
    schema_version: typing.Literal[1] = 1


class TemporalFreshness(WireModel):
    """Wire-native temporal freshness observation (record R32)."""

    source: TemporalSourceRef
    last_event_at: UtcTimestamp
    observed_at: UtcTimestamp
    is_stale: bool
    staleness_reason: str = ""
    schema_version: typing.Literal[1] = 1


class TemporalCursor(WireModel):
    """Wire-native ordered temporal cursor (record R33).

    Applications are ordered by the monotonic sequence or the supplied
    cursor token.
    """

    source: TemporalSourceRef
    sequence: int = Field(ge=0)
    cursor_token: str | None = None
    as_of: UtcTimestamp
    schema_version: typing.Literal[1] = 1


class TemporalGap(WireModel):
    """Wire-native detected temporal gap (record R34)."""

    source: TemporalSourceRef
    from_sequence: int = Field(ge=0)
    to_sequence: int = Field(ge=0)
    reason: str = ""
    schema_version: typing.Literal[1] = 1

    @model_validator(mode="after")
    def validate_gap_bounds(self) -> TemporalGap:
        """Reject gap bounds that end before they start.

        Returns:
            The validated gap.

        Raises:
            ValueError: ``to_sequence`` precedes ``from_sequence``.
        """
        if self.to_sequence < self.from_sequence:
            raise ValueError("to_sequence must be at or after from_sequence")
        return self


class TemporalResynchronization(WireModel):
    """Wire-native temporal resynchronization outcome (record R35)."""

    context_id: Uuid7
    outcome: typing.Literal["RESYNCED", "FAILED_CLOSED"]
    started_at: UtcTimestamp
    completed_at: UtcTimestamp
    replayed_from_sequence: int | None = Field(default=None, ge=0)
    schema_version: typing.Literal[1] = 1


class TemporalContext(WireModel):
    """Wire-native temporal context record (record R30).

    Defined after its cursor/freshness/gap/resynchronization parts;
    registry order still follows the README inventory. Time-domain mixing
    is rejected at runtime: widgets show causally consistent evidence or
    fail closed.
    """

    context_id: Uuid7
    workspace_id: Uuid7
    domain: TimeDomain
    bound_source: TemporalSourceRef
    cursor: TemporalCursor | None = None
    freshness: TemporalFreshness | None = None
    open_gaps: tuple[TemporalGap, ...] = ()
    resynchronization: TemporalResynchronization | None = None
    schema_version: typing.Literal[1] = 1


class WidgetRemovalResult(WireModel):
    """Wire-native widget removal outcome (record R37).

    Exact removal without stale controls, listeners, or state leaks, with
    a deterministic fallback focus target.
    """

    instance_id: Uuid7
    widget_type: NonEmptyStr
    removal_state: typing.Literal["REMOVED", "PARTIAL", "FAILED"]
    reversed_effects: tuple[NonEmptyStr, ...] = ()
    focused_fallback: str | None = None
    schema_version: typing.Literal[1] = 1


class StartWorkPresentationRequest(WireModel):
    """Operation-discriminated start-work presentation request (port 1)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "SHOW_HOME",
        "LIST_RECENT",
        "LAUNCH_SHORTCUT",
        "SHOW_NEWS",
    ]
    schema_version: typing.Literal[1] = 1


class StartWorkPresentationSuccess(WireModel):
    """Successful start-work presentation result (port 1).

    ``recent_routes`` is returned for LIST_RECENT, ``shortcuts`` for
    LAUNCH_SHORTCUT, and ``news`` for SHOW_NEWS; SHOW_HOME carries the
    provider's home presentation.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    recent_routes: tuple[RouteTargetWire, ...] = ()
    shortcuts: tuple[UiCommandDescriptorWire, ...] = ()
    news: tuple[UiNotificationWire, ...] = ()
    schema_version: typing.Literal[1] = 1


class ManageLayoutsPresentationRequest(WireModel):
    """Operation-discriminated manage-layouts presentation request (port 2)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "COMPOSE",
        "PERSIST",
        "RESTORE",
        "MANAGE_TABS",
        "SCALE",
    ]
    schema_version: typing.Literal[1] = 1


class ManageLayoutsPresentationSuccess(WireModel):
    """Successful manage-layouts presentation result (port 2).

    ``layout`` carries the workstation layout snapshot, ``migration`` the
    restore-path migration outcome, and ``template`` the saved or loaded
    template.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    layout: WorkspaceLayoutSnapshot | None = None
    migration: LayoutMigrationResult | None = None
    template: WorkspaceTemplate | None = None
    schema_version: typing.Literal[1] = 1


class EditInputsPresentationRequest(WireModel):
    """Operation-discriminated edit-inputs presentation request (port 3)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "RENDER_FIELDS",
        "VALIDATE",
        "PRESERVE_DRAFT",
        "RESOLVE_CONFLICT",
        "CONFIRM",
    ]
    schema_version: typing.Literal[1] = 1


class EditInputsPresentationSuccess(WireModel):
    """Successful edit-inputs presentation result (port 3).

    ``fields`` is returned for RENDER_FIELDS, ``findings`` for VALIDATE,
    ``draft`` for PRESERVE_DRAFT, ``conflict`` for RESOLVE_CONFLICT, and
    ``confirmation`` for CONFIRM.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    fields: tuple[FieldDescriptorWire, ...] = ()
    findings: tuple[ValidationIssue, ...] = ()
    draft: DraftEnvelopeWire | None = None
    conflict: DraftConflictWire | None = None
    confirmation: ConfirmationPlanWire | None = None
    schema_version: typing.Literal[1] = 1


class AuthorStrategiesPresentationRequest(WireModel):
    """Operation-discriminated author-strategies presentation request (port 4)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "EDIT_TREE",
        "BROWSE_BLOCKS",
        "CONFIGURE",
        "VALIDATE",
        "USE_EXAMPLES",
        "REQUEST_TEST",
    ]
    schema_version: typing.Literal[1] = 1


class AuthorStrategiesPresentationSuccess(WireModel):
    """Successful author-strategies presentation result (port 4).

    ``projection`` carries the read-only authoring view, ``findings`` the
    validation issues, and ``strategy_version_id`` the committed strategy
    version for REQUEST_TEST.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    projection: ViewProjectionWire | None = None
    findings: tuple[ValidationIssue, ...] = ()
    strategy_version_id: Uuid7 | None = None
    schema_version: typing.Literal[1] = 1


class RunResearchPresentationRequest(WireModel):
    """Operation-discriminated run-research presentation request (port 5)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "SELECT_MODE",
        "CONFIGURE",
        "PREVIEW",
        "CONTROL",
        "COMPARE",
        "REUSE_SETTINGS",
    ]
    schema_version: typing.Literal[1] = 1


class RunResearchPresentationSuccess(WireModel):
    """Successful run-research presentation result (port 5).

    ``preview`` reuses the Interfaces-owned ``ResearchPreview`` and
    ``run`` the Research-owned ``ResearchRunRef``; the UI never invents
    admission or run state.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    preview: ResearchPreview | None = None
    run: ResearchRunRef | None = None
    pinned_versions: tuple[Uuid7, ...] = ()
    schema_version: typing.Literal[1] = 1


class EditProjectsPresentationRequest(WireModel):
    """Operation-discriminated edit-projects presentation request (port 6)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "MANAGE",
        "EDIT_TASKS",
        "EDIT_GRAPH",
        "COMPARE",
        "CONTROL",
        "INSPECT",
    ]
    schema_version: typing.Literal[1] = 1


class EditProjectsPresentationSuccess(WireModel):
    """Successful edit-projects presentation result (port 6).

    ``projection`` reuses the Interfaces-owned
    ``ProjectGraphProjection``; ``progress`` carries project run
    monitoring and ``project_version_id`` the referenced version.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    projection: ProjectGraphProjection | None = None
    project_version_id: Uuid7 | None = None
    progress: ProgressPresentationWire | None = None
    schema_version: typing.Literal[1] = 1


class ManageDataPresentationRequest(WireModel):
    """Operation-discriminated manage-data presentation request (port 7)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "BROWSE",
        "IMPORT",
        "SYNC",
        "EXPORT",
        "EDIT_INSTRUMENTS",
        "EDIT_SESSIONS",
        "ADMINISTER",
    ]
    schema_version: typing.Literal[1] = 1


class ManageDataPresentationSuccess(WireModel):
    """Successful manage-data presentation result (port 7).

    ``job`` reuses the Interfaces-owned ``AsyncJobRef`` wire projection
    for long-running import/sync/export work.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    projection: ViewProjectionWire | None = None
    findings: tuple[ValidationIssue, ...] = ()
    job: AsyncJobRefWire | None = None
    schema_version: typing.Literal[1] = 1


class OperateDatabanksPresentationRequest(WireModel):
    """Operation-discriminated operate-databanks presentation request (port 8)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "QUERY",
        "CONFIGURE_COLUMNS",
        "SELECT",
        "FILTER",
        "BULK_ACTION",
        "OPEN_RESULT",
    ]
    schema_version: typing.Literal[1] = 1


class OperateDatabanksPresentationSuccess(WireModel):
    """Successful operate-databanks presentation result (port 8).

    ``page`` reuses the Analytics-owned ``ResultPage``, ``bulk_token``
    the Interfaces-owned ``BulkRequestToken``, and ``confirmation`` the
    bounded bulk-action confirmation plan.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    page: ResultPage | None = None
    selection: ClientSelectionWire | None = None
    bulk_token: BulkRequestToken | None = None
    confirmation: ConfirmationPlanWire | None = None
    schema_version: typing.Literal[1] = 1


class ExploreResultsPresentationRequest(WireModel):
    """Operation-discriminated explore-results presentation request (port 9)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "SUMMARIZE",
        "PLOT_EQUITY",
        "LIST_TRADES",
        "PLOT_TRADES",
        "ANALYZE",
        "INSPECT_ROBUSTNESS",
        "INSPECT_SOURCE",
        "EXPORT",
    ]
    schema_version: typing.Literal[1] = 1


class ExploreResultsPresentationSuccess(WireModel):
    """Successful explore-results presentation result (port 9).

    ``context`` carries the causally consistent temporal context backing
    the result view.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    summary: ViewProjectionWire | None = None
    page_state: ClientPageStateWire | None = None
    chart_alternative: ChartAlternativeWire | None = None
    context: TemporalContext | None = None
    schema_version: typing.Literal[1] = 1


class ComposePortfoliosPresentationRequest(WireModel):
    """Operation-discriminated compose-portfolios presentation request (port 10)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "SELECT_CONSTITUENTS",
        "EDIT",
        "INSPECT_CORRELATION",
        "RUN",
        "COMPARE",
    ]
    schema_version: typing.Literal[1] = 1


class ComposePortfoliosPresentationSuccess(WireModel):
    """Successful compose-portfolios presentation result (port 10).

    ``projection`` reuses the Interfaces-owned
    ``PortfolioBuilderProjection``; the UI never invents portfolio
    manifests or results.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    projection: PortfolioBuilderProjection | None = None
    portfolio_version_id: Uuid7 | None = None
    schema_version: typing.Literal[1] = 1


class EditCodePresentationRequest(WireModel):
    """Operation-discriminated edit-code presentation request (port 11)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "NAVIGATE",
        "EDIT_TABS",
        "SEARCH",
        "MANAGE_FILES",
        "SHOW_DIAGNOSTICS",
        "TEST",
    ]
    schema_version: typing.Literal[1] = 1


class EditCodePresentationSuccess(WireModel):
    """Successful edit-code presentation result (port 11).

    ``diagnostics`` carries code findings and ``job`` the
    Interfaces-owned ``AsyncJobRef`` wire projection for extension test
    jobs.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    files: tuple[NonEmptyStr, ...] = ()
    diagnostics: tuple[ValidationIssue, ...] = ()
    job: AsyncJobRefWire | None = None
    schema_version: typing.Literal[1] = 1


class MonitorWorkPresentationRequest(WireModel):
    """Operation-discriminated monitor-work presentation request (port 12)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "TRACK",
        "CONTROL",
        "PRESENT_FAILURES",
        "NOTIFY",
    ]
    schema_version: typing.Literal[1] = 1


class MonitorWorkPresentationSuccess(WireModel):
    """Successful monitor-work presentation result (port 12).

    ``progress`` carries tracked progress, ``notification`` deduplicated
    outcome notices, and ``error`` structured failure presentations.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    progress: ProgressPresentationWire | None = None
    notification: UiNotificationWire | None = None
    error: ErrorPresentationWire | None = None
    schema_version: typing.Literal[1] = 1


class MonitorWorkPresentationEventSubscription(WireModel):
    """Owner-required work monitoring event stream subscription (port 12).

    ``resume_event_id`` reconnects after interruption with ordered
    replay/resync semantics and ``replay_limit`` bounds buffered replay
    per FR-UI-STREAM_ACTIVITY.
    """

    workspace_id: Uuid7 | None = None
    job_id: Uuid7 | None = None
    resume_event_id: Uuid7 | None = None
    replay_limit: int = Field(default=0, ge=0, le=10000)
    schema_version: typing.Literal[1] = 1


class AdministerSystemPresentationRequest(WireModel):
    """Operation-discriminated administer-system presentation request (port 13)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "SET_LANGUAGE",
        "SET_APPEARANCE",
        "CONFIGURE_CLIENT",
        "MANAGE_LICENSE",
        "MANAGE_UPDATES",
        "ADMINISTER_CAPABILITIES",
    ]
    schema_version: typing.Literal[1] = 1


class AdministerSystemPresentationSuccess(WireModel):
    """Successful administer-system presentation result (port 13).

    ``administration`` reuses the Interfaces-owned
    ``CapabilityAdministrationProjection``; no secrets or credential
    values ever appear.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    preferences: ViewPreferenceWire | None = None
    accessibility: AccessibilityPreferenceWire | None = None
    administration: CapabilityAdministrationProjection | None = None
    schema_version: typing.Literal[1] = 1


class OperateTradingPresentationRequest(WireModel):
    """Operation-discriminated operate-trading presentation request (port 14)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "MANAGE_SESSIONS",
        "SHOW_READINESS",
        "PREVIEW_ACTION",
        "COMMIT_ACTION",
        "OPERATE_KILL_SWITCH",
        "WATCH_MARKETS",
        "INSPECT_OPERATOR_ANALYTICS",
    ]
    schema_version: typing.Literal[1] = 1


class OperateTradingPresentationSuccess(WireModel):
    """Successful operate-trading presentation result (port 14).

    ``readiness`` and ``preview`` reuse Interfaces-owned projections,
    ``receipt`` the Trading-owned ``DispatchReceipt``, ``kill_switch``
    the Risk-owned ``KillSwitchState``, and ``market`` the Broker-owned
    ``BrokerMarketState``; the UI never invents fills or authority.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    readiness: TradingReadinessProjection | None = None
    preview: TradingActionPreview | None = None
    receipt: DispatchReceipt | None = None
    kill_switch: KillSwitchState | None = None
    market: BrokerMarketState | None = None
    schema_version: typing.Literal[1] = 1


class OperateTradingPresentationEventSubscription(WireModel):
    """Owner-required trading presentation event stream subscription (port 14).

    ``scope`` filters trading versus market events per
    FR-UI-WATCH_TRADING_EVENTS replay/resync and FR-UI-WATCH_MARKETS live
    markets; ``resume_event_id`` reconnects with ordered replay/resync
    semantics bounded by ``replay_limit``.
    """

    session_ref: Uuid7 | None = None
    scope: typing.Literal["TRADING", "MARKET", "ALL"] = "ALL"
    resume_event_id: Uuid7 | None = None
    replay_limit: int = Field(default=0, ge=0, le=10000)
    schema_version: typing.Literal[1] = 1


class EnsureAccessPresentationRequest(WireModel):
    """Operation-discriminated ensure-access presentation request (port 15)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "OPERATE_BY_KEYBOARD",
        "MANAGE_FOCUS",
        "LABEL_CONTROLS",
        "PROVIDE_DATA_ALTERNATIVES",
        "DISTINGUISH_STATE",
        "PRESERVE_USABILITY",
    ]
    schema_version: typing.Literal[1] = 1


class EnsureAccessPresentationSuccess(WireModel):
    """Successful ensure-access presentation result (port 15).

    ``alternatives`` carries data alternatives for charts,
    ``bindings`` the keyboard bindings, and ``focus_target`` the
    deterministic focus destination.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    alternatives: tuple[ChartAlternativeWire, ...] = ()
    bindings: tuple[KeyboardBindingWire, ...] = ()
    focus_target: str | None = None
    schema_version: typing.Literal[1] = 1


class ExtendViewsPresentationRequest(WireModel):
    """Operation-discriminated extend-views presentation request (port 16)."""

    request_id: Uuid7
    capability_snapshot_id: Uuid7
    operation: typing.Literal[
        "DECLARE",
        "VALIDATE",
        "SCOPE",
        "REPLACE",
        "REMOVE",
    ]
    schema_version: typing.Literal[1] = 1


class ExtendViewsPresentationSuccess(WireModel):
    """Successful extend-views presentation result (port 16).

    ``widget_type`` carries the declared or validated descriptor,
    ``removal`` the exact-removal outcome, and ``migration`` the
    replacement migration outcome.
    """

    outcome: typing.Literal["SUCCESS"] = "SUCCESS"
    request_id: Uuid7
    result_version: typing.Literal[1] = 1
    widget_type: WidgetTypeDescriptor | None = None
    removal: WidgetRemovalResult | None = None
    migration: LayoutMigrationResult | None = None
    schema_version: typing.Literal[1] = 1


# Wire projections register under their inventory names (``<Record>`` ->
# ``<Record>Wire``); wire-native and request/success/subscription records
# register directly. The record R36 ``WidgetLifecycleEvent`` event payload
# registers in ``WIRE_EVENTS`` in ``events.py``.
WIRE_MODELS: dict[str, type[WireModel]] = {
    "UiFeatureDescriptor": UiFeatureDescriptorWire,
    "RouteTarget": RouteTargetWire,
    "NavigationContribution": NavigationContributionWire,
    "UiCommandDescriptor": UiCommandDescriptorWire,
    "KeyboardBinding": KeyboardBindingWire,
    "ViewProjection": ViewProjectionWire,
    "FieldDescriptor": FieldDescriptorWire,
    "ClientSelection": ClientSelectionWire,
    "ClientPageState": ClientPageStateWire,
    "ChartAlternative": ChartAlternativeWire,
    "DraftEnvelope": DraftEnvelopeWire,
    "DraftConflict": DraftConflictWire,
    "ConfirmationPlan": ConfirmationPlanWire,
    "UiNotification": UiNotificationWire,
    "ProgressPresentation": ProgressPresentationWire,
    "ErrorPresentation": ErrorPresentationWire,
    "LayoutSnapshot": LayoutSnapshotWire,
    "PanelContribution": PanelContributionWire,
    "TabContribution": TabContributionWire,
    "ViewPreference": ViewPreferenceWire,
    "AccessibilityPreference": AccessibilityPreferenceWire,
    "WidgetTypeDescriptor": WidgetTypeDescriptor,
    "WidgetInstanceRef": WidgetInstanceRef,
    "WidgetPlacement": WidgetPlacement,
    "WidgetConfigurationEnvelope": WidgetConfigurationEnvelope,
    "WidgetStateEnvelope": WidgetStateEnvelope,
    "WorkspaceLayoutSnapshot": WorkspaceLayoutSnapshot,
    "WorkspaceTemplate": WorkspaceTemplate,
    "LayoutMigrationResult": LayoutMigrationResult,
    "TemporalContext": TemporalContext,
    "TemporalSourceRef": TemporalSourceRef,
    "TemporalFreshness": TemporalFreshness,
    "TemporalCursor": TemporalCursor,
    "TemporalGap": TemporalGap,
    "TemporalResynchronization": TemporalResynchronization,
    "WidgetRemovalResult": WidgetRemovalResult,
    "StartWorkPresentationRequest": StartWorkPresentationRequest,
    "StartWorkPresentationSuccess": StartWorkPresentationSuccess,
    "ManageLayoutsPresentationRequest": ManageLayoutsPresentationRequest,
    "ManageLayoutsPresentationSuccess": ManageLayoutsPresentationSuccess,
    "EditInputsPresentationRequest": EditInputsPresentationRequest,
    "EditInputsPresentationSuccess": EditInputsPresentationSuccess,
    "AuthorStrategiesPresentationRequest": AuthorStrategiesPresentationRequest,
    "AuthorStrategiesPresentationSuccess": AuthorStrategiesPresentationSuccess,
    "RunResearchPresentationRequest": RunResearchPresentationRequest,
    "RunResearchPresentationSuccess": RunResearchPresentationSuccess,
    "EditProjectsPresentationRequest": EditProjectsPresentationRequest,
    "EditProjectsPresentationSuccess": EditProjectsPresentationSuccess,
    "ManageDataPresentationRequest": ManageDataPresentationRequest,
    "ManageDataPresentationSuccess": ManageDataPresentationSuccess,
    "OperateDatabanksPresentationRequest": OperateDatabanksPresentationRequest,
    "OperateDatabanksPresentationSuccess": OperateDatabanksPresentationSuccess,
    "ExploreResultsPresentationRequest": ExploreResultsPresentationRequest,
    "ExploreResultsPresentationSuccess": ExploreResultsPresentationSuccess,
    "ComposePortfoliosPresentationRequest": ComposePortfoliosPresentationRequest,
    "ComposePortfoliosPresentationSuccess": ComposePortfoliosPresentationSuccess,
    "EditCodePresentationRequest": EditCodePresentationRequest,
    "EditCodePresentationSuccess": EditCodePresentationSuccess,
    "MonitorWorkPresentationRequest": MonitorWorkPresentationRequest,
    "MonitorWorkPresentationSuccess": MonitorWorkPresentationSuccess,
    "MonitorWorkPresentationEventSubscription": (
        MonitorWorkPresentationEventSubscription
    ),
    "AdministerSystemPresentationRequest": AdministerSystemPresentationRequest,
    "AdministerSystemPresentationSuccess": AdministerSystemPresentationSuccess,
    "OperateTradingPresentationRequest": OperateTradingPresentationRequest,
    "OperateTradingPresentationSuccess": OperateTradingPresentationSuccess,
    "OperateTradingPresentationEventSubscription": (
        OperateTradingPresentationEventSubscription
    ),
    "EnsureAccessPresentationRequest": EnsureAccessPresentationRequest,
    "EnsureAccessPresentationSuccess": EnsureAccessPresentationSuccess,
    "ExtendViewsPresentationRequest": ExtendViewsPresentationRequest,
    "ExtendViewsPresentationSuccess": ExtendViewsPresentationSuccess,
}
