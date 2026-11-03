"""HSL workspace examples, durable file exchange, and Retester handoff.

Description: Coordinate validated examples, host storage, and compiled Retester bundles.
Purpose: FEAT-WIZARD-HSL-LANGUAGE: Consistent strategy authoring and exchange.
Key Capabilities:
    - FR-shared-hsl-execution: Log decisions and verify observable effects.
Python API Usage: Import the typed services from this module.
CLI Usage: uv run pytest tests/workspace/algo_wizard --no-cov
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path, PurePath
from typing import Any

from app.core.host.logging import get_logger
from app.core.host.strategy_storage import HostStrategyStorage
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse, build_typed_response
from app.core.trading.strategy.hsl.compiler import StrategyCompiler
from app.core.trading.strategy.hsl.documents import (
    canonical_hsl_bytes,
    compute_document_hash,
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from app.core.trading.strategy.hsl.library import WizardBlockLibrary
from app.core.trading.strategy.hsl.models import (
    HSLStrategyDocument,
)
from app.core.trading.strategy.hsl.validation import (
    StrategyValidator,
    validation_error_details,
)
from app.workspace.algo_wizard.catalogue import WizardCatalogueService
from app.workspace.algo_wizard.strategies import StrategyDocumentService
from app.workspace.algo_wizard.visual_blocks import VisualBlockService
from app.workspace.algo_wizard.workspace_models import (
    ListWizardExamplesRequest,
    LoadStrategyFileRequest,
    LoadWizardExampleRequest,
    RetesterHandoffResult,
    SavedStrategyFileResult,
    SaveStrategyFileRequest,
    SaveToRetesterRequest,
    WizardExamplePayload,
    WizardExampleSummary,
)

logger = get_logger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _build_default_examples() -> dict[str, WizardExamplePayload]:
    """Load the existing ordered example catalogue from shipped documents."""
    examples: dict[str, WizardExamplePayload] = {}
    directory = Path(__file__).with_name("examples")
    for example_id in (
        "ema_crossover",
        "rsi_mean_reversion",
        "atr_breakout",
        "mtf_trend_filter",
    ):
        item = WizardExamplePayload.model_validate_json(
            (directory / f"{example_id}.json").read_bytes()
        )
        examples[item.summary.example_id] = item
    logger.info("FR-wizard-examples-loaded: count=%s", len(examples))
    return examples


class WizardService:
    """AppWizard coordinator for examples, file exchange, and Retester handoff."""

    def __init__(
        self,
        *,
        library: WizardBlockLibrary | None = None,
        validator: StrategyValidator | None = None,
        compiler: StrategyCompiler | None = None,
        catalogue_service: WizardCatalogueService | None = None,
        strategy_service: StrategyDocumentService | None = None,
        visual_block_service: VisualBlockService | None = None,
        storage: HostStrategyStorage | None = None,
    ) -> None:
        """Initialize WizardService and its shared HSL 1.0 collaborators."""
        self._library = library if library is not None else WizardBlockLibrary()
        self._validator = validator or StrategyValidator(library=self._library)
        self._compiler = compiler or StrategyCompiler(
            library=self._library,
            validator=self._validator,
        )
        self._catalogue_service = catalogue_service or WizardCatalogueService(
            library=self._library,
        )
        self._strategy_service = strategy_service or StrategyDocumentService(
            validator=self._validator,
            compiler=self._compiler,
            storage=storage,
        )
        self._visual_block_service = visual_block_service or VisualBlockService(
            library=self._library,
            validator=self._validator,
            compiler=self._compiler,
        )
        storage_root = os.environ.get("HARU_STRATEGY_STORAGE_DIR")
        self._storage = storage or (
            HostStrategyStorage(storage_root) if storage_root else None
        )
        self._examples: dict[str, WizardExamplePayload] = _build_default_examples()
        self._files: dict[str, SavedStrategyFileResult] = {}
        if self._storage is not None:
            for key, record in self._storage.records("file:").items():
                self._files[key.removeprefix("file:")] = (
                    SavedStrategyFileResult.model_validate(record["payload"])
                )
        self._recent_files: list[str] = []
        self._retester_handoffs: dict[str, RetesterHandoffResult] = {}
        self._revision: int = 1
        logger.info(
            "FR-wizard-examples-catalog: initialized WizardService with %d examples",
            len(self._examples),
        )

    @property
    def validator(self) -> StrategyValidator:
        """Return the StrategyValidator instance."""
        return self._validator

    @property
    def compiler(self) -> StrategyCompiler:
        """Return the StrategyCompiler instance."""
        return self._compiler

    @property
    def catalogue_service(self) -> WizardCatalogueService:
        """Return the shared WizardCatalogueService instance."""
        return self._catalogue_service

    @property
    def strategy_service(self) -> StrategyDocumentService:
        """Return the shared StrategyDocumentService instance."""
        return self._strategy_service

    @property
    def visual_block_service(self) -> VisualBlockService:
        """Return the shared VisualBlockService instance."""
        return self._visual_block_service

    def list_examples(
        self,
        request: ListWizardExamplesRequest | None = None,
    ) -> StandardResponse[tuple[WizardExampleSummary, ...]]:
        """Serve /AlgoWizard/examples/examples.json catalog of HSL 1.0 templates."""
        req = request or ListWizardExamplesRequest()
        category_filter = req.category.strip().lower() if req.category else None
        query_filter = req.query.strip().lower() if req.query else None

        summaries: list[WizardExampleSummary] = []
        for payload in self._examples.values():
            summary = payload.summary
            if category_filter and summary.category.lower() != category_filter:
                continue
            if query_filter:
                haystack = " ".join(
                    (
                        summary.example_id,
                        summary.name,
                        summary.category,
                        summary.description,
                        *summary.tags,
                    )
                ).lower()
                if query_filter not in haystack:
                    continue
            summaries.append(summary)

        result = tuple(summaries)
        logger.info(
            "FR-wizard-examples-catalog: list_examples request_id=%s count=%d",
            req.request_id,
            len(result),
        )
        return build_typed_response(
            request_id=req.request_id,
            data=result,
            json_payload=[item.model_dump(mode="json") for item in result],
            revision=self._revision,
        )

    def load_example(
        self,
        request: LoadWizardExampleRequest,
    ) -> StandardResponse[WizardExamplePayload]:
        """Serve /algowizard/loadExample by returning a validated example clone."""
        normalized_id = self._normalize_example_id(request.example_id)
        payload = self._examples.get(normalized_id)
        if payload is None:
            logger.warning(
                "FR-wizard-examples-catalog: unknown example_id=%s (normalized=%s)",
                request.example_id,
                normalized_id,
            )
            raise DomainError(
                code="WIZARD_EXAMPLE_NOT_FOUND",
                message=f"Built-in wizard example '{request.example_id}' not found",
                details={"example_id": request.example_id},
            )

        cloned_doc = parse_hsl_document(canonical_hsl_bytes(payload.document))
        report = self._validator.validate(cloned_doc, raise_on_error=False)
        if not report.valid:  # pragma: no cover - defensive invariant check
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=f"Built-in example '{normalized_id}' failed HSL validation",
                details=validation_error_details(cloned_doc.strategy.id, report),
            )

        result = WizardExamplePayload(
            summary=payload.summary,
            document=cloned_doc,
        )
        logger.info(
            "FR-wizard-examples-catalog: load_example request_id=%s "
            "example_id=%s strategy_id=%s",
            request.request_id,
            normalized_id,
            cloned_doc.strategy.id,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def load_file(
        self,
        request: LoadStrategyFileRequest,
    ) -> StandardResponse[HSLStrategyDocument]:
        """Serve /algowizard/loadFile from store or inline HSL/legacy payload."""
        doc = self._resolve_file_document(request)
        report = self._validator.validate(doc, raise_on_error=False)
        if request.strict and not report.valid:
            logger.warning(
                "FR-wizard-file-exchange: load_file rejected invalid strategy_id=%s",
                doc.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Strategy '{doc.strategy.id}' failed HSL validation with "
                    f"{len(report.issues)} issue(s)"
                ),
                details=validation_error_details(doc.strategy.id, report),
            )

        if request.file_id:
            self._record_recent_file(self._sanitize_filename(request.file_id))

        logger.info(
            "FR-wizard-file-exchange: load_file request_id=%s strategy_id=%s valid=%s",
            request.request_id,
            doc.strategy.id,
            report.valid,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=doc,
            json_payload=doc.model_dump(mode="json"),
            revision=self._revision,
        )

    def save_file(
        self,
        request: SaveStrategyFileRequest,
    ) -> StandardResponse[SavedStrategyFileResult]:
        """Serve /algowizard/saveFile by validating and persisting an HSL document."""
        report = self._validator.validate(request.document, raise_on_error=False)
        if request.strict and not report.valid:
            logger.warning(
                "FR-wizard-file-exchange: save_file rejected invalid strategy_id=%s",
                request.document.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Cannot save invalid HSL strategy '{request.document.strategy.id}'"
                ),
                details=validation_error_details(
                    request.document.strategy.id,
                    report,
                ),
            )

        raw_name = request.filename or request.file_id or request.document.strategy.id
        filename = self._sanitize_filename(raw_name)
        file_id = self._sanitize_file_id(request.file_id or filename)
        if self._storage is None:
            raise DomainError(
                code="HSL_STORAGE_UNAVAILABLE",
                message="Configure host strategy storage before saving",
            )
        latest = self._storage.load("file:" + file_id)
        existing = (
            SavedStrategyFileResult.model_validate(latest["payload"])
            if latest
            else None
        )
        actual_revision = existing.revision if existing is not None else 0
        if (
            request.expected_revision is not None
            and request.expected_revision != actual_revision
        ):
            raise DomainError(
                code="WIZARD_REVISION_CONFLICT",
                message="Strategy file revision changed",
            )
        revision = actual_revision + 1
        doc_hash = compute_document_hash(request.document)
        cloned_doc = parse_hsl_document(canonical_hsl_bytes(request.document))

        recent_files = tuple(dict.fromkeys((filename, *self._recent_files)))
        saved = SavedStrategyFileResult(
            file_id=file_id,
            filename=filename,
            strategy_id=cloned_doc.strategy.id,
            revision=revision,
            document_hash=doc_hash,
            recent_files=recent_files,
            document=cloned_doc,
        )
        self._storage.save(
            "file:" + file_id,
            saved.model_dump(mode="json"),
            expected_revision=revision - 1,
        )
        self._record_recent_file(filename)
        self._revision += 1
        self._files[file_id] = saved

        logger.info(
            "FR-wizard-file-exchange: save_file request_id=%s file_id=%s "
            "filename=%s rev=%d hash=%s",
            request.request_id,
            file_id,
            filename,
            revision,
            doc_hash,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=saved,
            json_payload=saved.model_dump(mode="json"),
            revision=self._revision,
        )

    def save_to_retester(
        self,
        request: SaveToRetesterRequest,
    ) -> StandardResponse[RetesterHandoffResult]:
        """Serve /algowizard/saveToRetester by validating and compiling for Retester."""
        report = self._validator.validate(request.document, raise_on_error=False)
        if not report.valid:
            logger.warning(
                "FR-wizard-retester-handoff: rejected invalid strategy_id=%s",
                request.document.strategy.id,
            )
            raise DomainError(
                code="WIZARD_INVALID_STRATEGY",
                message=(
                    f"Cannot hand off invalid strategy "
                    f"'{request.document.strategy.id}' to Retester"
                ),
                details=validation_error_details(
                    request.document.strategy.id,
                    report,
                ),
            )

        compiled = self._compiler.compile_to_runtime(request.document)
        doc_hash = compute_document_hash(request.document)
        cloned_doc = parse_hsl_document(canonical_hsl_bytes(request.document))
        handoff_id = (
            f"retester-{cloned_doc.strategy.id}-{len(self._retester_handoffs) + 1}"
        )
        result = RetesterHandoffResult(
            handoff_id=handoff_id,
            retester_project_name=request.retester_project_name,
            strategy_id=cloned_doc.strategy.id,
            document_hash=doc_hash,
            document=cloned_doc,
            compiled_document=compiled,
        )
        self._retester_handoffs[handoff_id] = result
        self._revision += 1

        logger.info(
            "FR-wizard-retester-handoff: save_to_retester request_id=%s "
            "handoff_id=%s strategy_id=%s project=%s",
            request.request_id,
            handoff_id,
            cloned_doc.strategy.id,
            request.retester_project_name,
        )
        return build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=self._revision,
        )

    def get_saved_file(self, file_id: str) -> SavedStrategyFileResult | None:
        """Look up a previously saved strategy file by file_id or filename."""
        normalized = self._sanitize_file_id(file_id)
        if self._storage is not None:
            record = self._storage.load("file:" + normalized)
            if record is not None:
                saved = SavedStrategyFileResult.model_validate(record["payload"])
                self._files[normalized] = saved
                return saved
            return None
        return self._files.get(normalized)

    def list_saved_files(self) -> tuple[SavedStrategyFileResult, ...]:
        """Return all saved strategy file records in insertion order."""
        return tuple(self._files.values())

    def list_retester_handoffs(self) -> tuple[RetesterHandoffResult, ...]:
        """Return all recorded Retester handoff bundles."""
        return tuple(self._retester_handoffs.values())

    def _resolve_file_document(
        self,
        request: LoadStrategyFileRequest,
    ) -> HSLStrategyDocument:
        """Resolve an HSLStrategyDocument from saved file_id or inline payload."""
        if request.payload is not None:
            return self._parse_payload(request.payload)

        file_id = request.file_id or ""
        saved = self.get_saved_file(file_id)
        if saved is None:
            logger.warning(
                "FR-wizard-file-exchange: file_id=%s not found in workspace store",
                file_id,
            )
            raise DomainError(
                code="WIZARD_FILE_NOT_FOUND",
                message=f"Saved strategy file '{file_id}' not found",
                details={"file_id": file_id},
            )
        return parse_hsl_document(canonical_hsl_bytes(saved.document))

    def _parse_payload(
        self,
        payload: dict[str, Any] | str,
    ) -> HSLStrategyDocument:
        """Parse an inline JSON string or dictionary as HSL 1.0 or legacy wizard."""
        raw_dict: dict[str, Any]
        if isinstance(payload, str):
            try:
                loaded = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message=f"Strategy file payload is not valid JSON: {exc.msg}",
                    details={"pos": exc.pos},
                ) from exc
            if not isinstance(loaded, dict):
                raise DomainError(
                    code="WIZARD_INVALID_JSON",
                    message="Strategy file JSON root must be an object",
                )
            raw_dict = loaded
        else:
            raw_dict = dict(payload)

        if "schema_version" in raw_dict and isinstance(raw_dict.get("strategy"), dict):
            return parse_hsl_document(raw_dict)
        return upgrade_legacy_wizard_document(raw_dict)

    @staticmethod
    def _normalize_example_id(raw_id: str) -> str:
        """Normalize an example identifier or filename into a catalog key."""
        leaf = PurePath(raw_id.strip().replace("\\", "/")).name
        for ext in (".json", ".sqx", ".sqw", ".str", ".sq4"):
            if leaf.lower().endswith(ext):
                leaf = leaf[: -len(ext)]
                break
        return re.sub(r"[\s\-]+", "_", leaf.strip().lower())

    @staticmethod
    def _sanitize_filename(raw_name: str) -> str:
        """Sanitize a user-provided filename into a safe `<stem>.json` name."""
        leaf = PurePath(raw_name.strip().replace("\\", "/")).name
        for ext in (".json", ".sqx", ".sqw", ".str", ".sq4"):
            if leaf.lower().endswith(ext):
                leaf = leaf[: -len(ext)]
                break
        cleaned = _SAFE_FILENAME_RE.sub("_", leaf).strip("._-")
        if not cleaned:
            cleaned = "strategy"
        return f"{cleaned}.json"

    @classmethod
    def _sanitize_file_id(cls, raw_id: str) -> str:
        """Sanitize a file identifier into its canonical stem."""
        filename = cls._sanitize_filename(raw_id)
        return filename[: -len(".json")]

    def _record_recent_file(self, filename: str) -> None:
        """Record a filename at the front of the MRU list."""
        if filename in self._recent_files:
            self._recent_files.remove(filename)
        self._recent_files.insert(0, filename)
        del self._recent_files[20:]


__all__ = [
    "WizardService",
]
