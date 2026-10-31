"""HSL 1.0 strategy envelope, condition trees, actions, and priority-ordered rules.

Description:
    Defines the canonical CONDITION, ACTION, and RULE semantic node families,
    strategy parameters vs. mutable runtime variables, multi-symbol universe
    and timeframe declarations, 14 lifecycle events, and the top-level
    HSLStrategyPayload and HSLStrategyDocument envelopes.

Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Canonical AST models for the HaruQuant Strategy
    Language (HSL 1.0) consumed across the visual Strategy Builder, validator,
    compiler, code generator, and AI Strategy Co-Pilot.

Key Capabilities:
    - FR-hsl-condition-trees: Composable boolean condition AST nodes (logical,
      not, comparison, state, temporal) replacing legacy nested XML <If> blocks.
    - FR-hsl-action-nodes: Discriminated action nodes for market/pending entries,
      exits, SL/TP modification, order cancellation, variable mutation, and alerts.
    - FR-hsl-priority-rules: Event-driven WHEN -> THEN -> ELSE RuleNode models
      with explicit priority ordering across 14 lifecycle events.
    - FR-hsl-strategy-document: Versioned HSLStrategyDocument (schema_version
      1.0.0) separating parameters, variables, sub-DSLs, and rules.

Python API Usage:
    from app.workspace.algo_wizard.models import (
        HSLStrategyDocument,
        HSLStrategyPayload,
    )

    doc = HSLStrategyDocument(
        strategy=HSLStrategyPayload(id="ema-cross", name="EMA Crossover")
    )

CLI Usage:
    python -c "from app.workspace.algo_wizard import models; print(1)"
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.host.logging import get_logger
from app.workspace.algo_wizard.value_models import (
    MoneyManagementSpec,
    OperandNode,
    RiskManagementSpec,
    ScalarLiteral,
    ScalarValueType,
    StopLossSpec,
    TakeProfitSpec,
    TradeManagementSpec,
    TradingOptionsSpec,
    coerce_operand_value,
)

logger = get_logger(__name__)

LifecycleEventType = Literal[
    "on_start",
    "on_stop",
    "on_timer",
    "on_tick",
    "on_bar_open",
    "on_bar_close",
    "on_order_submitted",
    "on_order_filled",
    "on_order_cancelled",
    "on_order_rejected",
    "on_position_opened",
    "on_position_closed",
    "on_session_open",
    "on_session_close",
]

ComparisonOperator = Literal[
    "greater_than",
    "greater_or_equal",
    "less_than",
    "less_or_equal",
    "equal",
    "not_equal",
    "crosses_above",
    "crosses_below",
]

StateConditionKind = Literal[
    "position.is_flat",
    "position.is_long",
    "position.is_short",
    "session.is_open",
    "always_true",
    "always_false",
]

TemporalOperator = Literal[
    "remains_true_for",
    "occurred_within",
]

_ACTION_NAMES: frozenset[str] = frozenset(
    {
        "enter_market",
        "enter_stop",
        "enter_limit",
        "exit_position",
        "modify_stop_loss",
        "modify_take_profit",
        "cancel_orders",
        "set_variable",
        "emit_alert",
    }
)


class ParameterSpec(BaseModel):
    """Externally configurable and optimizable strategy parameter."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: ScalarValueType = Field(default="float", description="Parameter scalar type")
    default: ScalarLiteral = Field(..., description="Default parameter value")
    min: int | float | None = Field(
        default=None,
        description="Minimum allowed numeric value for optimization/validation",
    )
    max: int | float | None = Field(
        default=None,
        description="Maximum allowed numeric value for optimization/validation",
    )
    step: int | float | None = Field(
        default=None,
        gt=0,
        description="Optimization grid step increment",
    )
    optimize: bool = Field(
        default=False,
        description="Whether this parameter participates in strategy optimization",
    )
    description: str = Field(default="", description="Human-readable parameter notes")


