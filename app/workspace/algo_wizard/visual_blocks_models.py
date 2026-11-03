"""Pydantic data contracts for ServletAlgoWizard (VisualBlockService).

Description:
    Defines the Pydantic v2 request and response schemas for VisualBlockService
    (ServletAlgoWizard equivalent), covering wizard configuration, non-mutating
    3-pass document validation, deterministic condition negation, custom block
    definitions (backed by CompositionSpec), block groups, timeframe expansion,
    resource dependency checks, and wizard simulation backtests.

Purpose:
    FEAT-WIZARD-VISUAL-BLOCKS: Gate G6 (Phase 5.6, WO-WZ-VISUAL-BLOCKS /
    I-ServletAlgoWizard) data contracts for visual HSL 1.0 AST authoring and
    simulation runs.

Key Capabilities:
    - FR-wizard-visual-models: Defines WizardConfigResult, CustomBlockDefinition
      (with CompositionSpec projection), BlockGroupDefinition,
      ResourceCheckResult, and WizardBacktestResult.
    - FR-wizard-visual-requests: Defines typed request contracts for all
      VisualBlockService endpoints.

Python API Usage:
    from app.workspace.algo_wizard.visual_blocks_models import NegateConditionRequest

    req = NegateConditionRequest(request_id="r1", condition=cond_node)

CLI Usage:
    uv run python -m pytest tests/workspace/algo_wizard/test_visual_blocks.py
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.core.trading.backtest.contracts import BacktestSettings
from app.core.trading.blocks.composition import CompositionSpec
from app.workspace.algo_wizard.models import (
    ActionNode,
    ConditionNode,
    HSLStrategyDocument,
    ParameterSpec,
)
from app.workspace.algo_wizard.value_models import OperandNode

logger = get_logger(__name__)

CustomBlockFamily = Literal["EXPRESSION", "CONDITION", "ACTION"]
MissingResourceKind = Literal["symbol", "timeframe", "block"]
WizardBacktestState = Literal["COMPLETED", "STOPPED", "FAILED"]


class BlockGroupDefinition(BaseModel):
    """Named palette group of building blocks for the visual strategy builder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    group_id: str = Field(..., min_length=1, description="Stable block group ID")
    name: str = Field(..., min_length=1, description="Display group name")
    description: str = Field(default="", description="Group summary")
    block_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Ordered semantic or custom block IDs in this group",
    )
    enabled: bool = Field(default=True, description="Whether group is active")


class CustomBlockDefinition(BaseModel):
    """Reusable parameterized HSL condition/expression/action subtree."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    block_id: str = Field(
        ...,
        min_length=1,
        description="Unique custom block identifier (e.g. custom.rsi_filter)",
    )
    name: str = Field(..., min_length=1, description="Human-readable block name")
    category: str = Field(
        default="custom",
        min_length=1,
        description="Block category key",
    )
    family: CustomBlockFamily = Field(
        default="CONDITION",
        description="Semantic family of the root AST subtree",
    )
    owner_id: str = Field(
        default="rsi",
        min_length=1,
        description="Primary indicator or block owner ID for CompositionSpec",
    )
    donor: str = Field(
        default="AlgoWizardCustomBlock",
        min_length=1,
        description="Provenance tag for CompositionSpec",
    )
    description: str = Field(default="", description="Custom block description")
    parameters: dict[str, ParameterSpec] = Field(
        default_factory=dict,
        description="Parameterized inputs exposed by this custom block",
    )
    subtree: ConditionNode | OperandNode | ActionNode = Field(
        ...,
        description="Root HSL 1.0 AST node encapsulated by this custom block",
    )
    generation_eligible: bool = Field(
        default=False,
        description="Whether block is eligible for automated strategy generation",
    )

    def to_composition_spec(self) -> CompositionSpec:
        """Project this custom block into an immutable Core CompositionSpec."""
        param_map: dict[str, Any] = {}
        for p_name, spec in sorted(self.parameters.items()):
            json_type = {
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "str": "string",
            }.get(spec.type, "number")
            entry: dict[str, Any] = {
                "type": json_type,
                "default": spec.default,
                "required": False,
            }
            if spec.min is not None:
                entry["minimum"] = spec.min
            if spec.max is not None:
                entry["maximum"] = spec.max
            param_map[p_name] = entry

        recipe: dict[str, Any] = {
            "family": self.family,
            "parameters": param_map,
            "nodes": {"root": {"indicator": self.owner_id}},
            "expression": self.subtree.model_dump(mode="json"),
        }
        return CompositionSpec(
            id=self.block_id,
            name=self.name,
            donor=self.donor,
            owner_id=self.owner_id,
            recipe=recipe,
            generation_eligible=self.generation_eligible,
        )


class WizardConfigResult(BaseModel):
    """Default configuration bundle returned by VisualBlockService.get_config."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Canonical HSL schema version",
    )
    supported_lifecycle_events: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Supported HSL lifecycle event triggers",
    )
    default_symbol: str = Field(
        default="EURUSD",
        min_length=1,
        description="Default primary symbol for new strategies",
    )
    default_timeframe: str = Field(
        default="H1",
        min_length=1,
        description="Default primary timeframe for new strategies",
    )
    supported_timeframes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Supported bar timeframe codes",
    )
    custom_block_groups: tuple[BlockGroupDefinition, ...] = Field(
        default_factory=tuple,
        description="Active custom block groups",
    )
    custom_blocks_count: int = Field(
        default=0,
        ge=0,
        description="Number of registered custom blocks",
    )

    @model_validator(mode="after")
    def _log_config(self) -> WizardConfigResult:
        logger.debug(
            "FR-wizard-visual-models: WizardConfigResult schema=%s groups=%d",
            self.schema_version,
            len(self.custom_block_groups),
        )
        return self


