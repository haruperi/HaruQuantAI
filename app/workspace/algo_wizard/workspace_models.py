"""Pydantic data contracts for AppWizard (WizardService) workspace coordination.

Description:
    Defines the Pydantic v2 models for WizardService (AppWizard equivalent),
    covering the canonical HSL 1.0 built-in examples catalog
    (/AlgoWizard/examples/examples.json), example loading
    (/algowizard/loadExample), strategy file import and persistence
    (/algowizard/loadFile, /algowizard/saveFile), and Retester handoff
    (/algowizard/saveToRetester).

Purpose:
    FEAT-WIZARD-WORKSPACE: Gate G7 (Phase 5.7, WO-WZ-WORKSPACE-COORDINATOR /
    I-AppWizard) data contracts for workspace-level strategy examples, file
    exchange, and Retester handoff.

Key Capabilities:
    - FR-wizard-workspace-models: Defines WizardExampleSummary,
      WizardExamplePayload, SavedStrategyFileResult, and RetesterHandoffResult
      with strict schema validation and structured diagnostic logging.
    - FR-wizard-workspace-requests: Defines ListWizardExamplesRequest,
      LoadWizardExampleRequest, LoadStrategyFileRequest,
      SaveStrategyFileRequest, and SaveToRetesterRequest.

Python API Usage:
    from app.workspace.algo_wizard.workspace_models import LoadWizardExampleRequest

    req = LoadWizardExampleRequest(request_id="r1", example_id="ema_crossover")

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_workspace.py --no-cov -q
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.strategy.contracts import StrategyDocument
from app.workspace.algo_wizard.models import HSLStrategyDocument

logger = get_logger(__name__)


class WizardExampleSummary(BaseModel):
    """Metadata summary for a built-in canonical HSL 1.0 strategy example."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    example_id: str = Field(
        ...,
        min_length=1,
        description="Stable example template identifier (e.g. ema_crossover)",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable example display title",
    )
    category: str = Field(
        ...,
        min_length=1,
        description="Template category (e.g. trend, mean_reversion, breakout)",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Summary of the strategy logic and indicators used",
    )
    tags: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Searchable tags for filtering examples in the UI",
    )

    @model_validator(mode="after")
    def _log_summary(self) -> WizardExampleSummary:
        logger.debug(
            "FR-wizard-workspace-models: WizardExampleSummary id=%s category=%s",
            self.example_id,
            self.category,
        )
        return self


class WizardExamplePayload(BaseModel):
    """Full built-in HSL 1.0 example payload returned by load_example."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: WizardExampleSummary = Field(
        ...,
        description="Summary descriptor for the loaded example",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Validated canonical HSL 1.0 strategy AST document",
    )

    @model_validator(mode="after")
    def _log_payload(self) -> WizardExamplePayload:
        logger.debug(
            "FR-wizard-workspace-models: WizardExamplePayload id=%s strategy_id=%s",
            self.summary.example_id,
            self.document.strategy.id,
        )
        return self


class ListWizardExamplesRequest(BaseModel):
    """Request contract for WizardService.list_examples."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-examples-list",
        min_length=1,
        description="Caller correlation identifier",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter",
    )
    query: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on name/tags",
    )

    @model_validator(mode="after")
    def _log_request(self) -> ListWizardExamplesRequest:
        logger.debug(
            "FR-wizard-workspace-requests: ListWizardExamplesRequest "
            "request_id=%s category=%s query=%s",
            self.request_id,
            self.category,
            self.query,
        )
        return self


class LoadWizardExampleRequest(BaseModel):
    """Request contract for WizardService.load_example (/algowizard/loadExample)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-example-load",
        min_length=1,
        description="Caller correlation identifier",
    )
    example_id: str = Field(
        ...,
        min_length=1,
        description="Target built-in example ID or filename stem",
    )

    @model_validator(mode="after")
    def _log_request(self) -> LoadWizardExampleRequest:
        logger.debug(
            "FR-wizard-workspace-requests: LoadWizardExampleRequest "
            "request_id=%s example_id=%s",
            self.request_id,
            self.example_id,
        )
        return self


class LoadStrategyFileRequest(BaseModel):
    """Request contract for WizardService.load_file (/algowizard/loadFile)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-file-load",
        min_length=1,
        description="Caller correlation identifier",
    )
    file_id: str | None = Field(
        default=None,
        description="Optional saved workspace file identifier or filename",
    )
    payload: dict[str, Any] | str | None = Field(
        default=None,
        description="Optional inline JSON string or dictionary payload (HSL or legacy)",
    )
    strict: bool = Field(
        default=True,
        description="When True, reject documents failing StrategyValidator",
    )

    @model_validator(mode="after")
    def _validate_source(self) -> LoadStrategyFileRequest:
        if not self.file_id and self.payload is None:
            raise ValueError(
                "LoadStrategyFileRequest requires either file_id or payload"
            )
        logger.debug(
            "FR-wizard-workspace-requests: LoadStrategyFileRequest "
            "request_id=%s file_id=%s has_payload=%s",
            self.request_id,
            self.file_id,
            self.payload is not None,
        )
        return self


