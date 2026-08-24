"""UI presentation and shell contract models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


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