class MissingResourceItem(BaseModel):
    """Single missing symbol, timeframe, or block dependency."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    resource_type: MissingResourceKind = Field(
        ...,
        description="Category of missing resource (symbol, timeframe, block)",
    )
    identifier: str = Field(
        ...,
        min_length=1,
        description="Missing resource identifier",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="AST JSON path where the dependency was referenced",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="Diagnostic explanation of the missing dependency",
    )


class ResourceCheckResult(BaseModel):
    """Dependency check summary returned by VisualBlockService.check_resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ready: bool = Field(
        ...,
        description="True when zero missing dependencies were detected",
    )
    referenced_symbols: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Unique explicit symbols referenced by the strategy",
    )
    referenced_timeframes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Unique explicit timeframes referenced by the strategy",
    )
    referenced_blocks: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Unique indicator/function/custom block IDs referenced",
    )
    missing_resources: tuple[MissingResourceItem, ...] = Field(
        default_factory=tuple,
        description="Detected missing symbol, timeframe, or block resources",
    )


class WizardBarInput(BaseModel):
    """OHLCV bar input for VisualBlockService.run_backtest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    time: int = Field(..., ge=0, description="Bar timestamp in epoch seconds")
    open: float = Field(..., description="Bar open price")
    high: float = Field(..., description="Bar high price")
    low: float = Field(..., description="Bar low price")
    close: float = Field(..., description="Bar close price")
    volume: float = Field(default=100.0, ge=0.0, description="Bar volume")


class WizardTradeLogEntry(BaseModel):
    """Recorded order or position action during a wizard simulation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bar_index: int = Field(..., ge=0, description="Zero-based bar index")
    timestamp: int = Field(..., ge=0, description="Bar timestamp in epoch seconds")
    action: str = Field(..., min_length=1, description="Emitted action type")
    symbol: str = Field(..., min_length=1, description="Traded symbol")
    side: str = Field(..., min_length=1, description="Order/position side")
    volume: float = Field(..., ge=0.0, description="Order/position volume")
    price: float = Field(..., description="Execution or trigger price")
    sl: float = Field(default=0.0, description="Stop-loss level")
    tp: float = Field(default=0.0, description="Take-profit level")
    comment: str = Field(default="", description="Action comment or reason")


class WizardBacktestStatus(BaseModel):
    """Status response returned by VisualBlockService.stop_backtest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    backtest_id: str = Field(..., min_length=1, description="Backtest run identifier")
    strategy_id: str = Field(..., min_length=1, description="Evaluated strategy ID")
    status: WizardBacktestState = Field(..., description="Current backtest status")
    stopped: bool = Field(default=False, description="Whether run was stopped")
    message: str = Field(default="", description="Human-readable status summary")


class WizardBacktestResult(BaseModel):
    """Simulation results returned by VisualBlockService.run_backtest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    backtest_id: str = Field(..., min_length=1, description="Backtest run identifier")
    strategy_id: str = Field(..., min_length=1, description="Evaluated strategy ID")
    status: WizardBacktestState = Field(..., description="Final backtest status")
    bars_evaluated: int = Field(..., ge=0, description="Number of bars evaluated")
    total_orders_opened: int = Field(..., ge=0, description="Count of opened orders")
    total_positions_closed: int = Field(
        ...,
        ge=0,
        description="Count of closed positions",
    )
    total_orders_modified: int = Field(
        ...,
        ge=0,
        description="Count of modified orders/positions",
    )
    total_orders_cancelled: int = Field(
        ...,
        ge=0,
        description="Count of cancelled pending orders",
    )
    equity_delta: float = Field(
        default=0.0,
        description="Simulated net realized/mark-to-market PnL delta",
    )
    trade_log: tuple[WizardTradeLogEntry, ...] = Field(
        default_factory=tuple,
        description="Chronological log of emitted trading actions",
    )


class GetWizardConfigRequest(BaseModel):
    """Request contract for VisualBlockService.get_config."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-wizard-config",
        min_length=1,
        description="Caller request correlation identifier",
    )


class ValidateDocumentRequest(BaseModel):
    """Request contract for VisualBlockService.validate_document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-validate-doc",
        min_length=1,
        description="Caller request correlation identifier",
    )
    document: HSLStrategyDocument | dict[str, Any] = Field(
        ...,
        description="HSL 1.0 strategy document or raw dictionary payload",
    )


