"""Pydantic data contracts for ServletStrategy and HSL strategy lifecycle management.

Description:
    Defines the canonical Pydantic v2 models for StrategyDocumentService
    (ServletStrategy equivalent), covering managed strategy records, runtime
    status states (IDLE, RUNNING, STOPPED, ERROR), optimistic revision control,
    and request/result envelopes for add, get, list, start, stop, and remove
    operations.

Purpose:
    FEAT-WIZARD-STRATEGY-LIFECYCLE: Gate G5 (Phase 5.5, WO-WZ-STRATEGY-LIFECYCLE)
    data contracts for HSL 1.0 strategy persistence, revisioning, and runtime
    execution lifecycle.

Key Capabilities:
    - FR-wizard-strategy-lifecycle-models: Defines StrategyRuntimeStatus,
      ManagedStrategyRecord, and RemoveStrategyResult with strict schema
      validation and structured diagnostic logging.
    - FR-wizard-strategy-lifecycle-requests: Defines AddStrategyRequest,
      StrategyIdRequest, ListStrategiesRequest, StartStrategyRequest,
      StopStrategyRequest, and RemoveStrategyRequest.

Python API Usage:
    from app.workspace.algo_wizard.strategies_models import AddStrategyRequest

    req = AddStrategyRequest(request_id="r1", document=hsl_doc, strict=True)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_strategies.py --no-cov -q
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.core.trading.strategy.hsl.validation import ValidationReport

logger = get_logger(__name__)

StrategyRuntimeStatus = Literal["IDLE", "RUNNING", "STOPPED", "ERROR"]


class ManagedStrategyRecord(BaseModel):
    """Versioned HSL 1.0 strategy record managed by StrategyDocumentService."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Canonical strategy identifier matching document.strategy.id",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Human-readable strategy display name",
    )
    status: StrategyRuntimeStatus = Field(
        ...,
        description="Current runtime lifecycle state (IDLE, RUNNING, STOPPED, ERROR)",
    )
    revision: int = Field(
        ...,
        ge=1,
        description="Monotonically increasing optimistic concurrency revision",
    )
    document_hash: str = Field(
        ...,
        min_length=1,
        description="Deterministic SHA-256 hex digest of the canonical HSL document",
    )
    document: HSLStrategyDocument = Field(
        ...,
        description="Canonical HSL 1.0 strategy AST document",
    )
    validation: ValidationReport = Field(
        ...,
        description="Latest 3-pass StrategyValidator report for this document",
    )
    updated_at: str = Field(
        ...,
        min_length=1,
        description="UTC ISO-8601 timestamp of the most recent record mutation",
    )
    connection_name: str = Field(
        default="default",
        min_length=1,
        description="Target execution connection name (ServletStrategy compatibility)",
    )
    symbol: str = Field(
        default="EURUSD",
        min_length=1,
        description="Primary trading symbol resolved from strategy universe",
    )
    timeframe: str = Field(
        default="H1",
        min_length=1,
        description="Primary trading timeframe resolved from strategy timeframe spec",
    )

    @model_validator(mode="after")
    def _log_record(self) -> ManagedStrategyRecord:
        logger.debug(
            "FR-wizard-strategy-lifecycle-models: ManagedStrategyRecord "
            "id=%s status=%s rev=%d valid=%s",
            self.strategy_id,
            self.status,
            self.revision,
            self.validation.valid,
        )
        return self


class AddStrategyRequest(BaseModel):
    """Request contract for StrategyDocumentService.add_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-add",
        min_length=1,
        description="Caller request correlation identifier",
    )
    document: HSLStrategyDocument | dict[str, Any] = Field(
        ...,
        description="HSL 1.0 strategy document or raw/legacy dictionary payload",
    )
    strict: bool = Field(
        default=True,
        description="When True, reject documents that fail 3-pass validation",
    )
    expected_revision: int | None = Field(
        default=None,
        ge=0,
        description="Optional optimistic concurrency revision check (0 for new)",
    )
    connection_name: str = Field(
        default="default",
        min_length=1,
        description="Target execution connection name",
    )


class StrategyIdRequest(BaseModel):
    """Request contract for StrategyDocumentService.get_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-get",
        min_length=1,
        description="Caller request correlation identifier",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Target strategy identifier",
    )


class ListStrategiesRequest(BaseModel):
    """Request contract for StrategyDocumentService.list_strategies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-list",
        min_length=1,
        description="Caller request correlation identifier",
    )
    status: StrategyRuntimeStatus | None = Field(
        default=None,
        description="Optional runtime status filter",
    )


class StartStrategyRequest(BaseModel):
    """Request contract for StrategyDocumentService.start_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-start",
        min_length=1,
        description="Caller request correlation identifier",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Target strategy identifier to compile and start",
    )


class StopStrategyRequest(BaseModel):
    """Request contract for StrategyDocumentService.stop_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-stop",
        min_length=1,
        description="Caller request correlation identifier",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Target strategy identifier to stop",
    )


class RemoveStrategyRequest(BaseModel):
    """Request contract for StrategyDocumentService.remove_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-strategy-remove",
        min_length=1,
        description="Caller request correlation identifier",
    )
    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Target strategy identifier to stop and remove",
    )


class RemoveStrategyResult(BaseModel):
    """Result payload returned by StrategyDocumentService.remove_strategy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy_id: str = Field(
        ...,
        min_length=1,
        description="Removed strategy identifier",
    )
    removed: bool = Field(
        default=True,
        description="Whether the strategy record was removed",
    )
    previous_status: StrategyRuntimeStatus = Field(
        ...,
        description="Lifecycle status immediately prior to removal",
    )
    final_revision: int = Field(
        ...,
        ge=1,
        description="Final revision number of the removed record",
    )


__all__ = [
    "AddStrategyRequest",
    "ListStrategiesRequest",
    "ManagedStrategyRecord",
    "RemoveStrategyRequest",
    "RemoveStrategyResult",
    "StartStrategyRequest",
    "StopStrategyRequest",
    "StrategyIdRequest",
    "StrategyRuntimeStatus",
]
