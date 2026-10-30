"""Typed editor command inputs and durable results.

Description:
    Defines reload, catalogue, import repair, export and compilation boundaries.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Complete the editor command surface.
Key Capabilities:
    - FR-editor-command-validation: Reject malformed requests; route tests verify
      acceptance/rejection logs without source or secret-bearing values.
Python API Usage:
    request = ReloadRequest(file_path="app/include/user/example.py")
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