class VariableSpec(BaseModel):
    """Mutable runtime state variable declaration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: ScalarValueType = Field(default="float", description="Variable scalar type")
    initial: ScalarLiteral = Field(..., description="Initial runtime value")
    scope: Literal["strategy", "session"] = Field(
        default="strategy",
        description="Reset scope (strategy lifetime or per trading session)",
    )
    description: str = Field(default="", description="Human-readable variable notes")


class UniverseSpec(BaseModel):
    """Multi-symbol instrument universe declaration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mode: Literal["explicit", "portfolio", "dynamic"] = Field(
        default="explicit",
        description="Symbol selection mode",
    )
    symbols: tuple[str, ...] = Field(
        default=("EURUSD",),
        min_length=1,
        description="Declared tradable and referenceable instrument symbols",
    )


class TimeframeSpec(BaseModel):
    """Primary and additional multi-timeframe bar subscriptions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    primary: str = Field(
        default="H1",
        min_length=1,
        description="Primary execution bar timeframe",
    )
    additional: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Additional higher or secondary timeframes",
    )


class LifecycleEventSpec(BaseModel):
    """Rule trigger lifecycle event specification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: LifecycleEventType = Field(
        default="on_bar_close",
        description="Lifecycle event trigger type",
    )
    timeframe: str = Field(
        default="$current_timeframe",
        min_length=1,
        description="Timeframe filter for bar events",
    )
    symbol: str = Field(
        default="$current_symbol",
        min_length=1,
        description="Symbol filter for bar/order/position events",
    )


class ComparisonConditionNode(BaseModel):
    """Binary relational or crossing CONDITION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["comparison"] = "comparison"
    operator: ComparisonOperator = Field(
        ...,
        description="Relational or bar-crossing comparison operator",
    )
    left: OperandNode = Field(..., description="Left-hand operand")
    right: OperandNode = Field(..., description="Right-hand operand")

    @field_validator("left", "right", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class StateConditionNode(BaseModel):
    """Portfolio, position, or session state CONDITION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["state"] = "state"
    state: StateConditionKind = Field(
        ...,
        description="Semantic state predicate identifier",
    )


class LogicalConditionNode(BaseModel):
    """Composable boolean AND / OR CONDITION tree node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["logical"] = "logical"
    operator: Literal["and", "or"] = Field(
        default="and",
        description="Boolean conjunction or disjunction operator",
    )
    conditions: tuple[ConditionNode, ...] = Field(
        ...,
        min_length=1,
        description="Child condition nodes",
    )


class NotConditionNode(BaseModel):
    """Boolean negation CONDITION tree node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["not"] = "not"
    condition: ConditionNode = Field(..., description="Negated child condition node")


class TemporalConditionNode(BaseModel):
    """Multi-bar persistence or lookback window CONDITION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["temporal"] = "temporal"
    operator: TemporalOperator = Field(
        ...,
        description="Temporal window predicate (remains_true_for or occurred_within)",
    )
    condition: ConditionNode = Field(..., description="Monitored child condition node")
    bars: int = Field(
        ...,
        ge=1,
        description="Number of consecutive or lookback bars",
    )


ConditionNode = Annotated[
    LogicalConditionNode
    | NotConditionNode
    | ComparisonConditionNode
    | StateConditionNode
    | TemporalConditionNode,
    Field(discriminator="type"),
]


class OrderMarketActionNode(BaseModel):
    """Market order entry ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["enter_market"] = "enter_market"
    side: Literal["long", "short"] = Field(..., description="Order direction")
    size: MoneyManagementSpec | OperandNode | None = Field(
        default=None,
        description="Optional per-action position sizing override",
    )
    stop_loss: StopLossSpec | None = Field(
        default=None,
        description="Optional per-order stop-loss override",
    )
    take_profit: TakeProfitSpec | None = Field(
        default=None,
        description="Optional per-order take-profit override",
    )
    comment: str = Field(default="", description="Order tag or comment")
    magic_number: int | None = Field(
        default=None,
        description="Optional strategy order identifier",
    )


