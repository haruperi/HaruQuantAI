"""HSL 1.0 block catalogue, parameter bounds, and ServletConstants models.

Description:
    Defines the Pydantic data contracts for the AlgoWizard block catalogue,
    parameter bound descriptors, option enumerations, commission calculation
    methods, and ServletConstants request/response envelopes.

Purpose:
    FEAT-WIZARD-CATALOGUE: Typed schemas projecting BlockRegistry metadata and
    HSL 1.0 language constants for the visual Strategy Builder and AI Co-Pilot.

Key Capabilities:
    - FR-wizard-catalogue-models: Defines HSLBlockCatalogueEntry,
      CatalogueParameterBounds, CommissionMethodDescriptor, and
      WizardConstantsBundle envelopes.
    - FR-wizard-catalogue-requests: Defines typed request contracts for
      WizardCatalogueService (get_all, list_commission_methods,
      get_block_descriptor).

Python API Usage:
    from app.workspace.algo_wizard.catalogue_models import GetCatalogueRequest

    req = GetCatalogueRequest(request_id="r1", family="EXPRESSION")

CLI Usage:
    python -c "from app.workspace.algo_wizard import catalogue_models; print(1)"
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.host.logging import get_logger
from app.workspace.algo_wizard.value_models import ScalarLiteral, ScalarValueType

logger = get_logger(__name__)

SemanticNodeFamily = Literal[
    "VALUE",
    "EXPRESSION",
    "CONDITION",
    "ACTION",
    "RULE",
]

StaticReturnType = Literal[
    "float",
    "int",
    "bool",
    "str",
    "price",
    "series",
    "void",
]

CommissionUnit = Literal[
    "percent",
    "per_lot",
    "per_trade",
    "per_share",
]


class CatalogueParameterBounds(BaseModel):
    """Parameter type, default, and numeric range metadata for a block."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(..., min_length=1, description="Parameter identifier")
    param_type: ScalarValueType = Field(
        default="float",
        description="Expected parameter scalar type",
    )
    default: ScalarLiteral | None = Field(
        default=None,
        description="Default parameter value when omitted",
    )
    min_value: int | float | None = Field(
        default=None,
        description="Inclusive lower bound for numeric parameters",
    )
    max_value: int | float | None = Field(
        default=None,
        description="Inclusive upper bound for numeric parameters",
    )
    required: bool = Field(
        default=False,
        description="Whether parameter must be explicitly supplied",
    )
    description: str = Field(default="", description="Human-readable parameter notes")


class CatalogueOptionItem(BaseModel):
    """Selectable constant option item for timeframes, events, or operators."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(..., min_length=1, description="Canonical option identifier")
    label: str = Field(..., min_length=1, description="Display label")
    description: str = Field(default="", description="Option narrative summary")
    category: str = Field(default="", description="Optional grouping tag")


class CommissionMethodDescriptor(BaseModel):
    """Commission calculation method descriptor served by ServletConstants."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method_id: str = Field(..., min_length=1, description="Stable commission method ID")
    name: str = Field(..., min_length=1, description="Display name")
    unit: CommissionUnit = Field(..., description="Commission charging unit")
    default_value: float = Field(
        default=0.0,
        ge=0.0,
        description="Default commission value",
    )
    min_value: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum allowed commission value",
    )
    max_value: float = Field(
        default=100.0,
        ge=0.0,
        description="Maximum allowed commission value",
    )
    description: str = Field(default="", description="Method calculation details")


class HSLBlockCatalogueEntry(BaseModel):
    """Projected HSL 1.0 block descriptor with semantic ID and type metadata."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    semantic_id: str = Field(
        ...,
        min_length=1,
        description="Canonical HSL 1.0 semantic block ID (e.g. indicator.rsi)",
    )
    registry_id: str = Field(
        ...,
        min_length=1,
        description="Underlying BlockRegistry descriptor ID",
    )
    name: str = Field(..., min_length=1, description="Human-readable block name")
    category: str = Field(..., min_length=1, description="Block category key")
    family: SemanticNodeFamily = Field(
        ...,
        description="One of the 5 fundamental HSL semantic node families",
    )
    return_type: StaticReturnType = Field(
        ...,
        description="Static return type used by Pass 3 type checking",
    )
    description: str = Field(default="", description="Block documentation summary")
    parameters: tuple[CatalogueParameterBounds, ...] = Field(
        default_factory=tuple,
        description="Ordered parameter definitions and bounds",
    )
    outputs: tuple[str, ...] = Field(
        default=("main",),
        description="Available output buffer names",
    )
    required_inputs: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Required market price input series",
    )
    aliases: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Recognized shorthand and registry aliases",
    )
    is_causal: bool = Field(
        default=True,
        description="Whether block computation is strictly causal (lookahead-free)",
    )


class WizardConstantsBundle(BaseModel):
    """Complete ServletConstants payload combining blocks and wizard options."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: str = Field(..., min_length=1, description="BlockRegistry revision tag")
    blocks: tuple[HSLBlockCatalogueEntry, ...] = Field(
        default_factory=tuple,
        description="Projected HSL 1.0 block catalogue entries",
    )
    timeframes: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Supported bar timeframes",
    )
    lifecycle_events: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Standardized 14 HSL lifecycle event triggers",
    )
    price_fields: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Supported market bar and derived price fields",
    )
    comparison_operators: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Relational and crossing comparison operators",
    )
    math_operators: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Arithmetic expression operators",
    )
    money_management_modes: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Position sizing modes",
    )
    stop_loss_modes: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Stop-loss calculation modes",
    )
    take_profit_modes: tuple[CatalogueOptionItem, ...] = Field(
        default_factory=tuple,
        description="Take-profit calculation modes",
    )
    commission_methods: tuple[CommissionMethodDescriptor, ...] = Field(
        default_factory=tuple,
        description="Supported broker commission models",
    )

    @model_validator(mode="after")
    def _log_bundle(self) -> WizardConstantsBundle:
        logger.debug(
            "Constructed WizardConstantsBundle revision=%s blocks=%d",
            self.revision,
            len(self.blocks),
        )
        return self


class GetCatalogueRequest(BaseModel):
    """Request parameters for WizardCatalogueService.get_all."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-catalogue",
        min_length=1,
        description="Caller request correlation identifier",
    )
    category: str | None = Field(
        default=None,
        description="Optional block category filter",
    )
    family: SemanticNodeFamily | None = Field(
        default=None,
        description="Optional HSL semantic node family filter",
    )


class ListCommissionMethodsRequest(BaseModel):
    """Request parameters for WizardCatalogueService.list_commission_methods."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-commissions",
        min_length=1,
        description="Caller request correlation identifier",
    )


class GetBlockDescriptorRequest(BaseModel):
    """Request parameters for WizardCatalogueService.get_block_descriptor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(
        default="req-block-descriptor",
        min_length=1,
        description="Caller request correlation identifier",
    )
    block_id: str = Field(
        ...,
        min_length=1,
        description="Semantic or registry block identifier to inspect",
    )
