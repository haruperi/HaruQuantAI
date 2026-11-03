"""Pydantic data contracts for ServletAlgoCloud (CloudExportService).

Description:
    Defines the Pydantic v2 models for CloudExportService (ServletAlgoCloud
    equivalent), covering strategy import from editor, saved workspace files,
    databanks, and backtest results (/algocloud/import), export target platform
    descriptors (/algocloud/targets), and multi-target strategy code generation
    (/algocloud/export).

Purpose:
    FEAT-WIZARD-CLOUD-EXPORT: Gate G8 (Phase 5.8, WO-WZ-CLOUD-EXPORT /
    I-ServletAlgoCloud) data contracts for HSL 1.0 strategy import and
    multi-platform code export.

Key Capabilities:
    - FR-wizard-cloud-export-models: Defines CloudImportSource,
      ExportTargetPlatform, ExportTargetDescriptor, CloudImportResult, and
      ExportStrategyResult with strict schema validation and structured logging.
    - FR-wizard-cloud-export-requests: Defines ListExportTargetsRequest,
      CloudImportRequest, and ExportStrategyRequest.

Python API Usage:
    from app.workspace.algo_wizard.cloud_export_models import ExportStrategyRequest

    req = ExportStrategyRequest(document=hsl_doc, target_platform="python")

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_cloud_export.py --no-cov -q
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.core.trading.strategy.hsl.validation import ValidationReport

logger = get_logger(__name__)

CloudImportSource = Literal["editor", "file", "databank", "backtest_id"]

ExportTargetPlatform = Literal[
    "python",
    "mql4",
    "mql5",
    "easylanguage",
    "ninjatrader",
    "jforex",
    "pseudo_code",
    "hsl_json",
]


class ExportTargetDescriptor(BaseModel):
    """Metadata descriptor for a supported strategy code export target platform."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    supported_for_hsl: bool = False

    platform: ExportTargetPlatform = Field(
        ...,
        description="Canonical export target platform identifier",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable platform display name",
    )
    extension: str = Field(
        ...,
        min_length=2,
        description="Target source file extension including leading dot",
    )
    language: str = Field(
        ...,
        min_length=1,
        description="Programming or specification language name",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Summary of the generated strategy target format",
    )

    @model_validator(mode="after")
    def _log_descriptor(self) -> ExportTargetDescriptor:
        logger.debug(
            "FR-wizard-cloud-export-models: ExportTargetDescriptor platform=%s ext=%s",
            self.platform,
            self.extension,
        )
        return self


class ListExportTargetsRequest(BaseModel):
    """Request contract for CloudExportService.list_export_targets."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-export-targets",
        min_length=1,
        description="Caller correlation identifier",
    )

    @model_validator(mode="after")
    def _log_request(self) -> ListExportTargetsRequest:
        logger.debug(
            "FR-wizard-cloud-export-requests: ListExportTargetsRequest request_id=%s",
            self.request_id,
        )
        return self


class CloudImportRequest(BaseModel):
    """Request contract for CloudExportService.import_strategy (/algocloud/import)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-cloud-import",
        min_length=1,
        description="Caller correlation identifier",
    )
    source: CloudImportSource = Field(
        default="editor",
        description="Import origin: editor, file, databank, or backtest_id",
    )
    document: HSLStrategyDocument | dict[str, Any] | str | None = Field(
        default=None,
        description="Inline HSL 1.0 or legacy strategy payload when source='editor'",
    )
    file_id: str | None = Field(
        default=None,
        description="Workspace file identifier when source='file'",
    )
    databank_name: str | None = Field(
        default=None,
        description="Source databank name when source='databank'",
    )
    strategy_name: str | None = Field(
        default=None,
        description="Strategy identifier or name when source='databank'",
    )
    backtest_id: str | None = Field(
        default=None,
        description="Wizard backtest identifier when source='backtest_id'",
    )
    strict: bool = Field(
        default=False,
        description="When True, raise WIZARD_INVALID_STRATEGY on validation issues",
    )

    @model_validator(mode="after")
    def _log_request(self) -> CloudImportRequest:
        logger.debug(
            "FR-wizard-cloud-export-requests: CloudImportRequest "
            "request_id=%s source=%s strict=%s",
            self.request_id,
            self.source,
            self.strict,
        )
        return self


class CloudImportResult(BaseModel):
    """Result envelope returned by CloudExportService.import_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: CloudImportSource = Field(
        ...,
        description="Resolved import origin",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Canonical strategy identifier from document.strategy.id",
    )
    document_hash: str = Field(
        ...,
        min_length=1,
        description="Deterministic SHA-256 hex digest of the canonical HSL document",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Normalized canonical HSL 1.0 strategy AST document",
    )
    validation: ValidationReport = Field(
        ...,
        description="3-pass StrategyValidator report for the imported document",
    )

    @model_validator(mode="after")
    def _log_result(self) -> CloudImportResult:
        logger.debug(
            "FR-wizard-cloud-export-models: CloudImportResult "
            "source=%s strategy_id=%s valid=%s",
            self.source,
            self.strategy_id,
            self.validation.valid,
        )
        return self


class ExportStrategyRequest(BaseModel):
    """Request contract for CloudExportService.export_strategy (/algocloud/export)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-export-strategy",
        min_length=1,
        description="Caller correlation identifier",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Canonical HSL 1.0 strategy document to export",
    )
    target_platform: ExportTargetPlatform = Field(
        ...,
        description="Target platform for code or JSON generation",
    )

    @model_validator(mode="after")
    def _log_request(self) -> ExportStrategyRequest:
        logger.debug(
            "FR-wizard-cloud-export-requests: ExportStrategyRequest "
            "request_id=%s strategy_id=%s platform=%s",
            self.request_id,
            self.document.strategy.id,
            self.target_platform,
        )
        return self


class ExportStrategyResult(BaseModel):
    """Result envelope returned by CloudExportService.export_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Canonical strategy identifier",
    )
    target_platform: ExportTargetPlatform = Field(
        ...,
        description="Target platform used for export",
    )
    filename: str = Field(
        ...,
        min_length=1,
        description="Generated source filename with platform extension",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Rendered source code or canonical JSON string",
    )
    sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Deterministic SHA-256 hex digest of the exported UTF-8 content",
    )

    @model_validator(mode="after")
    def _log_result(self) -> ExportStrategyResult:
        logger.debug(
            "FR-wizard-cloud-export-models: ExportStrategyResult "
            "strategy_id=%s platform=%s filename=%s sha256=%s",
            self.strategy_id,
            self.target_platform,
            self.filename,
            self.sha256,
        )
        return self


__all__ = [
    "CloudImportRequest",
    "CloudImportResult",
    "CloudImportSource",
    "ExportStrategyRequest",
    "ExportStrategyResult",
    "ExportTargetDescriptor",
    "ExportTargetPlatform",
    "ListExportTargetsRequest",
]