class OrderPendingActionNode(BaseModel):
    """Stop or limit pending order entry ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["enter_stop", "enter_limit"] = Field(
        ...,
        description="Pending order execution type",
    )
    side: Literal["long", "short"] = Field(..., description="Order direction")
    entry_price: OperandNode = Field(..., description="Pending trigger/limit price")
    expiration_bars: int | None = Field(
        default=None,
        ge=1,
        description="Optional pending order expiration in bars",
    )
    size: MoneyManagementSpec | OperandNode | None = Field(
        default=None,
        description="Optional per-action position sizing override",
    )
    stop_loss: StopLossSpec | None = Field(
        default=None,
        description="Optional per-order stop-loss override",
    )
    take_profit: TakeProfitSpec | None = Field(
        default=None,
        description="Optional per-order take-profit override",
    )
    comment: str = Field(default="", description="Order tag or comment")
    magic_number: int | None = Field(
        default=None,
        description="Optional strategy order identifier",
    )

    @field_validator("entry_price", mode="before")
    @classmethod
    def _coerce_entry_price(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class PositionCloseActionNode(BaseModel):
    """Open position full or partial close ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["exit_position"] = "exit_position"
    target_side: Literal["long", "short", "any"] = Field(
        default="any",
        description="Position direction to close",
    )
    quantity_pct: float = Field(
        default=100.0,
        gt=0.0,
        le=100.0,
        description="Percentage of open position quantity to close",
    )
    reason: str = Field(default="", description="Exit reason tag")


class OrderModifyActionNode(BaseModel):
    """Open position stop-loss or take-profit modification ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["modify_stop_loss", "modify_take_profit"] = Field(
        ...,
        description="Protective order modification action",
    )
    stop_loss: StopLossSpec | None = Field(
        default=None,
        description="New stop-loss specification when action is modify_stop_loss",
    )
    take_profit: TakeProfitSpec | None = Field(
        default=None,
        description="New take-profit specification when action is modify_take_profit",
    )

    @model_validator(mode="after")
    def _validate_target(self) -> OrderModifyActionNode:
        if self.action == "modify_stop_loss" and self.stop_loss is None:
            msg = "OrderModifyActionNode 'modify_stop_loss' requires 'stop_loss'."
            raise ValueError(msg)
        if self.action == "modify_take_profit" and self.take_profit is None:
            msg = "OrderModifyActionNode 'modify_take_profit' requires 'take_profit'."
            raise ValueError(msg)
        return self


class OrderCancelActionNode(BaseModel):
    """Pending order cancellation ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["cancel_orders"] = "cancel_orders"
    target_side: Literal["long", "short", "any"] = Field(
        default="any",
        description="Pending order direction filter to cancel",
    )


class VariableSetActionNode(BaseModel):
    """Runtime variable assignment ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["set_variable"] = "set_variable"
    name: str = Field(..., min_length=1, description="Target mutable variable key")
    value: OperandNode = Field(..., description="Assigned operand expression")

    @field_validator("value", mode="before")
    @classmethod
    def _coerce_value(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class AlertActionNode(BaseModel):
    """Diagnostic or operator notification alert ACTION node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["action"] = "action"
    action: Literal["emit_alert"] = "emit_alert"
    level: Literal["info", "warning", "error"] = Field(
        default="info",
        description="Alert severity level",
    )
    message: str = Field(..., min_length=1, description="Alert message text")


ActionNode = Annotated[
    OrderMarketActionNode
    | OrderPendingActionNode
    | PositionCloseActionNode
    | OrderModifyActionNode
    | OrderCancelActionNode
    | VariableSetActionNode
    | AlertActionNode,
    Field(discriminator="action"),
]


def _normalize_action_entry(item: Any) -> Any:
    """Normalize shorthand {'type': '<action>'} dicts into canonical action nodes."""
    if isinstance(item, Mapping):
        raw_type = item.get("type")
        if (
            isinstance(raw_type, str)
            and raw_type in _ACTION_NAMES
            and "action" not in item
        ):
            normalized = dict(item)
            normalized["type"] = "action"
            normalized["action"] = raw_type
            return normalized
    return item


