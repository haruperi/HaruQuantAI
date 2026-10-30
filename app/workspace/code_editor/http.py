"""Typed editor HTTP requests, results and host error adaptation.

Description:
    Validates existing editor HTTP requests/results and adapts failures through
    host transport categories. Routes and successful payload shapes are retained.
    Services own domain work; host capabilities own persistence/jobs/events.
Purpose:
    FEAT-CODE-EDITOR-CONTRACTS: Preserve explicit editor boundary contracts.
Key Capabilities:
    - FR-code-editor-http-operation: Observe completed/rejected/failed operations;
      integration and logging tests verify safe records without request contents.
    - FR-code-editor-http-request: Reject invalid requests using host envelopes;
      nested-input integration cases verify validation responses.
    - FR-code-editor-http-result: Reject invalid service results without exposing
      their payload; malformed-result integration cases verify safe failures.
Python API Usage:
    from app.workspace.code_editor.http import router
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor/test_http.py --no-cov
"""

from __future__ import annotations

import logging
import re
import zipfile
from collections.abc import Callable, Coroutine
from typing import Any, override

from fastapi import APIRouter
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.routing import APIRoute
from starlette.requests import Request
from starlette.responses import Response

from app.core.host.transport import TransportError
from app.core.lib.errors import JSONValue
from app.core.lib.responses import ErrorCode
from app.workspace.code_editor import results as dto
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor.import_export import ImportExport
from app.workspace.code_editor.indicator_tester import IndicatorTester
from app.workspace.code_editor.mcp import router as mcp_router
from app.workspace.code_editor.requests import (
    CloneRequest,
    CloseTabRequest,
    CompileRequest,
    CreateSnippetRequest,
    DeleteRequest,
    ExportPackRequest,
    ImportPackRequest,
    IndicatorTestEditParamsRequest,
    IndicatorTestNewRequest,
    IndicatorTestRunRequest,
    InspectPackRequest,
    NewDirRequest,
    NewFileRequest,
    OpenTabRequest,
    RenameRequest,
    RenderTemplateRequest,
    SaveAllRequest,
    SaveAsRequest,
    SaveFileRequest,
    SaveTestRequest,
    SearchRequest,
    SessionRequest,
    SessionTabRequest,
)

__all__ = [
    "CloneRequest",
    "CloseTabRequest",
    "CompileRequest",
    "CreateSnippetRequest",
    "DeleteRequest",
    "ExportPackRequest",
    "ImportPackRequest",
    "IndicatorTestEditParamsRequest",
    "IndicatorTestNewRequest",
    "IndicatorTestRunRequest",
    "InspectPackRequest",
    "NewDirRequest",
    "NewFileRequest",
    "OpenTabRequest",
    "RenameRequest",
    "RenderTemplateRequest",
    "SaveAllRequest",
    "SaveAsRequest",
    "SaveFileRequest",
    "SaveTestRequest",
    "SearchRequest",
    "SessionRequest",
    "SessionTabRequest",
    "router",
]

from app.workspace.code_editor.routes import CodeEditor
from app.workspace.code_editor.templates import (
    list_templates,
    render_template,
)

logger = logging.getLogger(__name__)


