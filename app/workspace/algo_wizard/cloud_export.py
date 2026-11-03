"""ServletAlgoCloud strategy import and multi-target export service.

Description:
    Implements CloudExportService (ServletAlgoCloud equivalent), supporting
    strategy import from the visual editor, saved workspace files, databanks,
    and backtest results (/algocloud/import), export target platform discovery
    (/algocloud/targets), and multi-platform source code generation from the
    canonical HSL 1.0 AST (/algocloud/export) across Python, MQL4, MQL5,
    EasyLanguage, NinjaTrader, JForex, Pseudocode, and canonical HSL JSON.

Purpose:
    FEAT-WIZARD-CLOUD-EXPORT: Gate G8 (Phase 5.8, WO-WZ-CLOUD-EXPORT /
    I-ServletAlgoCloud) service for HSL 1.0 strategy import and multi-target
    code generation.

Key Capabilities:
    - FR-wizard-cloud-import: Resolves strategies from editor, file, databank,
      or backtest_id, upgrades legacy payloads to canonical HSL 1.0, and runs
      3-pass StrategyValidator checks.
    - FR-wizard-cloud-export-targets: Publishes metadata and file extensions for
      all 8 supported export target platforms.
    - FR-wizard-cloud-export-code: Compiles validated HSL 1.0 documents to
      NormalizedStrategy and renders deterministic source code with SHA-256
      content digests.

Python API Usage:
    from app.workspace.algo_wizard.cloud_export import CloudExportService
    from app.workspace.algo_wizard.cloud_export_models import ExportStrategyRequest

    service = CloudExportService()
    res = service.export_strategy(
        ExportStrategyRequest(document=hsl_doc, target_platform="python")
    )

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_cloud_export.py --no-cov -q
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue
from app.core.lib.responses import StandardResponse
from app.core.wizard.template_helpers import render_jinja_template
from app.core.wizard.transform import PYTHON_TEMPLATE
from app.extend.code.easylanguage.descriptor import render_easylanguage
from app.extend.code.jforex.descriptor import render_jforex
from app.extend.code.mql4.descriptor import render_mql4
from app.extend.code.mql5.descriptor import render_mql5
from app.extend.code.ninjatrader.descriptor import render_ninjatrader
from app.extend.code.pseudo_code.descriptor import render_pseudo_code
from app.workspace.algo_wizard.cloud_export_models import (
    CloudImportRequest,
    CloudImportResult,
    ExportStrategyRequest,
    ExportStrategyResult,
    ExportTargetDescriptor,
    ExportTargetPlatform,
    ListExportTargetsRequest,
)
from app.workspace.algo_wizard.compiler import StrategyCompiler
from app.workspace.algo_wizard.documents import (
    canonical_hsl_bytes,
    compute_document_hash,
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from app.workspace.algo_wizard.library import WizardBlockLibrary
from app.workspace.algo_wizard.models import HSLStrategyDocument
from app.workspace.algo_wizard.strategies import StrategyDocumentService
from app.workspace.algo_wizard.strategies_models import StrategyIdRequest
from app.workspace.algo_wizard.validation import StrategyValidator, ValidationReport
from app.workspace.algo_wizard.workspace import WizardService

logger = get_logger(__name__)

_SAFE_STEM_RE = re.compile(r"[^A-Za-z0-9_-]+")

_EXPORT_TARGETS: tuple[ExportTargetDescriptor, ...] = (
    ExportTargetDescriptor(
        platform="python",
        supported_for_hsl=True,
        name="HaruQuant Python Strategy",
        extension=".py",
        language="Python",
        description="Executable Python strategy class for HaruQuant runtime.",
    ),
    ExportTargetDescriptor(
        platform="mql4",
        name="MetaTrader 4 Expert Advisor (MQL4)",
        extension=".mq4",
        language="MQL4",
        description="MetaTrader 4 Expert Advisor source file (.mq4).",
    ),
    ExportTargetDescriptor(
        platform="mql5",
        name="MetaTrader 5 Expert Advisor (MQL5)",
        extension=".mq5",
        language="MQL5",
        description="MetaTrader 5 Expert Advisor source file (.mq5).",
    ),
    ExportTargetDescriptor(
        platform="easylanguage",
        name="TradeStation / MultiCharts EasyLanguage",
        extension=".eld",
        language="EasyLanguage",
        description="TradeStation and MultiCharts EasyLanguage strategy script.",
    ),
    ExportTargetDescriptor(
        platform="ninjatrader",
        name="NinjaTrader 8 NinjaScript (C#)",
        extension=".cs",
        language="C#",
        description="NinjaTrader 8 C# NinjaScript strategy class.",
    ),
    ExportTargetDescriptor(
        platform="jforex",
        name="Dukascopy JForex Strategy (Java)",
        extension=".java",
        language="Java",
        description="Dukascopy JForex IStrategy Java implementation.",
    ),
    ExportTargetDescriptor(
        platform="pseudo_code",
        supported_for_hsl=True,
        name="Human-Readable Strategy Pseudocode",
        extension=".txt",
        language="Pseudocode",
        description="Structured English description of parameters and rules.",
    ),
    ExportTargetDescriptor(
        platform="hsl_json",
        supported_for_hsl=True,
        name="HaruQuant Strategy Language (HSL 1.0 JSON)",
        extension=".json",
        language="JSON",
        description="Canonical pretty-printed HSL 1.0 strategy AST document.",
    ),
)

_TARGET_BY_PLATFORM: dict[ExportTargetPlatform, ExportTargetDescriptor] = {
    item.platform: item for item in _EXPORT_TARGETS
}


def _build_typed_response[T](
    *,
    request_id: str,
    data: T,
    json_payload: Any,
    revision: int,
) -> StandardResponse[T]:
    """Validate json_payload through StandardResponse and attach typed data."""
    envelope: StandardResponse[Any] = StandardResponse(
        request_id=request_id,
        data=json_payload,
        revision=revision,
    )
    object.__setattr__(envelope, "data", data)
    return cast("StandardResponse[T]", envelope)


def _validation_error_details(
    strategy_id: str,
    report: ValidationReport,
) -> dict[str, JSONValue]:
    """Format ValidationReport issues as finite JSON error details."""
    issues_json: list[JSONValue] = [
        {
            "code": issue.code,
            "message": issue.message,
            "path": issue.path,
            "node_id": issue.node_id,
        }
        for issue in report.issues
    ]
    return {
        "strategy_id": strategy_id,
        "issue_count": len(report.issues),
        "issues": issues_json,
    }


class CloudExportService:
    """ServletAlgoCloud service for HSL strategy import and multi-target export."""

    def __init__(
        self,
        *,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
        compiler: StrategyCompiler | None = None,
        wizard_service: WizardService | None = None,
        strategy_service: StrategyDocumentService | None = None,
    ) -> None:
        """Initialize CloudExportService and its shared HSL 1.0 collaborators."""
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)
        self._compiler = compiler or StrategyCompiler(
            library=self._library,
            validator=self._validator,
        )
        self._wizard_service = wizard_service or WizardService(
            library=self._library,
            validator=self._validator,
            compiler=self._compiler,
            strategy_service=strategy_service,
        )
        self._strategy_service = (
            strategy_service or self._wizard_service.strategy_service
        )
        self._databank_strategies: dict[tuple[str, str], HSLStrategyDocument] = {}
        self._backtest_strategies: dict[str, HSLStrategyDocument] = {}
        self._revision: int = 1
        logger.info(
            "FR-wizard-cloud-export-targets: initialized CloudExportService "
            "with %d export targets",
            len(_EXPORT_TARGETS),
        )

    def register_databank_strategy(
        self,
        databank_name: str,
        strategy_name: str,
        document: HSLStrategyDocument,
    ) -> None:
        """Register an HSLStrategyDocument in a named databank for cloud import."""
        key = (databank_name.strip().lower(), strategy_name.strip())
        self._databank_strategies[key] = parse_hsl_document(
            canonical_hsl_bytes(document)
        )

    def register_backtest_strategy(
        self,
        backtest_id: str,
        document: HSLStrategyDocument,
    ) -> None:
        """Associate a completed backtest_id with its HSLStrategyDocument."""
        self._backtest_strategies[backtest_id.strip()] = parse_hsl_document(
            canonical_hsl_bytes(document)
        )

    def list_export_targets(
        self,
        request: ListExportTargetsRequest | None = None,
    ) -> StandardResponse[tuple[ExportTargetDescriptor, ...]]:
        """Return metadata and file extensions for all supported export platforms."""
        req = request or ListExportTargetsRequest()
        logger.info(
            "FR-wizard-cloud-export-targets: list_export_targets "
            "request_id=%s count=%d",
            req.request_id,
            len(_EXPORT_TARGETS),
        )
        return _build_typed_response(
            request_id=req.request_id,
            data=_EXPORT_TARGETS,
            json_payload=[item.model_dump(mode="json") for item in _EXPORT_TARGETS],
            revision=self._revision,
        )

    def import_strategy(
        self,
        request: CloudImportRequest,
    ) -> StandardResponse[CloudImportResult]:
        """Implement /algocloud/import from editor, file, databank, or backtest_id."""
        doc = self._resolve_import_source(request)
        report = self._validator.validate(doc, raise_on_error=False)
        if request.strict and not report.valid:
            logger.warning(
                "FR-wizard-cloud-import: strict import rejected invalid strategy_id=%s",
                doc.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Imported strategy '{doc.strategy.id}' failed HSL validation "
                    f"with {len(report.issues)} issue(s)"
                ),
                details=_validation_error_details(doc.strategy.id, report),
            )

        doc_hash = compute_document_hash(doc)
        result = CloudImportResult(
            source=request.source,
            strategy_id=doc.strategy.id,
            document_hash=doc_hash,
            document=doc,
            validation=report,
        )
        self._revision += 1
        logger.info(
            "FR-wizard-cloud-import: import_strategy request_id=%s "
            "source=%s strategy_id=%s valid=%s",
            request.request_id,
            request.source,
            doc.strategy.id,
            report.valid,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def export_strategy(
        self,
        request: ExportStrategyRequest,
    ) -> StandardResponse[ExportStrategyResult]:
        """Validate, normalize, and render an HSL 1.0 strategy for a target platform."""
        report = self._validator.validate(request.document, raise_on_error=False)
        if not report.valid:
            logger.warning(
                "FR-wizard-cloud-export-code: export rejected invalid strategy_id=%s",
                request.document.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Cannot export invalid strategy '{request.document.strategy.id}'"
                ),
                details=_validation_error_details(
                    request.document.strategy.id,
                    report,
                ),
            )

        descriptor = _TARGET_BY_PLATFORM[request.target_platform]
        content = self._render_target_content(
            request.document,
            request.target_platform,
        )
        stem = _SAFE_STEM_RE.sub("_", request.document.strategy.id).strip("_")
        if not stem:
            stem = "strategy"
        filename = f"{stem}{descriptor.extension}"
        sha256_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()

        result = ExportStrategyResult(
            strategy_id=request.document.strategy.id,
            target_platform=request.target_platform,
            filename=filename,
            content=content,
            sha256=sha256_hex,
        )
        self._revision += 1
        logger.info(
            "FR-wizard-cloud-export-code: export_strategy request_id=%s "
            "strategy_id=%s platform=%s filename=%s sha256=%s",
            request.request_id,
            request.document.strategy.id,
            request.target_platform,
            filename,
            sha256_hex,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def _resolve_import_source(
        self,
        request: CloudImportRequest,
    ) -> HSLStrategyDocument:
        """Resolve and normalize an HSLStrategyDocument from the requested source."""
        if request.source == "editor":
            return self._resolve_editor_source(request.document)
        if request.source == "file":
            return self._resolve_file_source(request.file_id)
        if request.source == "databank":
            return self._resolve_databank_source(
                request.databank_name,
                request.strategy_name,
            )
        return self._resolve_backtest_source(request.backtest_id)

    def _resolve_editor_source(
        self,
        raw: HSLStrategyDocument | dict[str, Any] | str | None,
    ) -> HSLStrategyDocument:
        """Parse an inline editor HSL document, dictionary, or JSON string."""
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message="Editor import requires a non-empty strategy document payload",
                details={"source": "editor"},
            )
        if isinstance(raw, HSLStrategyDocument):
            return parse_hsl_document(canonical_hsl_bytes(raw))
        if isinstance(raw, str):
            try:
                loaded = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message=f"Editor import JSON is invalid: {exc.msg}",
                    details={"pos": exc.pos},
                ) from exc
            if not isinstance(loaded, dict):
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message="Editor import JSON root must be an object",
                )
            raw = loaded
        if "schema_version" in raw and isinstance(raw.get("strategy"), dict):
            return parse_hsl_document(raw)
        return upgrade_legacy_wizard_document(raw)

    def _resolve_file_source(self, file_id: str | None) -> HSLStrategyDocument:
        """Resolve a saved strategy document from WizardService by file_id."""
        if not file_id or not file_id.strip():
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message="File import requires a non-empty file_id",
                details={"source": "file"},
            )
        saved = self._wizard_service.get_saved_file(file_id)
        if saved is None:
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message=f"Saved strategy file '{file_id}' was not found",
                details={"source": "file", "file_id": file_id},
            )
        return parse_hsl_document(canonical_hsl_bytes(saved.document))

    def _resolve_databank_source(
        self,
        databank_name: str | None,
        strategy_name: str | None,
    ) -> HSLStrategyDocument:
        """Resolve a strategy from the databank registry or StrategyDocumentService."""
        if not strategy_name or not strategy_name.strip():
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message="Databank import requires strategy_name",
                details={"source": "databank"},
            )
        db_key = (databank_name or "default").strip().lower()
        strat_key = strategy_name.strip()
        registered = self._databank_strategies.get((db_key, strat_key))
        if registered is not None:
            return parse_hsl_document(canonical_hsl_bytes(registered))

        try:
            managed = self._strategy_service.get_strategy(
                StrategyIdRequest(strategy_id=strat_key)
            )
            return parse_hsl_document(canonical_hsl_bytes(managed.data.document))
        except DomainError as exc:
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message=(
                    f"Strategy '{strat_key}' not found in databank "
                    f"'{databank_name or 'default'}'"
                ),
                details={
                    "source": "databank",
                    "databank_name": databank_name or "default",
                    "strategy_name": strat_key,
                },
            ) from exc

    def _resolve_backtest_source(self, backtest_id: str | None) -> HSLStrategyDocument:
        """Resolve a strategy document associated with a completed backtest_id."""
        if not backtest_id or not backtest_id.strip():
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message="Backtest import requires backtest_id",
                details={"source": "backtest_id"},
            )
        bt_key = backtest_id.strip()
        doc = self._backtest_strategies.get(bt_key)
        if doc is None:
            raise DomainError(
                code="WIZARD_IMPORT_SOURCE_NOT_FOUND",
                message=f"No strategy document found for backtest_id '{bt_key}'",
                details={"source": "backtest_id", "backtest_id": bt_key},
            )
        return parse_hsl_document(canonical_hsl_bytes(doc))

    def _render_target_content(
        self,
        document: HSLStrategyDocument,
        target_platform: ExportTargetPlatform,
    ) -> str:
        """Render target platform code or JSON from a validated HSLStrategyDocument."""
        if target_platform == "hsl_json":
            return (
                json.dumps(
                    document.model_dump(mode="json"),
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )

        if target_platform not in ("python", "pseudo_code"):
            raise DomainError(
                code="HSL_EXPORT_UNSUPPORTED",
                message=f"Target '{target_platform}' has no qualified HSL mapping",
            )
        norm_strategy = self._compiler.compile_to_normalized(document)
        renderers = {
            "python": lambda: render_jinja_template(PYTHON_TEMPLATE, norm_strategy),
            "mql4": lambda: render_mql4(norm_strategy),
            "mql5": lambda: render_mql5(norm_strategy),
            "easylanguage": lambda: render_easylanguage(norm_strategy),
            "ninjatrader": lambda: render_ninjatrader(norm_strategy),
            "jforex": lambda: render_jforex(norm_strategy),
        }
        if target_platform in renderers:
            return renderers[target_platform]()
        strat = document.strategy
        return render_pseudo_code(
            norm_strategy,
            display_name=strat.name,
            schema_version=document.schema_version,
            symbols=strat.universe.symbols,
            primary_timeframe=strat.timeframe.primary,
            additional_timeframes=strat.timeframe.additional,
            description=strat.description,
        )


__all__ = [
    "CloudExportService",
]
