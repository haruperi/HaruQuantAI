"""Editor HTTP contracts for documents, templates, extensions and indicator tests."""

from __future__ import annotations

import re
import zipfile
from collections.abc import Callable, Coroutine
from typing import Any, override

from fastapi import APIRouter
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import Response

from app.core.host.logging import get_logger
from app.core.host.transport import TransportError
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.import_export import ImportExport
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.mcp import router as mcp_router
from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import (
    list_templates,
    render_template,
)

logger = get_logger(__name__)


class EditorRoute(APIRoute):
    """Translate expected workspace errors consistently across every endpoint."""

    @override
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Return the common editor error boundary."""
        handler = super().get_route_handler()

        async def wrapped(request: Request) -> Response:
            try:
                return await handler(request)
            except (
                CodeEditorError,
                OSError,
                ValueError,
                re.error,
                zipfile.BadZipFile,
            ) as exc:
                logger.warning("Editor operation rejected: %s", exc)
                raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc

        return wrapped


router = APIRouter(
    route_class=EditorRoute, prefix="/api/v1/code-editor", tags=["code_editor"]
)

_code_editor = CodeEditor()
_import_export = ImportExport()
_indicator_tester = IndicatorTester()


def _envelope(data: Any) -> dict[str, Any]:
    return {"status": "success", "data": data}


class OpenTabRequest(BaseModel):
    """Payload to open a file tab."""

    file_path: str
    mode: str = "python"


class CloseTabRequest(BaseModel):
    """Payload to close a file tab."""

    file_path: str
    force: bool = False


class SaveFileRequest(BaseModel):
    """Payload to save file contents."""

    file_path: str
    content: str


class SaveAllRequest(BaseModel):
    """Payload to save multiple files."""

    files: list[dict[str, str]] | None = None


class NewFileRequest(BaseModel):
    """Payload to create a new source file."""

    file_path: str
    content: str = ""


class NewDirRequest(BaseModel):
    """Payload to create a new directory."""

    dir_path: str


class CloneRequest(BaseModel):
    """Payload to clone an existing file."""

    source_path: str
    target_path: str


class RenameRequest(BaseModel):
    """Payload to rename a file or directory."""

    old_path: str
    new_path: str


class DeleteRequest(BaseModel):
    """Payload to delete a file or directory."""

    file_path: str


class SearchRequest(BaseModel):
    """Payload for finding text patterns across files."""

    query: str
    case_sensitive: bool = False
    regex: bool = False
    whole_word: bool = False
    search_dir: str | None = None


class CompileRequest(BaseModel):
    """Payload for AST compile and hot-reloading."""

    file_path: str
    content: str | None = None


class CreateSnippetRequest(BaseModel):
    """Payload to instantiate a template snippet."""

    template_type: str
    name: str
    category: str = "custom"


class RenderTemplateRequest(BaseModel):
    """Payload to preview a template's generated code."""

    template_id: str
    name: str
    category: str | None = None


class ExportPackRequest(BaseModel):
    """Payload to bundle snippets into an archive."""

    file_paths: list[str]
    archive_path: str
    metadata: dict[str, Any] | None = None


class InspectPackRequest(BaseModel):
    """Payload to inspect an extension pack archive."""

    archive_path: str


class ImportPackRequest(BaseModel):
    """Payload to extract and install an extension pack."""

    archive_path: str
    resolution_rules: dict[str, str] | None = None


class IndicatorTestRunRequest(BaseModel):
    """Payload to execute an indicator test bench run."""

    indicator_name: str
    symbol: str = "EURUSD"
    timeframe: str = "H1"
    params: dict[str, Any] | None = None
    bars_to_reserve: int = Field(default=50, ge=0, le=10000)
    bar_count: int = Field(default=150, ge=1, le=10000)
    reference_values: list[float] | None = None


class IndicatorTestNewRequest(BaseModel):
    """Payload to initialize an indicator test configuration."""

    indicator_name: str
    symbol: str = "EURUSD"
    timeframe: str = "H1"


