"""Typed HTTP adapter for the complete editor command additions.

Description:
    Connects catalogues, disk reload, import repair, compilation and source-export
    authoring to existing editor envelopes and host-owned execution/persistence.
Purpose:
    FEAT-CODE-EDITOR-COMMANDS: Deliver complete editor workflows.
Key Capabilities:
    - FR-editor-command-http: Log each operation and safe validation rejection;
      HTTP tests verify requests, responses and durable job delivery.
Python API Usage:
    install_commands(router)
CLI Usage:
    uv run python -m pytest tests/workspace/code_editor --no-cov
"""

import logging
import threading

from fastapi import APIRouter, Request

from app.core.jobs.manager import JobManager
from app.workspace.code_editor._common import CodeEditorError
from app.workspace.code_editor._storage import StateStore
from app.workspace.code_editor.catalogue import indicator_catalogue, symbol_catalogue
from app.workspace.code_editor.command_models import (
    CodeTypeInfo,
    CompilationRequest,
    CompilationSnapshot,
    ExportTemplateRequest,
    FormatInfo,
    IndicatorInfo,
    PathInfo,
    ReloadRequest,
    ReloadResult,
    RepairRequest,
    RepairResult,
    SymbolInfo,
)
from app.workspace.code_editor.compilation import CompilationService
from app.workspace.code_editor.export_templates import (
    create_export_template,
    supported_formats,
)
from app.workspace.code_editor.import_repair import repair_imports
from app.workspace.code_editor.path_policy import inspect_path
from app.workspace.code_editor.results import SaveResult, SuccessEnvelope

logger = logging.getLogger(__name__)
_lifecycle_lock = threading.Lock()


def compilation_service(request: Request) -> CompilationService:
    """Lazily allocate a host-owned pool; app lifespan shuts it down."""
    with _lifecycle_lock:
        state = request.app.state
        service: CompilationService | None = getattr(
            state, "code_editor_compilation", None
        )
        if service is None:
            gateway = getattr(state, "persistence", None)
            store = StateStore(gateway)
            manager = JobManager(max_workers=1, persistence=store.gateway)
            state.code_editor_jobs = manager
            service = CompilationService(manager, store)
            state.code_editor_compilation = service
        return service


def install_commands(router: APIRouter) -> None:
    """Register typed command routes under the existing validation adapter."""

    @router.get("/code-types", response_model=SuccessEnvelope[list[CodeTypeInfo]])
    def code_types() -> SuccessEnvelope[list[CodeTypeInfo]]:
        from app.workspace.code_editor.templates import list_templates

        logger.debug("FR-editor-command-http: code types")
        records = [
            CodeTypeInfo(
                type_id=t["template_id"],
                name=t["name"],
                subtypes=["Open", "Modify", "Close"]
                if t["template_id"] == "BlocksOrder"
                else [],
            )
            for t in list_templates()
        ]
        records.extend(
            [
                CodeTypeInfo(
                    type_id="MonteCarlo",
                    name="Monte Carlo",
                    subtypes=["Manipulation", "Retest"],
                ),
                CodeTypeInfo(
                    type_id="CodeExport",
                    name="Code export template",
                    subtypes=[f.format_id for f in supported_formats()],
                ),
            ]
        )
        return {"status": "success", "data": records}

    @router.post("/file/reload", response_model=SuccessEnvelope[ReloadResult])
    def reload_disk(req: ReloadRequest) -> SuccessEnvelope[ReloadResult]:
        from app.workspace.code_editor.http import _code_editor

        logger.debug("FR-editor-command-http: reload")
        tab = _code_editor.editor.reload_disk(
            req.file_path, discard_dirty=req.discard_dirty
        )
        return {
            "status": "success",
            "data": ReloadResult(tab=tab, active_file=tab["file_path"]),
        }

    @router.get("/catalogue/symbols", response_model=SuccessEnvelope[list[SymbolInfo]])
    def symbols() -> SuccessEnvelope[list[SymbolInfo]]:
        logger.debug("FR-editor-command-http: symbols")
        return {"status": "success", "data": symbol_catalogue()}

    @router.get(
        "/catalogue/indicators", response_model=SuccessEnvelope[list[IndicatorInfo]]
    )
    def indicators() -> SuccessEnvelope[list[IndicatorInfo]]:
        logger.debug("FR-editor-command-http: indicators")
        return {"status": "success", "data": indicator_catalogue()}

    @router.get("/file/info", response_model=SuccessEnvelope[PathInfo])
    def path_info(file_path: str) -> SuccessEnvelope[PathInfo]:
        logger.debug("FR-editor-command-http: path info")
        try:
            info = inspect_path(file_path)
        except ValueError:
            raise CodeEditorError("Path is outside the authorized root") from None
        return {"status": "success", "data": info}

    @router.post("/imports/repair", response_model=SuccessEnvelope[RepairResult])
    def repair(req: RepairRequest) -> SuccessEnvelope[RepairResult]:
        logger.debug("FR-editor-command-http: repair")
        return {"status": "success", "data": repair_imports(req)}

    @router.get("/export-formats", response_model=SuccessEnvelope[list[FormatInfo]])
    def formats(file_path: str | None = None) -> SuccessEnvelope[list[FormatInfo]]:
        logger.debug("FR-editor-command-http: formats")
        return {"status": "success", "data": supported_formats(file_path)}

    @router.post("/export-templates", response_model=SuccessEnvelope[SaveResult])
    def export_template(req: ExportTemplateRequest) -> SuccessEnvelope[SaveResult]:
        logger.debug("FR-editor-command-http: export template")
        return {"status": "success", "data": create_export_template(req)}

    @router.post("/compilations", response_model=SuccessEnvelope[CompilationSnapshot])
    def compile_start(
        req: CompilationRequest, request: Request
    ) -> SuccessEnvelope[CompilationSnapshot]:
        logger.debug("FR-editor-command-http: compile start")
        return {"status": "success", "data": compilation_service(request).start(req)}

    @router.get(
        "/compilations", response_model=SuccessEnvelope[CompilationSnapshot | None]
    )
    def compile_info(
        request: Request, job_id: str | None = None
    ) -> SuccessEnvelope[CompilationSnapshot | None]:
        logger.debug("FR-editor-command-http: compile info")
        return {"status": "success", "data": compilation_service(request).get(job_id)}

    @router.post(
        "/compilations/{job_id}/cancel",
        response_model=SuccessEnvelope[CompilationSnapshot],
    )
    def compile_cancel(
        job_id: str, request: Request
    ) -> SuccessEnvelope[CompilationSnapshot]:
        logger.debug("FR-editor-command-http: compile cancel")
        return {
            "status": "success",
            "data": compilation_service(request).cancel(job_id),
        }
