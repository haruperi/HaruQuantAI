"""Typed editor command inputs and durable results.

Description:
    Defines reload, catalogue, import repair, export and compilation boundaries.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Complete the editor command surface.
Key Capabilities:
    - FR-editor-command-validation: Reject malformed requests; route tests verify
      acceptance/rejection logs without source or secret-bearing values.
Python API Usage:
    request = ReloadRequest(file_path="app/extend/user/example.py")
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.lib.errors import JSONValue
from app.workspace.code_editor.requests import EditorRequest
from app.workspace.code_editor.results import CompileResult, Tab


class CommandResult(BaseModel):
    """Reject undeclared output fields and non-finite results."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ReloadRequest(EditorRequest):
    """Reload disk only after explicit dirty-buffer authority."""

    file_path: str
    discard_dirty: bool = False


class ReloadResult(CommandResult):
    """A successfully reloaded clean document."""

    tab: Tab
    active_file: str


class SymbolInfo(CommandResult):
    """Statically indexed public Python symbol and its declared members."""

    name: str
    module: str
    file_path: str
    kind: Literal["class", "function", "variable"]
    members: list[str] = Field(default_factory=list)


class IndicatorInfo(CommandResult):
    """Canonical indicator identity and validated metadata."""

    identity: str
    name: str
    file_path: str
    outputs: list[str]
    parameters: dict[str, JSONValue]
    protected: bool


class RepairRequest(EditorRequest):
    """Preview by default; apply only explicit candidate selections."""

    file_path: str
    content: str
    selections: dict[str, str] = Field(default_factory=dict)


class ImportChoice(CommandResult):
    """All possible modules for an unresolved symbol."""

    symbol: str
    candidates: list[str]


class RepairResult(CommandResult):
    """Repaired buffer plus remaining ambiguous/unresolved symbols."""

    content: str
    added: list[str]
    unresolved: list[ImportChoice]


class CompilationRequest(EditorRequest):
    """File uses the supplied buffer; other scopes compile saved Python files."""

    scope: Literal["file", "package", "all", "registered"] = "file"
    file_path: str | None = None
    content: str | None = None


class CompilationSnapshot(CommandResult):
    """Durable editor-specific result; host owns execution/lifecycle records."""

    job_id: str
    status: Literal[
        "QUEUED", "RUNNING", "PAUSED", "COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"
    ]
    progress: float = Field(ge=0, le=100)
    results: list[CompileResult] = Field(default_factory=list)
    message: str = ""
    cancellation_requested: bool = False
    source_hashes: dict[str, str] = Field(default_factory=dict)


class ExportTemplateRequest(EditorRequest):
    """Create a source-authoring template, not an executable strategy export."""

    source_paths: list[str] = Field(min_length=1, max_length=100)
    target_path: str
    format_id: Literal["python", "pseudocode"]


class FormatInfo(CommandResult):
    """Supported source-authoring format and extension."""

    format_id: str
    name: str
    extension: str


class CodeTypeInfo(CommandResult):
    """Supported authoring family and explicit subtype choices."""

    type_id: str
    name: str
    subtypes: list[str] = Field(default_factory=list)


class PathInfo(CommandResult):
    """Single shared policy used by navigation, editor and mutation commands."""

    file_path: str
    ownership: Literal["builtin", "user", "host"]
    protected: bool
    exists: bool
    clone_target: str


class SuiteIndicatorOption(CommandResult):
    """Expanded indicator/output option for batch suite configuration."""

    identity: str
    indicator: str
    class_name: str
    output: str
    file_path: str
    default_parameters: str
    parameters: dict[str, JSONValue]
    protected: bool


class SuiteTestCaseModel(CommandResult):
    """Single indicator/output test row in a batch suite configuration."""

    test_id: str
    use: bool = True
    indicator: str
    parameters: str = ""
    decimals: int = Field(default=6, ge=0, le=12)
    result: str = ""
    shift: int = Field(default=0, ge=0, le=500)
    file_name: str = ""
    exists: bool = False
    show_grid: bool = False
    errors: list[str] = Field(default_factory=list)


class SuiteConfigModel(CommandResult):
    """Batch indicator suite configuration with donor XML fidelity."""

    engine: str = "MetaTrader4"
    bars_to_reserve: int = Field(default=300, ge=0, le=10000)
    tests: list[SuiteTestCaseModel] = Field(default_factory=list)


class SuiteCreateConfigRequest(EditorRequest):
    """Create a fresh batch indicator suite configuration."""

    indicators: list[str] = Field(default_factory=list, max_length=500)
    engine: str = "MetaTrader4"
    bars_to_reserve: int = Field(default=300, ge=0, le=10000)


