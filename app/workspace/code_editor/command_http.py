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
    CalibrationRequest,
    CalibrationResult,
    CodeTypeInfo,
    CompilationRequest,
    CompilationSnapshot,
    ExportTemplateRequest,
    FormatInfo,
    ImportSessionActionRequest,
    ImportSessionSnapshot,
    ImportSessionStartRequest,
    IndicatorInfo,
    PathInfo,
    ReloadRequest,
    ReloadResult,
    RepairRequest,
    RepairResult,
    SuiteAddTestsRequest,
    SuiteCreateConfigRequest,
    SuiteIndicatorOption,
    SuiteLoadConfigRequest,
    SuiteSaveConfigRequest,
    SuiteSnapshot,
    SuiteStartRequest,
    SymbolInfo,
    TestDistributionRequest,
    TestDistributionSnapshot,
)
from app.workspace.code_editor.compilation import CompilationService
from app.workspace.code_editor.export_templates import (
    create_export_template,
    supported_formats,
)
from app.workspace.code_editor.import_repair import repair_imports
from app.workspace.code_editor.import_session import (
    ImportSessionService,
    list_exportable_tree,
)
from app.workspace.code_editor.indicator_calibration import (
    IndicatorCalibrationService,
)
from app.workspace.code_editor.indicator_suite import (
    IndicatorSuiteService,
    list_suite_indicators,
)
from app.workspace.code_editor.indicator_test_distribution import (
    IndicatorTestDistributionService,
)
from app.workspace.code_editor.path_policy import inspect_path
from app.workspace.code_editor.results import (
    NavigatorItem,
    SaveResult,
    SuccessEnvelope,
)

logger = logging.getLogger(__name__)
_lifecycle_lock = threading.RLock()


def _ensure_host_jobs(request: Request) -> tuple[JobManager, StateStore]:
    """Ensure shared host-owned JobManager and StateStore on app.state."""
    state = request.app.state
    gateway = getattr(state, "persistence", None)
    store: StateStore | None = getattr(state, "code_editor_store", None)
    if store is None or (gateway is not None and store.gateway is not gateway):
        store = StateStore(gateway)
        state.code_editor_store = store
    manager: JobManager | None = getattr(state, "code_editor_jobs", None)
    if manager is None:
        manager = JobManager(max_workers=1, persistence=store.gateway)
        state.code_editor_jobs = manager
    return manager, store


def compilation_service(request: Request) -> CompilationService:
    """Lazily allocate a host-owned pool; app lifespan shuts it down."""
    with _lifecycle_lock:
        state = request.app.state
        service: CompilationService | None = getattr(
            state, "code_editor_compilation", None
        )
        if service is None:
            manager, store = _ensure_host_jobs(request)
            service = CompilationService(manager, store)
            state.code_editor_compilation = service
        return service


def suite_service(request: Request) -> IndicatorSuiteService:
    """Return or initialize the host-backed IndicatorSuiteService."""
    with _lifecycle_lock:
        state = request.app.state
        service: IndicatorSuiteService | None = getattr(
            state, "code_editor_indicator_suite", None
        )
        if service is None:
            manager, store = _ensure_host_jobs(request)
            tests_dir = getattr(state, "code_editor_tests_dir", None)
            service = IndicatorSuiteService(manager, store, tests_dir=tests_dir)
            state.code_editor_indicator_suite = service
        return service


def distribution_service(request: Request) -> IndicatorTestDistributionService:
    """Return or initialize the host-backed IndicatorTestDistributionService."""
    with _lifecycle_lock:
        state = request.app.state
        service: IndicatorTestDistributionService | None = getattr(
            state, "code_editor_test_distribution", None
        )
        if service is None:
            suite = suite_service(request)
            manager, store = _ensure_host_jobs(request)
            service = IndicatorTestDistributionService(manager, store, suite)
            state.code_editor_test_distribution = service
        return service


def calibration_service(request: Request) -> IndicatorCalibrationService:
    """Return or initialize the host-backed IndicatorCalibrationService."""
    with _lifecycle_lock:
        state = request.app.state
        service: IndicatorCalibrationService | None = getattr(
            state, "code_editor_calibration", None
        )
        if service is None:
            _, store = _ensure_host_jobs(request)
            loader = getattr(state, "code_editor_history_loader", None)
            service = IndicatorCalibrationService(store=store, history_loader=loader)
            state.code_editor_calibration = service
        return service


