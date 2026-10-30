"""Dictionary-compatible, runtime-validated editor results.

Description:
    Names the existing service payloads without inserting defaults or null fields.
    Open-ended extension values use finite JSON; domain records have exact keys.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Share explicit service and persistence contracts.
Key Capabilities:
    - FR-code-editor-validate-result: Validate stored and outgoing records;
      DEBUG acceptance and ERROR rejection logs are tested without payloads.
Python API Usage:
    state = validate_result(TypeAdapter(WorkspaceState), stored_document)
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_contracts.py --no-cov
"""

import logging
from typing import Annotated, Literal, NotRequired, TypedDict

from pydantic import ConfigDict, Field, TypeAdapter, ValidationError, with_config

from app.core.lib.errors import JSONValue
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor.errors import CodeEditorError

logger = logging.getLogger(__name__)


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class CursorPosition(TypedDict):
    """One-based cursor coordinates."""

    line: int
    column: int


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Diagnostic(TypedDict):
    """A source diagnostic, optionally including the existing source line."""

    line: int
    column: int
    message: str
    severity: Literal["error", "warning", "info"]
    source_line: NotRequired[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Tab(TypedDict):
    """Complete document state persisted by the current editor."""

    file_path: str
    title: str
    is_dirty: bool
    content: str
    mode: str
    cursor_position: CursorPosition


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class WorkspaceState(TypedDict):
    """Stored workspace document; no schema migration is implied."""

    open_tabs: list[Tab]
    active_file: str | None


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Layout(TypedDict):
    """Existing workspace panel preferences."""

    navigator_visible: bool
    split_mode: str
    bottom_panel: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class WorkspaceInfo(WorkspaceState):
    """Initialized workspace result."""

    status: Literal["ready"]
    layout: Layout


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class OpenTabResult(TypedDict):
    """Opened or selected document."""

    status: Literal["opened", "switched"]
    tab: Tab
    active_file: str | None


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class CloseTabResult(TypedDict):
    """Existing close outcomes retain their branch-specific optional fields."""

    status: Literal["closed", "not_open", "unsaved_changes"]
    active_file: str | None
    file_path: NotRequired[str]
    closed_file: NotRequired[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SavedFile(TypedDict):
    """One saved buffer and its diagnostics."""

    file_path: str
    diagnostics: list[Diagnostic]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SaveResult(SavedFile):
    """Single-file publication result."""

    status: Literal["saved"]
    bytes_written: int


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SaveAllResult(TypedDict):
    """Batch publication result."""

    status: Literal["saved_all"]
    count: int
    files: list[SavedFile]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class NavigatorItem(TypedDict):
    """A file or recursive directory entry."""

    id: str
    name: str
    type: Literal["file", "directory"]
    extension: NotRequired[str]
    path: NotRequired[str]
    children: NotRequired[list[NavigatorItem]]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class EditorSummary(TypedDict):
    """Existing open-editor list item."""

    file_path: str
    title: str
    is_dirty: bool


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class MenuItem(TypedDict):
    """An existing toolbar contribution."""

    id: str
    label: str
    action: NotRequired[str]
    shortcut: NotRequired[str]
    options: NotRequired[list[str]]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Menu(TypedDict):
    """Existing toolbar configuration."""

    toolbar: list[MenuItem]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class PanelTabs(TypedDict):
    """Existing side/bottom panel tab configuration."""

    active_tab: str
    tabs: list[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class DirectoryResult(TypedDict):
    """Created directory result."""

    status: Literal["created"]
    dir_path: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class CreatedSnippet(TypedDict):
    """Generated snippet and opened tab."""

    status: Literal["created"]
    template_type: str
    name: str
    file_path: str
    tab: Tab


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class RenameResult(TypedDict):
    """Renamed path result."""

    status: Literal["renamed"]
    old_path: str
    new_path: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class DeleteResult(TypedDict):
    """Deleted path result."""

    status: Literal["deleted"]
    file_path: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SearchMatch(TypedDict):
    """Located source text; it must never be copied into operation logs."""

    file: str
    line: int
    column: int
    text: str
    match: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class CompileResult(TypedDict):
    """Existing synchronous compilation result."""

    file: str
    timestamp: str
    success: bool
    errors: list[Diagnostic]
    registered_classes: NotRequired[list[str]]
    module_reloaded: NotRequired[bool]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class CompileAllResult(TypedDict):
    """Existing synchronous batch result."""

    status: Literal["completed"]
    total_files: int
    valid_files: int
    results: list[CompileResult]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class TemplateInfo(TypedDict):
    """Current Python template catalogue entry."""

    template_id: str
    name: str
    description: str
    category: str
    default_filename: str
    target_subdir: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class TemplatePreview(TypedDict):
    """Source preview without publication."""

    content: str
    file_path: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class PackageManifest(TypedDict):
    """Existing on-disk Python package manifest."""

    version: Literal["1.0"]
    metadata: dict[str, JSONValue]
    files: list[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class ExportResult(TypedDict):
    """Published Python source package."""

    status: Literal["exported"]
    archive_path: str
    file_count: int
    files: list[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class ArchiveEntry(TypedDict):
    """Package inspection record."""

    filename: str
    file_size: int
    exists_locally: bool


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class ImportResult(TypedDict):
    """Publication and subsequent per-file compilation results."""

    status: Literal["completed"]
    extracted_count: int
    skipped_count: int
    extracted: list[str]
    skipped: list[str]
    reload_results: list[CompileResult]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class IndicatorConfig(TypedDict):
    """Existing stored/new single-indicator setup, not a batch suite."""

    test_id: str
    indicator_name: str
    symbol: str
    timeframe: str
    params: dict[str, JSONValue]
    bars_to_reserve: Annotated[int, Field(ge=0, le=10000)]
    bar_count: Annotated[int, Field(ge=1, le=10000)]
    created_at: NotRequired[float]
    reference_values: NotRequired[list[float] | None]
    saved_name: NotRequired[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Candle(TypedDict):
    """Historical chart bar."""

    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class PlotPoint(TypedDict):
    """Missing value means a chart gap, not zero."""

    time: int
    value: NotRequired[float]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class PlotSeries(TypedDict):
    """Named chart output and pane."""

    name: str
    pane: str
    data: list[PlotPoint]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class IndicatorRow(Candle):
    """Historical table output; missing indicator values remain null."""

    indicator_val: float | None
    outputs: dict[str, float | None]
    reference_val: NotRequired[float]
    diff: NotRequired[float | None]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class Difference(TypedDict):
    """Finite calculated/reference difference."""

    bar: int
    time: int
    calc: float
    ref: float
    diff: float


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class NonFiniteDiagnostic(TypedDict):
    """A non-finite output represented by a chart gap."""

    bar: int
    time: int
    series: str
    type: Literal["NonFiniteValue"]
    message: str


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class ExecutionDiagnostic(TypedDict):
    """A failed calculation or lookup."""

    bar: int
    type: str
    message: str


type IndicatorDiagnostic = Difference | NonFiniteDiagnostic | ExecutionDiagnostic


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class IndicatorResult(TypedDict):
    """Current calculation outcome, including its diagnostic variants."""

    test_id: str
    status: Literal["success", "failed"]
    symbol: str
    timeframe: str
    bars_calculated: int
    candlesticks: list[Candle]
    indicator_plots: list[PlotPoint]
    plot_series: list[PlotSeries]
    table_rows: list[IndicatorRow]
    discrepancies: list[IndicatorDiagnostic]
    data_source: NotRequired[Literal["historical"]]
    error: NotRequired[str]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SavedTest(TypedDict):
    """Persisted test configuration result."""

    status: Literal["saved"]
    config_id: str
    config: IndicatorConfig


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class LoadedTest(TypedDict):
    """Restored configuration result."""

    status: Literal["loaded"]
    config: IndicatorConfig


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class ToolInfo(TypedDict):
    """Finite JSON schema from a compiled extension."""

    name: str
    description: str
    inputSchema: dict[str, JSONValue]


@with_config(ConfigDict(extra="forbid", allow_inf_nan=False))
class SuccessEnvelope[T](TypedDict):
    """Preserved editor envelope; host transport owns failure envelopes."""

    status: Literal["success"]
    data: T


def validate_result[T](adapter: TypeAdapter[T], value: object) -> T:
    """Validate without partial publication or payload-bearing error logs."""
    try:
        result = adapter.validate_python(value, strict=True)
    except ValidationError:
        logger.error("FR-code-editor-validate-result: rejected")
        raise CodeEditorError(
            "Invalid editor result or stored state", code=ErrorCode.INTERNAL
        ) from None
    logger.debug("FR-code-editor-validate-result: accepted")
    return result