class SuiteAddTestsRequest(EditorRequest):
    """Append indicator test cases with explicit duplicate-row handling."""

    indicators: list[str] = Field(min_length=1, max_length=500)
    allow_duplicates: bool = False


class SuiteSaveConfigRequest(EditorRequest):
    """Persist suite configuration as JSON state and donor XML."""

    config: SuiteConfigModel | None = None
    xml_content: str | None = None


class SuiteLoadConfigRequest(EditorRequest):
    """Load suite configuration from stored state or explicit XML payload."""

    xml_content: str | None = None


class SuiteStartRequest(EditorRequest):
    """Start batch indicator suite execution with optional config override."""

    config: SuiteConfigModel | None = None
    selected_only: bool = True


class SuiteSnapshot(CommandResult):
    """Durable batch indicator suite execution snapshot."""

    job_id: str
    status: Literal[
        "IDLE",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "STOPPED",
        "FAILED",
        "INTERRUPTED",
    ]
    status_code: Literal[0, 1, 3, 4] = 0
    progress: float = Field(default=0.0, ge=0, le=100)
    completed_tests: int = 0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    cancellation_requested: bool = False
    message: str = ""
    config: SuiteConfigModel
    xml_content: str = ""


class TestDistributionRequest(EditorRequest):
    """Install indicator reference test bundle with mandatory SHA-256 verification."""

    __test__ = False

    archive_path: str | None = None
    source_url: str | None = None
    expected_sha256: str = Field(
        min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$"
    )


class TestDistributionSnapshot(CommandResult):
    """Progress and terminal outcome for indicator test-data distribution."""

    __test__ = False

    job_id: str
    status: Literal["IDLE", "RUNNING", "COMPLETED", "FAILED"]
    progress: float = Field(default=0.0, ge=0, le=100)
    completed: bool = False
    error: str = ""
    installed_files: list[str] = Field(default_factory=list)
    config_updated: bool = False


class CalibrationRequest(EditorRequest):
    """Calibrate indicator output ranges across historical symbols and timeframes."""

    project_name: str = "Default"
    task_name: str | None = None
    symbols: list[str] = Field(min_length=1, max_length=50)
    timeframes: list[str] = Field(min_length=1, max_length=20)
    engine: str = "MetaTrader4"
    max_steps: int = Field(default=-1, ge=-1, le=10000)
    indicators: list[str] = Field(default_factory=list, max_length=200)
    ranges_config_text: str | None = None
    bars_count: int = Field(default=500, ge=50, le=10000)


class CalibratedRangeEntry(CommandResult):
    """Beautified min/max/step range derived from indicator population statistics."""

    key: str
    indicator: str
    output: str
    min_value: float
    max_value: float
    step: float
    mean: float
    std_dev: float
    samples: int


class CalibrationResult(CommandResult):
    """Completed indicator calibration summary and persisted ranges."""

    project_name: str
    task_name: str | None = None
    engine: str
    calibrated_count: int
    skipped_indicators: list[str] = Field(default_factory=list)
    ranges: list[CalibratedRangeEntry] = Field(default_factory=list)


class SkippedImportItem(CommandResult):
    """File skipped or rejected during an interactive import session."""

    name: str
    reason: str


class ImportSessionStartRequest(EditorRequest):
    """Start an interactive import session for one or more extension archives."""

    archive_paths: list[str] = Field(min_length=1, max_length=20)
    timeout_seconds: float = Field(default=60.0, gt=0.0, le=300.0)


class ImportSessionActionRequest(EditorRequest):
    """Apply a user conflict decision to an active interactive import session."""

    session_id: str
    action: Literal["overwrite", "overwrite_always", "skip", "skip_always", "cancel"]


class ImportSessionSnapshot(CommandResult):
    """State of an interactive import conflict-resolution session."""

    session_id: str
    status: Literal[
        "RUNNING",
        "AWAITING_DECISION",
        "COMPLETED",
        "CANCELLED",
        "TIMED_OUT",
        "FAILED",
    ]
    decision_mode: Literal[0, 1, 2, 3, 4, 5] = 0
    current_conflict: str | None = None
    current_archive: str | None = None
    processed_entries: int = 0
    total_entries: int = 0
    new_files: list[str] = Field(default_factory=list)
    not_imported_files: list[SkippedImportItem] = Field(default_factory=list)
    reload_results: list[CompileResult] = Field(default_factory=list)
    message: str = ""
