"""Validated request records for existing editor operations.

Description:
    Validates nested client inputs before service effects. Extra client fields
    remain ignored; strings and existing Pydantic coercions are preserved.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Make editor request contracts explicit.
Key Capabilities:
    - FR-code-editor-validate-request: Reject non-finite/non-JSON inputs and
      malformed nested records; DEBUG acceptance/WARNING rejection logs are
      verified without logging input contents.
Python API Usage:
    request = SaveFileRequest(file_path="app/include/example.py", content="")
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_contracts.py --no-cov
"""

import logging
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.lib.errors import JSONValue, copy_json

logger = logging.getLogger(__name__)
type ConflictRule = Literal["overwrite", "skip", "rename"]


def _request_json(value: object) -> JSONValue:
    if isinstance(value, BaseModel):
        return _request_json(value.model_dump())
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON keys must be strings")
        return {key: _request_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_request_json(item) for item in value]
    return copy_json(cast("JSONValue", value))


class EditorRequest(BaseModel):
    """Common JSON boundary retaining the client's extra-field compatibility."""

    model_config = ConfigDict(extra="ignore", allow_inf_nan=False)

    @model_validator(mode="before")
    @classmethod
    def finite_json(cls, value: object) -> object:
        """Reject unsafe JSON values without exposing the rejected payload."""
        try:
            _request_json(value)
        except ValueError, RecursionError:
            logger.warning("FR-code-editor-validate-request: rejected JSON")
            raise ValueError("Editor requests require finite JSON values") from None
        logger.debug("FR-code-editor-validate-request: received")
        return value

    @model_validator(mode="after")
    def accepted(self) -> Self:
        """Record successful structural validation without recording contents."""
        logger.debug("FR-code-editor-validate-request: accepted")
        return self


class OpenTabRequest(EditorRequest):
    """Open an existing document; the default mode remains Python."""

    file_path: str
    mode: str = "python"


class CloseTabRequest(EditorRequest):
    """Close a document with explicit dirty-buffer authority."""

    file_path: str
    force: bool = False


class SaveFileRequest(EditorRequest):
    """A complete source buffer; empty content is valid."""

    file_path: str
    content: str


class SaveAllRequest(EditorRequest):
    """None selects dirty tabs; an empty list saves no files."""

    files: list[SaveFileRequest] | None = None


class NewFileRequest(EditorRequest):
    """Create a source file with optional empty content."""

    file_path: str
    content: str = ""


class NewDirRequest(EditorRequest):
    """Create an authorized snippet directory."""

    dir_path: str


class CloneRequest(EditorRequest):
    """Clone an existing source to a new authorized path."""

    source_path: str
    target_path: str


class RenameRequest(EditorRequest):
    """Rename a snippet file or directory."""

    old_path: str
    new_path: str


class DeleteRequest(EditorRequest):
    """Delete an authorized snippet path."""

    file_path: str


class SearchRequest(EditorRequest):
    """Search source with the existing optional matching flags."""

    query: str
    case_sensitive: bool = False
    regex: bool = False
    whole_word: bool = False
    search_dir: str | None = None


class CompileRequest(EditorRequest):
    """None reads disk; an explicit empty string compiles an empty buffer."""

    file_path: str
    content: str | None = None


class CreateSnippetRequest(EditorRequest):
    """Generate a current Python snippet template."""

    template_type: str
    name: str
    category: str = "custom"


class RenderTemplateRequest(EditorRequest):
    """Preview a template without publishing it."""

    template_id: str
    name: str
    category: str | None = None


class ExportPackRequest(EditorRequest):
    """Export saved source paths and finite JSON metadata."""

    file_paths: list[str]
    archive_path: str
    metadata: dict[str, JSONValue] | None = None


class InspectPackRequest(EditorRequest):
    """Inspect a selected archive."""

    archive_path: str


class ImportPackRequest(EditorRequest):
    """Import with the existing three conflict resolutions."""

    archive_path: str
    resolution_rules: dict[str, ConflictRule] | None = None


class IndicatorTestRunRequest(EditorRequest):
    """Run one indicator with class-derived defaults for null parameters."""

    indicator_name: str
    symbol: str = "EURUSD"
    timeframe: str = "H1"
    params: dict[str, JSONValue] | None = None
    bars_to_reserve: int = Field(default=50, ge=0, le=10000)
    bar_count: int = Field(default=150, ge=1, le=10000)
    reference_values: list[float] | None = None


class IndicatorTestNewRequest(EditorRequest):
    """Initialize one indicator configuration."""

    indicator_name: str
    symbol: str = "EURUSD"
    timeframe: str = "H1"


class IndicatorTestEditParamsRequest(EditorRequest):
    """Recalculate an existing test with explicit parameters."""

    test_id: str
    params: dict[str, JSONValue] = Field(default_factory=dict)


class SessionTabRequest(EditorRequest):
    """A buffer snapshot; title/dirty/cursor extras remain accepted and ignored."""

    file_path: str
    content: str
    mode: str = "python"


class SessionRequest(EditorRequest):
    """Replace the current session snapshot, not application storage."""

    tabs: list[SessionTabRequest]
    active_file: str | None = None


class SaveTestRequest(EditorRequest):
    """Persist an existing test under a display name."""

    test_id: str
    name: str