def import_session_service(request: Request) -> ImportSessionService:
    """Return or initialize the host-backed ImportSessionService."""
    with _lifecycle_lock:
        state = request.app.state
        service: ImportSessionService | None = getattr(
            state, "code_editor_import_sessions", None
        )
        if service is None:
            _, store = _ensure_host_jobs(request)
            service = ImportSessionService(store=store)
            state.code_editor_import_sessions = service
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

    @router.get(
        "/indicator-suite/indicators",
        response_model=SuccessEnvelope[list[SuiteIndicatorOption]],
    )
    def suite_indicators() -> SuccessEnvelope[list[SuiteIndicatorOption]]:
        logger.debug("FR-editor-command-http: suite indicators")
        return {"status": "success", "data": list_suite_indicators()}

    @router.post(
        "/indicator-suite/config/new",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_create_config(
        req: SuiteCreateConfigRequest, request: Request
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite create config")
        return {
            "status": "success",
            "data": suite_service(request).create_new_config(req),
        }

    @router.post(
        "/indicator-suite/config/add-tests",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_add_tests(
        req: SuiteAddTestsRequest, request: Request
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite add tests")
        return {
            "status": "success",
            "data": suite_service(request).add_tests(req),
        }

    @router.get(
        "/indicator-suite/config",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_get_config(request: Request) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite get config")
        return {
            "status": "success",
            "data": suite_service(request).load_config(SuiteLoadConfigRequest()),
        }

    @router.post(
        "/indicator-suite/config/load",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_load_config(
        req: SuiteLoadConfigRequest, request: Request
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite load config")
        return {
            "status": "success",
            "data": suite_service(request).load_config(req),
        }

    @router.post(
        "/indicator-suite/config/save",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_save_config(
        req: SuiteSaveConfigRequest, request: Request
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite save config")
        return {
            "status": "success",
            "data": suite_service(request).save_config(req),
        }

    @router.post(
        "/indicator-suite/start",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_start(
        req: SuiteStartRequest, request: Request
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite start")
        return {
            "status": "success",
            "data": suite_service(request).start_testing(req),
        }

    @router.post(
        "/indicator-suite/stop",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_stop(
        request: Request, job_id: str | None = None
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite stop")
        return {
            "status": "success",
            "data": suite_service(request).stop_testing(job_id),
        }

    @router.get(
        "/indicator-suite/status",
        response_model=SuccessEnvelope[SuiteSnapshot],
    )
    def suite_status(
        request: Request, job_id: str | None = None
    ) -> SuccessEnvelope[SuiteSnapshot]:
        logger.debug("FR-editor-command-http: suite status")
        return {
            "status": "success",
            "data": suite_service(request).get_snapshot(job_id),
        }

    @router.post(
        "/indicator-suite/download-tests",
        response_model=SuccessEnvelope[TestDistributionSnapshot],
    )
    def suite_download_tests(
        req: TestDistributionRequest, request: Request
    ) -> SuccessEnvelope[TestDistributionSnapshot]:
        logger.debug("FR-editor-command-http: suite download tests")
        return {
            "status": "success",
            "data": distribution_service(request).download_tests(req),
        }

    @router.get(
        "/indicator-suite/download-status",
        response_model=SuccessEnvelope[TestDistributionSnapshot],
    )
    def suite_download_status(
        request: Request, job_id: str | None = None
    ) -> SuccessEnvelope[TestDistributionSnapshot]:
        logger.debug("FR-editor-command-http: suite download status")
        return {
            "status": "success",
            "data": distribution_service(request).get_status(job_id),
        }

    @router.post(
        "/indicator-suite/calibrate",
        response_model=SuccessEnvelope[CalibrationResult],
    )
    def suite_calibrate(
        req: CalibrationRequest, request: Request
    ) -> SuccessEnvelope[CalibrationResult]:
        logger.debug("FR-editor-command-http: suite calibrate")
        return {
            "status": "success",
            "data": calibration_service(request).calibrate(req),
        }

    @router.get(
        "/import-export/list",
        response_model=SuccessEnvelope[NavigatorItem],
    )
    def import_export_list(
        filter_text: str = "",
    ) -> SuccessEnvelope[NavigatorItem]:
        logger.debug("FR-editor-command-http: import export list")
        return {
            "status": "success",
            "data": list_exportable_tree(filter_text=filter_text),
        }

    @router.post(
        "/import-export/session/start",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_start(
        req: ImportSessionStartRequest, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session start")
        return {
            "status": "success",
            "data": import_session_service(request).start_session(req),
        }

    @router.get(
        "/import-export/session",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_get(
        request: Request, session_id: str | None = None
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session get")
        return {
            "status": "success",
            "data": import_session_service(request).get_session(session_id),
        }

    @router.post(
        "/import-export/session/action",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_action(
        req: ImportSessionActionRequest, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session action")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(req),
        }

    @router.post(
        "/import-export/session/{session_id}/overwrite",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_overwrite(
        session_id: str, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session overwrite")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(
                ImportSessionActionRequest(session_id=session_id, action="overwrite")
            ),
        }

    @router.post(
        "/import-export/session/{session_id}/overwrite-always",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_overwrite_always(
        session_id: str, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session overwrite always")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(
                ImportSessionActionRequest(
                    session_id=session_id, action="overwrite_always"
                )
            ),
        }

    @router.post(
        "/import-export/session/{session_id}/skip",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_skip(
        session_id: str, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session skip")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(
                ImportSessionActionRequest(session_id=session_id, action="skip")
            ),
        }

    @router.post(
        "/import-export/session/{session_id}/skip-always",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_skip_always(
        session_id: str, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session skip always")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(
                ImportSessionActionRequest(session_id=session_id, action="skip_always")
            ),
        }

    @router.post(
        "/import-export/session/{session_id}/cancel",
        response_model=SuccessEnvelope[ImportSessionSnapshot],
    )
    def import_session_cancel(
        session_id: str, request: Request
    ) -> SuccessEnvelope[ImportSessionSnapshot]:
        logger.debug("FR-editor-command-http: import session cancel")
        return {
            "status": "success",
            "data": import_session_service(request).apply_action(
                ImportSessionActionRequest(session_id=session_id, action="cancel")
            ),
        }