class IndicatorTestEditParamsRequest(BaseModel):
    """Payload to edit indicator test parameters."""

    test_id: str
    params: dict[str, Any] = Field(default_factory=dict)


@router.get("/init")
def get_workspace_init() -> dict[str, Any]:
    """Return workspace panels, active tabs, and layout state."""
    return _envelope(_code_editor.editor.init_workspace())


@router.get("/navigator")
def get_navigator(root_dir: str | None = None) -> dict[str, Any]:
    """Return snippet repository directory tree."""
    return _envelope(_code_editor.navigator(root_dir))


@router.get("/tabs")
def get_tabs() -> dict[str, Any]:
    """Return list of open editor tabs."""
    return _envelope(_code_editor.maintabs())


@router.post("/tabs/open")
def open_tab(req: OpenTabRequest) -> dict[str, Any]:
    """Open a file into an editor tab."""
    try:
        res = _code_editor.editor.open_file_tab(req.file_path, mode=req.mode)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/tabs/close")
def close_tab(req: CloseTabRequest) -> dict[str, Any]:
    """Close an editor tab with optional force flag."""
    return _envelope(_code_editor.editor.close_file_tab(req.file_path, force=req.force))


@router.post("/file/save")
def save_file(req: SaveFileRequest) -> dict[str, Any]:
    """Save document content to disk and return diagnostics."""
    try:
        res = _code_editor.editor.save_file(req.file_path, req.content)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/file/save-all")
def save_all(req: SaveAllRequest) -> dict[str, Any]:
    """Batch save multiple open documents."""
    return _envelope(_code_editor.editor.save_all_files(req.files))


@router.post("/file/new")
def new_file(req: NewFileRequest) -> dict[str, Any]:
    """Create a new file in snippet workspace."""
    try:
        res = _code_editor.new_file(req.file_path, req.content)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/file/new-dir")
def new_dir(req: NewDirRequest) -> dict[str, Any]:
    """Create a new directory in snippet repository."""
    try:
        res = _code_editor.new_dir(req.dir_path)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/file/clone")
def clone_file(req: CloneRequest) -> dict[str, Any]:
    """Duplicate an existing file with a target path."""
    try:
        res = _code_editor.clone(req.source_path, req.target_path)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/file/rename")
def rename_file(req: RenameRequest) -> dict[str, Any]:
    """Rename a file or folder in the workspace."""
    try:
        res = _code_editor.rename_file(req.old_path, req.new_path)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/file/delete")
def delete_file(req: DeleteRequest) -> dict[str, Any]:
    """Safely delete a file or directory."""
    try:
        res = _code_editor.delete_file(req.file_path)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/search")
def search_files(req: SearchRequest) -> dict[str, Any]:
    """Search for text or regex patterns across snippet files."""
    matches = _code_editor.find_in_files(
        req.query,
        case_sensitive=req.case_sensitive,
        regex=req.regex,
        whole_word=req.whole_word,
        search_dir=req.search_dir,
    )
    return _envelope(matches)


@router.post("/compile")
def compile_file(req: CompileRequest) -> dict[str, Any]:
    """Validate Python AST syntax and dynamically reload snippet."""
    res = _code_editor.compile_file(req.file_path, req.content)
    return _envelope(res)


@router.post("/compile-all")
def compile_all() -> dict[str, Any]:
    """Batch compile and reload all repository snippets."""
    return _envelope(_code_editor.compile_all())


@router.get("/templates")
def get_templates() -> dict[str, Any]:
    """Return catalog metadata for all 12 templates."""
    return _envelope(list_templates())


@router.post("/templates/render")
def render_template_preview(req: RenderTemplateRequest) -> dict[str, Any]:
    """Generate boilerplate code and target path for template preview."""
    try:
        code, path = render_template(req.template_id, req.name, req.category)
        return _envelope({"content": code, "file_path": path})
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/templates/create")
def create_from_template(req: CreateSnippetRequest) -> dict[str, Any]:
    """Instantiate template snippet on disk and open tab."""
    try:
        res = _code_editor.create_new(req.template_type, req.name, req.category)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/import-export/export")