class EditorRoute(APIRoute):
    """Translate expected workspace errors consistently across every endpoint."""

    @override
    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Return the common editor error boundary."""
        logger.debug("FR-code-editor-http-get-route-handler: invoked")
        handler = super().get_route_handler()

        async def wrapped(request: Request) -> Response:
            logger.debug("FR-code-editor-http-wrapped: invoked")
            try:
                response = await handler(request)
                logger.info("FR-code-editor-http-operation: completed")
                return response
            except RequestValidationError:
                logger.warning("FR-code-editor-http-request: rejected")
                raise TransportError(
                    ErrorCode.VALIDATION, "Invalid editor request"
                ) from None
            except ResponseValidationError:
                logger.error("FR-code-editor-http-result: rejected")
                raise TransportError(
                    ErrorCode.INTERNAL, "Invalid editor result"
                ) from None
            except CodeEditorError as exc:
                logger.warning(
                    "FR-code-editor-http-operation: rejected category=%s",
                    exc.category.value,
                )
                raise TransportError(exc.category, str(exc)) from None
            except (
                OSError,
                ValueError,
                re.error,
                zipfile.BadZipFile,
            ) as exc:
                logger.warning("FR-code-editor-http-operation: rejected")
                raise TransportError(
                    ErrorCode.VALIDATION, "Editor operation rejected"
                ) from None
            except Exception:
                logger.error("FR-code-editor-http-operation: failed")
                raise TransportError(
                    ErrorCode.INTERNAL, "Editor operation failed"
                ) from None

        return wrapped


router = APIRouter(
    route_class=EditorRoute, prefix="/api/v1/code-editor", tags=["code_editor"]
)

_code_editor = CodeEditor()
_import_export = ImportExport()
_indicator_tester = IndicatorTester()


def _envelope[T](data: T) -> dto.SuccessEnvelope[T]:
    return {"status": "success", "data": data}


@router.get("/init", response_model=dto.SuccessEnvelope[dto.WorkspaceInfo])
def get_workspace_init() -> dto.SuccessEnvelope[dto.WorkspaceInfo]:
    """Return workspace panels, active tabs, and layout state."""
    logger.debug("FR-code-editor-http-get-workspace-init: invoked")
    return _envelope(_code_editor.editor.init_workspace())


@router.get("/navigator", response_model=dto.SuccessEnvelope[dto.NavigatorItem])
def get_navigator(
    root_dir: str | None = None,
    ownership: str = "all",
    filter_text: str = "",
) -> dto.SuccessEnvelope[dto.NavigatorItem]:
    """Return snippet repository directory tree."""
    logger.debug("FR-code-editor-http-get-navigator: invoked")
    return _envelope(
        _code_editor.navigator(root_dir, ownership=ownership, filter_text=filter_text)
    )


@router.get("/tabs", response_model=dto.SuccessEnvelope[list[dto.Tab]])
def get_tabs() -> dto.SuccessEnvelope[list[dto.Tab]]:
    """Return list of open editor tabs."""
    logger.debug("FR-code-editor-http-get-tabs: invoked")
    return _envelope(_code_editor.maintabs())


@router.post("/tabs/open", response_model=dto.SuccessEnvelope[dto.OpenTabResult])
def open_tab(req: OpenTabRequest) -> dto.SuccessEnvelope[dto.OpenTabResult]:
    """Open a file into an editor tab."""
    logger.debug("FR-code-editor-http-open-tab: invoked")
    res = _code_editor.editor.open_file_tab(req.file_path, mode=req.mode)
    return _envelope(res)


@router.post("/tabs/close", response_model=dto.SuccessEnvelope[dto.CloseTabResult])
def close_tab(req: CloseTabRequest) -> dto.SuccessEnvelope[dto.CloseTabResult]:
    """Close an editor tab with optional force flag."""
    logger.debug("FR-code-editor-http-close-tab: invoked")
    return _envelope(_code_editor.editor.close_file_tab(req.file_path, force=req.force))


@router.post("/file/save", response_model=dto.SuccessEnvelope[dto.SaveResult])
def save_file(req: SaveFileRequest) -> dto.SuccessEnvelope[dto.SaveResult]:
    """Save document content to disk and return diagnostics."""
    logger.debug("FR-code-editor-http-save-file: invoked")
    res = _code_editor.editor.save_file(req.file_path, req.content)
    return _envelope(res)


@router.post("/file/save-as", response_model=dto.SuccessEnvelope[dto.SaveAsResult])
def save_as(req: SaveAsRequest) -> dto.SuccessEnvelope[dto.SaveAsResult]:
    """Publish a new file and persist its replacement tab identity."""
    return _envelope(
        _code_editor.editor.save_as(req.source_path, req.target_path, req.content)
    )


@router.post("/file/save-all", response_model=dto.SuccessEnvelope[dto.SaveAllResult])
def save_all(req: SaveAllRequest) -> dto.SuccessEnvelope[dto.SaveAllResult]:
    """Batch save multiple open documents."""
    logger.debug("FR-code-editor-http-save-all: invoked")
    return _envelope(
        _code_editor.editor.save_all_files(
            None
            if req.files is None
            else [
                {"file_path": item.file_path, "content": item.content}
                for item in req.files
            ]
        )
    )


@router.post("/file/new", response_model=dto.SuccessEnvelope[dto.SaveResult])
def new_file(req: NewFileRequest) -> dto.SuccessEnvelope[dto.SaveResult]:
    """Create a new file in snippet workspace."""
    logger.debug("FR-code-editor-http-new-file: invoked")
    res = _code_editor.new_file(req.file_path, req.content)
    return _envelope(res)


@router.post("/file/new-dir", response_model=dto.SuccessEnvelope[dto.DirectoryResult])
def new_dir(req: NewDirRequest) -> dto.SuccessEnvelope[dto.DirectoryResult]:
    """Create a new directory in snippet repository."""
    logger.debug("FR-code-editor-http-new-dir: invoked")
    res = _code_editor.new_dir(req.dir_path)
    return _envelope(res)


@router.post("/file/clone", response_model=dto.SuccessEnvelope[dto.SaveResult])
def clone_file(req: CloneRequest) -> dto.SuccessEnvelope[dto.SaveResult]:
    """Duplicate an existing file with a target path."""
    logger.debug("FR-code-editor-http-clone-file: invoked")
    res = _code_editor.clone(req.source_path, req.target_path)
    return _envelope(res)


@router.post("/file/rename", response_model=dto.SuccessEnvelope[dto.RenameResult])
def rename_file(req: RenameRequest) -> dto.SuccessEnvelope[dto.RenameResult]:
    """Rename a file or folder in the workspace."""
    logger.debug("FR-code-editor-http-rename-file: invoked")
    res = _code_editor.rename_file(req.old_path, req.new_path)
    return _envelope(res)


@router.post("/file/delete", response_model=dto.SuccessEnvelope[dto.DeleteResult])
def delete_file(req: DeleteRequest) -> dto.SuccessEnvelope[dto.DeleteResult]:
    """Safely delete a file or directory."""
    logger.debug("FR-code-editor-http-delete-file: invoked")
    res = _code_editor.delete_file(req.file_path)
    return _envelope(res)


@router.post("/search", response_model=dto.SuccessEnvelope[list[dto.SearchMatch]])
def search_files(req: SearchRequest) -> dto.SuccessEnvelope[list[dto.SearchMatch]]:
    """Search for text or regex patterns across snippet files."""
    logger.debug("FR-code-editor-http-search-files: invoked")
    matches = _code_editor.find_in_files(
        req.query,
        case_sensitive=req.case_sensitive,
        regex=req.regex,
        whole_word=req.whole_word,
        search_dir=req.search_dir,
    )
    return _envelope(matches)


@router.post("/compile", response_model=dto.SuccessEnvelope[dto.CompileResult])
def compile_file(req: CompileRequest) -> dto.SuccessEnvelope[dto.CompileResult]:
    """Validate Python AST syntax and dynamically reload snippet."""
    logger.debug("FR-code-editor-http-compile-file: invoked")
    res = _code_editor.compile_file(req.file_path, req.content)
    return _envelope(res)


@router.post("/compile-all", response_model=dto.SuccessEnvelope[dto.CompileAllResult])
def compile_all() -> dto.SuccessEnvelope[dto.CompileAllResult]:
    """Batch compile and reload all repository snippets."""
    logger.debug("FR-code-editor-http-compile-all: invoked")
    return _envelope(_code_editor.compile_all())


@router.get("/templates", response_model=dto.SuccessEnvelope[list[dto.TemplateInfo]])
def get_templates(
    file_path: str | None = None,
) -> dto.SuccessEnvelope[list[dto.TemplateInfo]]:
    """Return catalog metadata for all 12 templates."""
    logger.debug("FR-code-editor-http-get-templates: invoked")
    return _envelope(list_templates(file_path))


@router.post(
    "/templates/render", response_model=dto.SuccessEnvelope[dto.TemplatePreview]
)
def render_template_preview(
    req: RenderTemplateRequest,
) -> dto.SuccessEnvelope[dto.TemplatePreview]:
    """Generate boilerplate code and target path for template preview."""
    logger.debug("FR-code-editor-http-render-template-preview: invoked")
    code, path = render_template(
        req.template_id,
        req.name,
        req.category,
        req.indicator,
        req.order_action_type,
        req.mc_type,
    )
    return _envelope({"content": code, "file_path": path})


@router.post(
    "/templates/create", response_model=dto.SuccessEnvelope[dto.CreatedSnippet]
)
def create_from_template(
    req: CreateSnippetRequest,
) -> dto.SuccessEnvelope[dto.CreatedSnippet]:
    """Instantiate template snippet on disk and open tab."""
    logger.debug("FR-code-editor-http-create-from-template: invoked")
    res = _code_editor.create_new(
        req.template_type,
        req.name,
        req.category,
        indicator=req.indicator,
        order_action_type=req.order_action_type,
        mc_type=req.mc_type,
    )
    return _envelope(res)


@router.post(
    "/import-export/export", response_model=dto.SuccessEnvelope[dto.ExportResult]
)
def export_pack(req: ExportPackRequest) -> dto.SuccessEnvelope[dto.ExportResult]:
    """Export snippets into a .zip package with manifest."""
    logger.debug("FR-code-editor-http-export-pack: invoked")
    res = _import_export.export(req.file_paths, req.archive_path, req.metadata)
    return _envelope(res)


@router.post(
    "/import-export/inspect", response_model=dto.SuccessEnvelope[list[dto.ArchiveEntry]]
)
def inspect_pack(
    req: InspectPackRequest,
) -> dto.SuccessEnvelope[list[dto.ArchiveEntry]]:
    """Preview contents and collisions of an extension archive."""
    logger.debug("FR-code-editor-http-inspect-pack: invoked")
    res = _import_export.imported_files(req.archive_path)
    return _envelope(res)


@router.post(
    "/import-export/import", response_model=dto.SuccessEnvelope[dto.ImportResult]
)
def import_pack(req: ImportPackRequest) -> dto.SuccessEnvelope[dto.ImportResult]:
    """Extract archive applying overwrite/skip/rename policies."""
    logger.debug("FR-code-editor-http-import-pack: invoked")
    res = _import_export.overwrite_confirm(req.archive_path, req.resolution_rules)
    return _envelope(res)


@router.post(
    "/indicator-test/run", response_model=dto.SuccessEnvelope[dto.IndicatorResult]
)
def run_indicator_test(
    req: IndicatorTestRunRequest,
) -> dto.SuccessEnvelope[dto.IndicatorResult]:
    """Execute indicator on bars and return chart and table series."""
    logger.debug("FR-code-editor-http-run-indicator-test: invoked")
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


@router.post(
    "/indicator-test/new", response_model=dto.SuccessEnvelope[dto.IndicatorConfig]
)
def new_indicator_test(
    req: IndicatorTestNewRequest,
) -> dto.SuccessEnvelope[dto.IndicatorConfig]:
    """Create a new indicator test configuration."""
    logger.debug("FR-code-editor-http-new-indicator-test: invoked")
    res = _indicator_tester.new_indy_test(
        req.indicator_name, symbol=req.symbol, timeframe=req.timeframe
    )
    return _envelope(res)


@router.post(
    "/indicator-test/edit-params",
    response_model=dto.SuccessEnvelope[dto.IndicatorResult],
)
def edit_indicator_params(
    req: IndicatorTestEditParamsRequest,
) -> dto.SuccessEnvelope[dto.IndicatorResult]:
    """Update parameters and re-calculate indicator values."""
    logger.debug("FR-code-editor-http-edit-indicator-params: invoked")
    res = _indicator_tester.edit_indy_params(req.test_id, req.params)
    return _envelope(res)


@router.post("/session", response_model=dto.SuccessEnvelope[dto.WorkspaceInfo])
def sync_session(req: SessionRequest) -> dto.SuccessEnvelope[dto.WorkspaceInfo]:
    """FR-CODEEDITOR-SESSION: Synchronize unsaved buffers and tab selection."""
    logger.debug("FR-code-editor-http-sync-session: invoked")
    return _envelope(
        _code_editor.editor.sync_session(
            [tab.model_dump() for tab in req.tabs], req.active_file
        )
    )


@router.get(
    "/indicator-test/errors",
    response_model=dto.SuccessEnvelope[list[dto.IndicatorDiagnostic]],
)
def indicator_errors(
    test_id: str | None = None,
) -> dto.SuccessEnvelope[list[dto.IndicatorDiagnostic]]:
    """Return calculation anomalies with locations."""
    logger.debug("FR-code-editor-http-indicator-errors: invoked")
    return _envelope(_indicator_tester.indicator_tester_error(test_id))


@router.post("/indicator-test/save", response_model=dto.SuccessEnvelope[dto.SavedTest])
def save_indicator_config(req: SaveTestRequest) -> dto.SuccessEnvelope[dto.SavedTest]:
    """Persist a complete test configuration."""
    logger.debug("FR-code-editor-http-save-indicator-config: invoked")
    return _envelope(_indicator_tester.save_test_config(req.test_id, req.name))


@router.get("/indicator-test/load", response_model=dto.SuccessEnvelope[dto.LoadedTest])
def load_indicator_config(config_id: str) -> dto.SuccessEnvelope[dto.LoadedTest]:
    """Restore a saved indicator test."""
    logger.debug("FR-code-editor-http-load-indicator-config: invoked")
    return _envelope(_indicator_tester.load_test_config(config_id))


@router.get("/tools", response_model=dto.SuccessEnvelope[list[dto.ToolInfo]])
def extension_tools() -> dto.SuccessEnvelope[list[dto.ToolInfo]]:
    """List compiled AI tools with MCP-compatible input schemas."""
    logger.debug("FR-code-editor-http-extension-tools: invoked")
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


@router.post("/tools/{name}/call", response_model=dto.SuccessEnvelope[JSONValue])
def call_extension_tool(
    name: str, arguments: dict[str, JSONValue]
) -> dto.SuccessEnvelope[JSONValue]:
    """Dispatch a compiled AI extension."""
    logger.debug("FR-code-editor-http-call-extension-tool: invoked")
    from app.workspace.code_editor.registry import registry

    return _envelope(registry.call_tool(name, arguments))


router.include_router(mcp_router)

from app.workspace.code_editor.command_http import install_commands  # noqa: E402

install_commands(router)
