"""ServletStrategy equivalent service (StrategyDocumentService) for AlgoWizard.

Description:
    Implements persistent in-memory HSL 1.0 strategy document CRUD, optimistic
    revision concurrency control, 3-pass validation gating, runtime compilation
    via StrategyCompiler, and trading setup lifecycle management (add, get, list,
    start, stop, remove) wrapped in canonical StandardResponse[T] envelopes.

Purpose:
    FEAT-WIZARD-STRATEGY-LIFECYCLE: Gate G5 (Phase 5.5, WO-WZ-STRATEGY-LIFECYCLE /
    I-ServletStrategy) backend service managing HSL strategy documents and
    StrategyRuntime execution state transitions.

Key Capabilities:
    - FR-wizard-strategy-crud: Manages HSLStrategyDocument registration, lookup,
      deterministic listing by strategy_id, and removal with structured logging.
    - FR-wizard-strategy-optimistic-revision: Enforces expected_revision checks
      on strategy writes, raising WIZARD_REVISION_CONFLICT on stale updates.
    - FR-wizard-strategy-runtime-lifecycle: Validates and compiles HSL documents
      to Core StrategyDocument plans on start_strategy (RUNNING) and transitions
      cleanly through STOPPED, IDLE, and ERROR states.

Python API Usage:
    from app.workspace.algo_wizard.strategies import StrategyDocumentService
    from app.workspace.algo_wizard.strategies_models import AddStrategyRequest

    svc = StrategyDocumentService()
    resp = svc.add_strategy(AddStrategyRequest(request_id="r1", document=hsl_doc))

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_strategies.py --no-cov -q
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, cast

from app.core.host.logging import get_logger
from app.core.host.strategy_storage import HostStrategyStorage
from app.core.lib.errors import DomainError, JSONValue
from app.core.lib.responses import StandardResponse
from app.core.trading.strategy.contracts import StrategyDocument
from app.core.trading.strategy.runtime import StrategyRuntime
from app.workspace.algo_wizard.compiler import StrategyCompiler
from app.workspace.algo_wizard.documents import (
    compute_document_hash,
    parse_hsl_document,
    upgrade_legacy_wizard_document,
)
from app.workspace.algo_wizard.models import HSLStrategyDocument
from app.workspace.algo_wizard.strategies_models import (
    AddStrategyRequest,
    ListStrategiesRequest,
    ManagedStrategyRecord,
    RemoveStrategyRequest,
    RemoveStrategyResult,
    StartStrategyRequest,
    StopStrategyRequest,
    StrategyIdRequest,
    StrategyRuntimeStatus,
)
from app.workspace.algo_wizard.validation import StrategyValidator, ValidationReport

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    """Return current UTC timestamp formatted as ISO-8601 with Z suffix."""
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    strategy_id: str, report: ValidationReport
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


class StrategyDocumentService:
    """Service managing HSL 1.0 strategy documents and runtime lifecycle."""

    def __init__(
        self,
        *,
        validator: StrategyValidator | None = None,
        compiler: StrategyCompiler | None = None,
        runtime: StrategyRuntime | None = None,
        storage: HostStrategyStorage | None = None,
    ) -> None:
        self._compiler = compiler if compiler is not None else StrategyCompiler()
        self._validator = (
            validator if validator is not None else self._compiler.validator
        )
        self._runtime = runtime if runtime is not None else StrategyRuntime()
        storage_root = os.environ.get("HARU_STRATEGY_STORAGE_DIR")
        self._storage = storage or (
            HostStrategyStorage(storage_root) if storage_root else None
        )
        self._records: dict[str, ManagedStrategyRecord] = {}
        self._compiled_plans: dict[str, StrategyDocument] = {}
        if self._storage is not None:
            for key, stored in self._storage.records("strategy:").items():
                if not stored["payload"].get("removed", False):
                    restored = ManagedStrategyRecord.model_validate(stored["payload"])
                    if restored.status == "RUNNING":
                        restored = restored.model_copy(update={"status": "IDLE"})
                    self._records[key.removeprefix("strategy:")] = restored

    def _persist(self, record: ManagedStrategyRecord, *, actual_revision: int) -> None:
        """Publish the record durably before acknowledging a state transition."""
        if self._storage is None:
            raise DomainError(
                code="HSL_STORAGE_UNAVAILABLE",
                message="Configure host strategy storage before saving",
            )
        self._storage.save(
            "strategy:" + record.strategy_id,
            record.model_dump(mode="json"),
            expected_revision=actual_revision,
        )

    @property
    def validator(self) -> StrategyValidator:
        """Return the active StrategyValidator."""
        return self._validator

    @property
    def compiler(self) -> StrategyCompiler:
        """Return the active StrategyCompiler."""
        return self._compiler

    @property
    def runtime(self) -> StrategyRuntime:
        """Return the active StrategyRuntime."""
        return self._runtime

    @staticmethod
    def _coerce_hsl_document(
        raw: HSLStrategyDocument | Mapping[str, Any],
    ) -> HSLStrategyDocument:
        if isinstance(raw, HSLStrategyDocument):
            return raw
        if "schema_version" in raw and "strategy" in raw:
            return parse_hsl_document(raw)
        return upgrade_legacy_wizard_document(raw)

    def _require_record(self, strategy_id: str) -> ManagedStrategyRecord:
        record = self._records.get(strategy_id)
        if record is None:
            logger.warning(
                "FR-wizard-strategy-crud: Strategy '%s' not found",
                strategy_id,
            )
            raise DomainError(
                code="WIZARD_STRATEGY_NOT_FOUND",
                message=f"Strategy '{strategy_id}' does not exist.",
                details={"strategy_id": strategy_id},
            )
        return record

    def _check_expected_revision(
        self,
        strategy_id: str,
        expected_revision: int | None,
        existing: ManagedStrategyRecord | None,
    ) -> int:
        actual_revision = existing.revision if existing is not None else 0
        if expected_revision is not None and expected_revision != actual_revision:
            logger.warning(
                "FR-wizard-strategy-optimistic-revision: Revision conflict on '%s' "
                "(expected=%d, actual=%d)",
                strategy_id,
                expected_revision,
                actual_revision,
            )
            raise DomainError(
                code="WIZARD_REVISION_CONFLICT",
                message=(
                    f"Optimistic revision conflict for strategy '{strategy_id}': "
                    f"expected {expected_revision}, actual {actual_revision}."
                ),
                details={
                    "strategy_id": strategy_id,
                    "expected_revision": expected_revision,
                    "actual_revision": actual_revision,
                },
            )
        return actual_revision + 1

    def add_strategy(
        self, request: AddStrategyRequest
    ) -> StandardResponse[ManagedStrategyRecord]:
        """Add or update an HSLStrategyDocument with validation and revision control."""
        doc = self._coerce_hsl_document(request.document)
        strat = doc.strategy
        strategy_id = strat.id
        existing = self._records.get(strategy_id)
        next_revision = self._check_expected_revision(
            strategy_id, request.expected_revision, existing
        )
        report = self._validator.validate(doc, raise_on_error=False)
        if request.strict and not report.valid:
            first_msg = (
                report.issues[0].message if report.issues else "Validation failed"
            )
            logger.warning(
                "FR-wizard-strategy-crud: Rejected invalid strategy '%s' (%d issues)",
                strategy_id,
                len(report.issues),
            )
            raise DomainError(
                code="WIZARD_STRATEGY_INVALID",
                message=f"Strategy '{strategy_id}' is invalid: {first_msg}",
                details=_validation_error_details(strategy_id, report),
            )

        status: StrategyRuntimeStatus = "IDLE" if report.valid else "ERROR"
        if not report.valid:
            self._compiled_plans.pop(strategy_id, None)
        elif existing is not None and existing.status == "RUNNING":
            self._compiled_plans[strategy_id] = self._compiler.compile_to_runtime(doc)
            status = "RUNNING"

        doc_hash = compute_document_hash(doc)
        primary_symbol = (
            strat.universe.symbols[0] if strat.universe.symbols else "EURUSD"
        )
        record = ManagedStrategyRecord(
            strategy_id=strategy_id,
            name=strat.name,
            status=status,
            revision=next_revision,
            document_hash=doc_hash,
            document=doc,
            validation=report,
            updated_at=_utc_now_iso(),
            connection_name=request.connection_name,
            symbol=primary_symbol,
            timeframe=strat.timeframe.primary,
        )
        self._persist(record, actual_revision=next_revision - 1)
        self._records[strategy_id] = record
        logger.info(
            "FR-wizard-strategy-crud: Stored strategy '%s' rev=%d status=%s hash=%s",
            strategy_id,
            next_revision,
            status,
            doc_hash[:12],
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=record,
            json_payload=record.model_dump(mode="json"),
            revision=next_revision,
        )

    def get_strategy(
        self, request: StrategyIdRequest
    ) -> StandardResponse[ManagedStrategyRecord]:
        """Return a managed strategy record by ID or raise WIZARD_STRATEGY_NOT_FOUND."""
        record = self._require_record(request.strategy_id)
        logger.info(
            "FR-wizard-strategy-crud: Retrieved strategy '%s' rev=%d status=%s",
            record.strategy_id,
            record.revision,
            record.status,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=record,
            json_payload=record.model_dump(mode="json"),
            revision=record.revision,
        )

    def list_strategies(
        self, request: ListStrategiesRequest | None = None
    ) -> StandardResponse[tuple[ManagedStrategyRecord, ...]]:
        """Return all registered strategies ordered deterministically by strategy_id."""
        req = request if request is not None else ListStrategiesRequest()
        items = [
            rec
            for _, rec in sorted(self._records.items(), key=lambda kv: kv[0])
            if req.status is None or rec.status == req.status
        ]
        result = tuple(items)
        max_rev = max((r.revision for r in result), default=1)
        logger.info(
            "FR-wizard-strategy-crud: Listed %d strategies (status_filter=%s)",
            len(result),
            req.status,
        )
        return _build_typed_response(
            request_id=req.request_id,
            data=result,
            json_payload=[r.model_dump(mode="json") for r in result],
            revision=max_rev,
        )

    def start_strategy(
        self, request: StartStrategyRequest
    ) -> StandardResponse[ManagedStrategyRecord]:
        """Validate, compile, and transition a strategy to RUNNING."""
        record = self._require_record(request.strategy_id)
        report = self._validator.validate(record.document, raise_on_error=False)
        if not report.valid:
            err_rev = record.revision + 1
            err_record = record.model_copy(
                update={
                    "status": "ERROR",
                    "revision": err_rev,
                    "validation": report,
                    "updated_at": _utc_now_iso(),
                }
            )
            self._records[record.strategy_id] = err_record
            self._compiled_plans.pop(record.strategy_id, None)
            first_msg = (
                report.issues[0].message if report.issues else "Validation failed"
            )
            logger.warning(
                "FR-wizard-strategy-runtime-lifecycle: Cannot start invalid "
                "strategy '%s' (%d issues)",
                record.strategy_id,
                len(report.issues),
            )
            raise DomainError(
                code="WIZARD_STRATEGY_INVALID",
                message=(
                    f"Cannot start invalid strategy '{record.strategy_id}': {first_msg}"
                ),
                details=_validation_error_details(record.strategy_id, report),
            )

        compiled_doc = self._compiler.compile_to_runtime(record.document)
        self._compiled_plans[record.strategy_id] = compiled_doc
        next_rev = record.revision + 1
        updated = record.model_copy(
            update={
                "status": "RUNNING",
                "revision": next_rev,
                "validation": report,
                "updated_at": _utc_now_iso(),
            }
        )
        self._persist(updated, actual_revision=record.revision)
        self._records[record.strategy_id] = updated
        logger.info(
            "FR-wizard-strategy-runtime-lifecycle: Started strategy '%s' rev=%d "
            "(rules=%d)",
            record.strategy_id,
            next_rev,
            len(compiled_doc.rules),
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=updated,
            json_payload=updated.model_dump(mode="json"),
            revision=next_rev,
        )

    def stop_strategy(
        self, request: StopStrategyRequest
    ) -> StandardResponse[ManagedStrategyRecord]:
        """Stop active execution of a strategy and transition status to STOPPED."""
        record = self._require_record(request.strategy_id)
        self._compiled_plans.pop(record.strategy_id, None)
        next_rev = record.revision + 1
        updated = record.model_copy(
            update={
                "status": "STOPPED",
                "revision": next_rev,
                "updated_at": _utc_now_iso(),
            }
        )
        self._persist(updated, actual_revision=record.revision)
        self._records[record.strategy_id] = updated
        logger.info(
            "FR-wizard-strategy-runtime-lifecycle: Stopped strategy '%s' rev=%d",
            record.strategy_id,
            next_rev,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=updated,
            json_payload=updated.model_dump(mode="json"),
            revision=next_rev,
        )

    def remove_strategy(
        self, request: RemoveStrategyRequest
    ) -> StandardResponse[RemoveStrategyResult]:
        """Stop if running and remove a strategy record from the service."""
        record = self._require_record(request.strategy_id)
        self._compiled_plans.pop(record.strategy_id, None)
        if self._storage is not None:
            self._storage.save(
                "strategy:" + record.strategy_id,
                {"removed": True},
                expected_revision=record.revision,
            )
        del self._records[record.strategy_id]
        result = RemoveStrategyResult(
            strategy_id=record.strategy_id,
            removed=True,
            previous_status=record.status,
            final_revision=record.revision,
        )
        logger.info(
            "FR-wizard-strategy-runtime-lifecycle: Removed strategy '%s' "
            "(previous_status=%s, final_revision=%d)",
            record.strategy_id,
            record.status,
            record.revision,
        )
        return _build_typed_response(
            request_id=request.request_id,
            data=result,
            json_payload=result.model_dump(mode="json"),
            revision=record.revision,
        )

    def get_compiled_runtime_document(self, strategy_id: str) -> StrategyDocument:
        """Return the compiled Core StrategyDocument for a registered strategy."""
        record = self._require_record(strategy_id)
        cached = self._compiled_plans.get(strategy_id)
        if cached is not None:
            return cached
        compiled = self._compiler.compile_to_runtime(record.document)
        self._compiled_plans[strategy_id] = compiled
        return compiled


__all__ = ["StrategyDocumentService"]