def export_pack(req: ExportPackRequest) -> dict[str, Any]:
    """Export snippets into a .zip package with manifest."""
    try:
        res = _import_export.export(req.file_paths, req.archive_path, req.metadata)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/import-export/inspect")
def inspect_pack(req: InspectPackRequest) -> dict[str, Any]:
    """Preview contents and collisions of an extension archive."""
    try:
        res = _import_export.imported_files(req.archive_path)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/import-export/import")
def import_pack(req: ImportPackRequest) -> dict[str, Any]:
    """Extract archive applying overwrite/skip/rename policies."""
    try:
        res = _import_export.overwrite_confirm(req.archive_path, req.resolution_rules)
        return _envelope(res)
    except CodeEditorError as exc:
        raise TransportError(ErrorCode.VALIDATION, str(exc)) from exc


@router.post("/indicator-test/run")
def run_indicator_test(req: IndicatorTestRunRequest) -> dict[str, Any]:
    """Execute indicator on bars and return chart and table series."""
    res = _indicator_tester.indicator_tester(
        indicator_name=req.indicator_name,
        symbol=req.symbol,
        timeframe=req.timeframe,
        params=req.params,
        bars_to_reserve=req.bars_to_reserve,
        bar_count=req.bar_count,
        reference_values=req.reference_values,
    )
    return _envelope(res)


@router.post("/indicator-test/new")
def new_indicator_test(req: IndicatorTestNewRequest) -> dict[str, Any]:
    """Create a new indicator test configuration."""
    res = _indicator_tester.new_indy_test(
        req.indicator_name, symbol=req.symbol, timeframe=req.timeframe
    )
    return _envelope(res)


@router.post("/indicator-test/edit-params")
def edit_indicator_params(
    req: IndicatorTestEditParamsRequest,
) -> dict[str, Any]:
    """Update parameters and re-calculate indicator values."""
    res = _indicator_tester.edit_indy_params(req.test_id, req.params)
    return _envelope(res)


class SessionTabRequest(BaseModel):
    """A validated editor buffer snapshot."""

    file_path: str
    content: str
    mode: str = "python"


class SessionRequest(BaseModel):
    """Complete current buffer snapshot and active tab."""

    tabs: list[SessionTabRequest]
    active_file: str | None = None


class SaveTestRequest(BaseModel):
    """A named indicator configuration to persist."""

    test_id: str
    name: str


@router.post("/session")
def sync_session(req: SessionRequest) -> dict[str, Any]:
    """FR-CODEEDITOR-SESSION: Synchronize unsaved buffers and tab selection."""
    return _envelope(
        _code_editor.editor.sync_session(
            [tab.model_dump() for tab in req.tabs], req.active_file
        )
    )


@router.get("/indicator-test/errors")
def indicator_errors(test_id: str | None = None) -> dict[str, Any]:
    """Return calculation anomalies with locations."""
    return _envelope(_indicator_tester.indicator_tester_error(test_id))


@router.post("/indicator-test/save")
def save_indicator_config(req: SaveTestRequest) -> dict[str, Any]:
    """Persist a complete test configuration."""
    return _envelope(_indicator_tester.save_test_config(req.test_id, req.name))


@router.get("/indicator-test/load")
def load_indicator_config(config_id: str) -> dict[str, Any]:
    """Restore a saved indicator test."""
    return _envelope(_indicator_tester.load_test_config(config_id))


@router.get("/tools")
def extension_tools() -> dict[str, Any]:
    """List compiled AI tools with MCP-compatible input schemas."""
    from app.workspace.code_editor.registry import registry

    return _envelope(
        [
            {
                "name": name,
                "description": tool.description,
                "inputSchema": tool.get_input_schema(),
            }
            for name, tool in registry.tools.items()
        ]
    )


@router.post("/tools/{name}/call")
def call_extension_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a compiled AI extension."""
    from app.workspace.code_editor.registry import registry

    return _envelope(registry.call_tool(name, arguments))


router.include_router(mcp_router)