class SaveStrategyFileRequest(BaseModel):
    """Request contract for WizardService.save_file (/algowizard/saveFile)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-file-save",
        min_length=1,
        description="Caller correlation identifier",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Canonical HSL 1.0 strategy document to persist",
    )
    filename: str | None = Field(
        default=None,
        description="Optional target filename (sanitized to <stem>.json)",
    )
    file_id: str | None = Field(
        default=None,
        description="Optional existing file identifier to overwrite",
    )
    strict: bool = Field(
        default=True,
        description="When True, require 0 validation errors before saving",
    )

    @model_validator(mode="after")
    def _log_request(self) -> SaveStrategyFileRequest:
        logger.debug(
            "FR-wizard-workspace-requests: SaveStrategyFileRequest "
            "request_id=%s strategy_id=%s filename=%s",
            self.request_id,
            self.document.strategy.id,
            self.filename,
        )
        return self


class SavedStrategyFileResult(BaseModel):
    """Result envelope returned by WizardService.save_file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file_id: str = Field(
        ...,
        min_length=1,
        description="Canonical workspace file identifier",
    )
    filename: str = Field(
        ...,
        min_length=1,
        description="Sanitized strategy filename ending in .json",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Strategy identifier from document.strategy.id",
    )
    revision: int = Field(
        ...,
        ge=1,
        description="Monotonically increasing file revision number",
    )
    document_hash: str = Field(
        ...,
        min_length=1,
        description="Deterministic SHA-256 hex digest of the saved HSL document",
    )
    recent_files: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Updated MRU recent strategy files list",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Persisted canonical HSL 1.0 strategy document",
    )

    @model_validator(mode="after")
    def _log_result(self) -> SavedStrategyFileResult:
        logger.debug(
            "FR-wizard-workspace-models: SavedStrategyFileResult "
            "file_id=%s filename=%s rev=%d hash=%s",
            self.file_id,
            self.filename,
            self.revision,
            self.document_hash,
        )
        return self


class SaveToRetesterRequest(BaseModel):
    """Request contract for WizardService.save_to_retester."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="wizard-save-retester",
        min_length=1,
        description="Caller correlation identifier",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Canonical HSL 1.0 strategy document to hand off to Retester",
    )
    retester_project_name: str = Field(
        default="Retester",
        min_length=1,
        description="Target Retester project name",
    )
    backtest_id: str | None = Field(
        default=None,
        description="Optional wizard backtest ID associated with this strategy",
    )

    @model_validator(mode="after")
    def _log_request(self) -> SaveToRetesterRequest:
        logger.debug(
            "FR-wizard-workspace-requests: SaveToRetesterRequest "
            "request_id=%s strategy_id=%s project=%s",
            self.request_id,
            self.document.strategy.id,
            self.retester_project_name,
        )
        return self


class RetesterHandoffResult(BaseModel):
    """Result envelope returned by WizardService.save_to_retester."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    handoff_id: str = Field(
        ...,
        min_length=1,
        description="Unique Retester handoff identifier",
    )
    retester_project_name: str = Field(
        ...,
        min_length=1,
        description="Target Retester project name",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Canonical strategy identifier",
    )
    document_hash: str = Field(
        ...,
        min_length=1,
        description="Deterministic SHA-256 hex digest of the HSL document",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Canonical HSL 1.0 strategy AST document",
    )
    compiled_document: StrategyDocument = Field(
        ...,
        description="Compiled runtime StrategyDocument ready for Retester execution",
    )

    @model_validator(mode="after")
    def _log_result(self) -> RetesterHandoffResult:
        logger.debug(
            "FR-wizard-workspace-models: RetesterHandoffResult "
            "handoff_id=%s strategy_id=%s project=%s",
            self.handoff_id,
            self.strategy_id,
            self.retester_project_name,
        )
        return self


__all__ = [
    "ListWizardExamplesRequest",
    "LoadStrategyFileRequest",
    "LoadWizardExampleRequest",
    "RetesterHandoffResult",
    "SaveStrategyFileRequest",
    "SaveToRetesterRequest",
    "SavedStrategyFileResult",
    "WizardExamplePayload",
    "WizardExampleSummary",
]