class RuleNode(BaseModel):
    """Event-driven, priority-ordered WHEN -> THEN -> ELSE execution RULE node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["rule"] = "rule"
    id: str = Field(..., min_length=1, description="Unique rule identifier")
    name: str = Field(default="", description="Human-readable rule label")
    priority: int = Field(
        default=100,
        description="Deterministic ascending execution priority (lower runs first)",
    )
    enabled: bool = Field(default=True, description="Whether rule is active")
    event: LifecycleEventSpec = Field(
        default_factory=LifecycleEventSpec,
        description="Lifecycle event that triggers rule evaluation",
    )
    when: ConditionNode = Field(..., description="Root boolean condition tree")
    then: tuple[ActionNode, ...] = Field(
        ...,
        min_length=1,
        description="Actions executed when 'when' evaluates to True",
    )
    else_then: tuple[ActionNode, ...] = Field(
        default_factory=tuple,
        description="Optional actions executed when 'when' evaluates to False",
    )

    @field_validator("event", mode="before")
    @classmethod
    def _coerce_event_shorthand(cls, v: Any) -> Any:
        if isinstance(v, str):
            return {"type": v}
        return v

    @field_validator("then", "else_then", mode="before")
    @classmethod
    def _normalize_actions(cls, v: Any) -> Any:
        if isinstance(v, (list, tuple)):
            return tuple(_normalize_action_entry(item) for item in v)
        return v


class HSLStrategyPayload(BaseModel):
    """Canonical HSL 1.0 strategy definition body."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str = Field(..., min_length=1, description="Stable strategy identifier")
    name: str = Field(..., min_length=1, description="Human-readable strategy name")
    description: str = Field(default="", description="Strategy narrative summary")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Author, tag, provenance, and audit metadata",
    )
    universe: UniverseSpec = Field(
        default_factory=UniverseSpec,
        description="Instrument universe specification",
    )
    timeframe: TimeframeSpec = Field(
        default_factory=TimeframeSpec,
        description="Primary and additional timeframe subscriptions",
    )
    parameters: dict[str, ParameterSpec] = Field(
        default_factory=dict,
        description="Externally configurable and optimizable parameters",
    )
    variables: dict[str, VariableSpec] = Field(
        default_factory=dict,
        description="Mutable runtime state variables",
    )
    money_management: MoneyManagementSpec = Field(
        default_factory=MoneyManagementSpec,
        description="Position sizing and money management specification",
    )
    risk_management: RiskManagementSpec = Field(
        default_factory=RiskManagementSpec,
        description="Portfolio risk limits and default protective stops",
    )
    trade_management: TradeManagementSpec = Field(
        default_factory=TradeManagementSpec,
        description="Breakeven, trailing stop, time stop, and partial exits",
    )
    trading_options: TradingOptionsSpec = Field(
        default_factory=TradingOptionsSpec,
        description="Session filters and end-of-day/Friday close options",
    )
    rules: tuple[RuleNode, ...] = Field(
        default_factory=tuple,
        description="Ordered rule definitions (sorted by (priority, id) on compile)",
    )


class HSLStrategyDocument(BaseModel):
    """Top-level versioned HSL 1.0 strategy AST document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0.0"] = Field(
        default="1.0.0",
        description="Canonical HaruQuant Strategy Language schema version",
    )
    strategy: HSLStrategyPayload = Field(
        ...,
        description="Canonical strategy AST payload",
    )

    @model_validator(mode="after")
    def _log_document_construction(self) -> HSLStrategyDocument:
        logger.debug(
            "Constructed HSLStrategyDocument id=%s schema_version=%s rules=%d",
            self.strategy.id,
            self.schema_version,
            len(self.strategy.rules),
        )
        return self


LogicalConditionNode.model_rebuild()
NotConditionNode.model_rebuild()
ComparisonConditionNode.model_rebuild()
StateConditionNode.model_rebuild()
TemporalConditionNode.model_rebuild()
OrderMarketActionNode.model_rebuild()
OrderPendingActionNode.model_rebuild()
PositionCloseActionNode.model_rebuild()
OrderModifyActionNode.model_rebuild()
OrderCancelActionNode.model_rebuild()
VariableSetActionNode.model_rebuild()
AlertActionNode.model_rebuild()
RuleNode.model_rebuild()
HSLStrategyPayload.model_rebuild()
HSLStrategyDocument.model_rebuild()