class NegateConditionRequest(BaseModel):
    """Request contract for VisualBlockService.negate_condition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-negate-cond",
        min_length=1,
        description="Caller request correlation identifier",
    )
    condition: ConditionNode = Field(
        ...,
        description="HSL 1.0 condition tree to negate deterministically",
    )
    distribute_logical: bool = Field(
        default=False,
        description="When True, apply De Morgan's law across logical AND/OR nodes",
    )


class SaveCustomBlocksRequest(BaseModel):
    """Request contract for VisualBlockService.save_custom_blocks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-save-custom-blocks",
        min_length=1,
        description="Caller request correlation identifier",
    )
    blocks: tuple[CustomBlockDefinition, ...] = Field(
        ...,
        description="Custom block definitions to validate and persist",
    )
    replace_all: bool = Field(
        default=False,
        description="When True, replace existing custom blocks before saving",
    )


class LoadCustomBlocksRequest(BaseModel):
    """Request contract for VisualBlockService.load_custom_blocks."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-load-custom-blocks",
        min_length=1,
        description="Caller request correlation identifier",
    )
    category: str | None = Field(
        default=None,
        description="Optional category filter",
    )


class SaveBlockGroupsRequest(BaseModel):
    """Request contract for VisualBlockService.save_block_groups."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-save-block-groups",
        min_length=1,
        description="Caller request correlation identifier",
    )
    groups: tuple[BlockGroupDefinition, ...] = Field(
        ...,
        description="Block group definitions to persist",
    )
    replace_all: bool = Field(
        default=False,
        description="When True, replace existing block groups before saving",
    )


class LoadBlockGroupsRequest(BaseModel):
    """Request contract for VisualBlockService.load_block_groups."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-load-block-groups",
        min_length=1,
        description="Caller request correlation identifier",
    )
    enabled_only: bool = Field(
        default=False,
        description="When True, return only enabled block groups",
    )


class AddTimeframeRequest(BaseModel):
    """Request contract for VisualBlockService.add_timeframe."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-add-timeframe",
        min_length=1,
        description="Caller request correlation identifier",
    )
    document: HSLStrategyDocument | dict[str, Any] = Field(
        ...,
        description="Target HSL strategy document to update",
    )
    timeframe: str = Field(
        ...,
        min_length=1,
        description="Timeframe code (e.g. M15, H4, D1) to add to timeframe.additional",
    )


class CheckResourcesRequest(BaseModel):
    """Request contract for VisualBlockService.check_resources."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-check-resources",
        min_length=1,
        description="Caller request correlation identifier",
    )
    document: HSLStrategyDocument | dict[str, Any] = Field(
        ...,
        description="HSL strategy document to inspect for resource dependencies",
    )
    available_symbols: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Optional available market data symbols to verify against",
    )
    available_timeframes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Optional available market data timeframes to verify against",
    )


class WizardBacktestRequest(BaseModel):
    """Request contract for VisualBlockService.run_backtest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-wizard-backtest",
        min_length=1,
        description="Caller request correlation identifier",
    )
    backtest_id: str = Field(
        default="bt-wizard-001",
        min_length=1,
        description="Unique backtest run identifier",
    )
    document: HSLStrategyDocument | dict[str, Any] = Field(
        ...,
        description="HSL strategy document to compile and simulate",
    )
    bars: tuple[WizardBarInput, ...] = Field(
        default_factory=tuple,
        description="Chronological OHLCV bar sequence for causal evaluation",
    )
    settings: BacktestSettings = Field(default_factory=BacktestSettings)

    negate_signals: bool = Field(
        default=False,
        description="When True, negate rule conditions prior to simulation",
    )


class StopWizardBacktestRequest(BaseModel):
    """Request contract for VisualBlockService.stop_backtest."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-stop-backtest",
        min_length=1,
        description="Caller request correlation identifier",
    )
    backtest_id: str = Field(
        ...,
        min_length=1,
        description="Target backtest run identifier to stop",
    )


class GetWizardBacktestRequest(BaseModel):
    """Request contract for VisualBlockService.get_backtest_results."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-get-backtest",
        min_length=1,
        description="Caller request correlation identifier",
    )
    backtest_id: str = Field(
        ...,
        min_length=1,
        description="Target backtest run identifier to retrieve",
    )


__all__ = [
    "AddTimeframeRequest",
    "BlockGroupDefinition",
    "CheckResourcesRequest",
    "CustomBlockDefinition",
    "CustomBlockFamily",
    "GetWizardBacktestRequest",
    "GetWizardConfigRequest",
    "LoadBlockGroupsRequest",
    "LoadCustomBlocksRequest",
    "MissingResourceItem",
    "MissingResourceKind",
    "NegateConditionRequest",
    "ResourceCheckResult",
    "SaveBlockGroupsRequest",
    "SaveCustomBlocksRequest",
    "StopWizardBacktestRequest",
    "ValidateDocumentRequest",
    "WizardBacktestRequest",
    "WizardBacktestResult",
    "WizardBacktestState",
    "WizardBacktestStatus",
    "WizardBarInput",
    "WizardConfigResult",
    "WizardTradeLogEntry",
]
