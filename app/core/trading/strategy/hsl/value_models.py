"""HSL 1.0 value nodes, expression AST nodes, and typed domain sub-DSLs.

Description:
    Defines the canonical VALUE and EXPRESSION semantic node families for the
    HaruQuant Strategy Language (HSL 1.0), along with multi-symbol and
    multi-timeframe evaluation contexts and typed domain sub-DSLs for stop loss,
    take profit, money management, risk management, trade management, and
    session trading options.

Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Strongly typed, side-effect-free value and
    expression AST nodes and trading setup sub-DSLs for AlgoWizard strategies.

Key Capabilities:
    - FR-hsl-evaluation-context: Binds symbol, timeframe, and bar shift metadata
      to market price and indicator expressions for lookahead-safe evaluation.
    - FR-hsl-operand-nodes: Discriminated union across VALUE (literal, parameter,
      variable, price) and EXPRESSION (indicator, math, function, position_attr)
      AST nodes with recursive tree composition.
    - FR-hsl-domain-sub-dsls: Typed Pydantic sub-DSLs for StopLossSpec,
      TakeProfitSpec, MoneyManagementSpec, RiskManagementSpec,
      TradeManagementSpec, and TradingOptionsSpec without raw code strings.

Python API Usage:
    from app.core.trading.strategy.hsl.value_models import (
        IndicatorExpressionNode,
        ValueLiteralNode,
    )

    node = IndicatorExpressionNode(
        name="indicator.rsi",
        params={"period": ValueLiteralNode(value=14, value_type="int")},
    )

CLI Usage:
    python -c "from app.core.trading.strategy.hsl import value_models; print(1)"
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.host.logging import get_logger

logger = get_logger(__name__)

ScalarLiteral = int | float | bool | str
ScalarValueType = Literal["int", "float", "bool", "str"]
PriceField = Literal[
    "open",
    "high",
    "low",
    "close",
    "volume",
    "typical",
    "median",
    "weighted",
]
MathOperator = Literal[
    "add",
    "subtract",
    "multiply",
    "divide",
    "min",
    "max",
    "abs",
]
PositionAttrField = Literal[
    "open_price",
    "unrealized_pnl",
    "bars_held",
    "size",
    "side",
]


def _infer_scalar_type(value: ScalarLiteral) -> ScalarValueType:
    """Infer the canonical HSL scalar type tag from a Python literal."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return "str"


class EvaluationContext(BaseModel):
    """Multi-symbol, multi-timeframe, and bar-shift evaluation context."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    symbol: str = Field(
        default="$current_symbol",
        min_length=1,
        description="Target symbol or $current_symbol placeholder",
    )
    timeframe: str = Field(
        default="$current_timeframe",
        min_length=1,
        description="Target timeframe or $current_timeframe placeholder",
    )
    shift: int = Field(
        default=0,
        description="Historical bar offset (0 = current bar, >= 1 = prior closed bars)",
    )


class ValueLiteralNode(BaseModel):
    """Typed constant literal VALUE node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["value"] = "value"
    value: ScalarLiteral = Field(..., description="Constant scalar value")
    value_type: ScalarValueType | None = Field(
        default=None,
        description="Explicit scalar type tag; inferred automatically when omitted",
    )

    @model_validator(mode="after")
    def _populate_value_type(self) -> ValueLiteralNode:
        if self.value_type is None:
            inferred = _infer_scalar_type(self.value)
            object.__setattr__(self, "value_type", inferred)
        actual = _infer_scalar_type(self.value)
        if self.value_type != actual and not (
            self.value_type == "float" and actual == "int"
        ):
            raise ValueError("Literal value does not match its declared type")
        return self


class ParameterRefNode(BaseModel):
    """External strategy parameter reference VALUE node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["parameter"] = "parameter"
    name: str = Field(..., min_length=1, description="Referenced parameter key")


class VariableRefNode(BaseModel):
    """Mutable runtime variable reference VALUE node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["variable"] = "variable"
    name: str = Field(..., min_length=1, description="Referenced variable key")


class MarketPriceNode(BaseModel):
    """Market bar price or derived price series VALUE node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["price"] = "price"
    field: PriceField = Field(
        default="close",
        description="Bar price field or derived price series",
    )
    context: EvaluationContext = Field(
        default_factory=EvaluationContext,
        description="Symbol, timeframe, and bar shift context",
    )


class PositionAttrNode(BaseModel):
    """Open position attribute EXPRESSION node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["position_attr"] = "position_attr"
    field: PositionAttrField = Field(
        ...,
        description="Open position attribute field to inspect",
    )


class IndicatorExpressionNode(BaseModel):
    """Parameterized technical indicator EXPRESSION node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["indicator"] = "indicator"
    name: str = Field(
        ...,
        min_length=1,
        description="Semantic indicator identifier (e.g. indicator.rsi or rsi)",
    )
    inputs: dict[str, OperandNode] = Field(
        default_factory=dict,
        description="Named input series operands such as source price",
    )
    params: dict[str, OperandNode | ScalarLiteral] = Field(
        default_factory=dict,
        description="Named indicator parameters as operand nodes or scalar literals",
    )
    output: str = Field(
        default="main",
        min_length=1,
        description="Selected indicator output buffer name",
    )
    context: EvaluationContext = Field(
        default_factory=EvaluationContext,
        description="Symbol, timeframe, and bar shift context",
    )


class MathExpressionNode(BaseModel):
    """Unary or binary arithmetic EXPRESSION node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["math"] = "math"
    operator: MathOperator = Field(..., description="Arithmetic operator")
    left: OperandNode = Field(..., description="Left or primary operand")
    right: OperandNode | None = Field(
        default=None,
        description="Right operand (required for binary operators, omitted for abs)",
    )

    @model_validator(mode="after")
    def _validate_arity(self) -> MathExpressionNode:
        if self.operator == "abs":
            if self.right is not None:
                msg = "Unary math operator 'abs' must not specify a 'right' operand."
                raise ValueError(msg)
        elif self.right is None:
            msg = f"Binary math operator '{self.operator}' requires a 'right' operand."
            raise ValueError(msg)
        return self


class FunctionExpressionNode(BaseModel):
    """Built-in semantic function EXPRESSION node."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: Literal["function"] = "function"
    name: str = Field(..., min_length=1, description="Semantic function identifier")
    args: tuple[OperandNode, ...] = Field(
        default_factory=tuple,
        description="Positional operand arguments",
    )


ValueNode = Annotated[
    ValueLiteralNode | ParameterRefNode | VariableRefNode | MarketPriceNode,
    Field(discriminator="type"),
]

ExpressionNode = Annotated[
    IndicatorExpressionNode
    | MathExpressionNode
    | FunctionExpressionNode
    | PositionAttrNode,
    Field(discriminator="type"),
]

OperandNode = Annotated[
    ValueLiteralNode
    | ParameterRefNode
    | VariableRefNode
    | MarketPriceNode
    | IndicatorExpressionNode
    | MathExpressionNode
    | FunctionExpressionNode
    | PositionAttrNode,
    Field(discriminator="type"),
]


def coerce_operand_value(value: Any) -> Any:
    """Coerce raw Python scalars into ValueLiteralNode dictionaries before parsing."""
    if isinstance(value, (bool, int, float, str)):
        return {
            "type": "value",
            "value": value,
            "value_type": _infer_scalar_type(value),
        }
    return value


StopLossType = Literal[
    "none",
    "fixed_pips",
    "fixed_points",
    "percent",
    "atr",
    "indicator",
    "expression",
]

TakeProfitType = Literal[
    "none",
    "fixed_pips",
    "fixed_points",
    "percent",
    "atr",
    "risk_multiple",
    "expression",
]

MoneyManagementType = Literal[
    "fixed_size",
    "fixed_cash",
    "percent_equity",
    "risk_percent",
]


class StopLossSpec(BaseModel):
    """Typed stop-loss sub-DSL specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: StopLossType = Field(default="none", description="Stop-loss calculation mode")
    value: OperandNode | None = Field(
        default=None,
        description="Distance value for fixed_pips, fixed_points, or percent modes",
    )
    period: OperandNode | None = Field(
        default=None,
        description="ATR period operand when type is 'atr'",
    )
    multiplier: OperandNode | None = Field(
        default=None,
        description="ATR multiplier operand when type is 'atr'",
    )
    indicator: IndicatorExpressionNode | None = Field(
        default=None,
        description="Indicator expression providing stop price for 'indicator' mode",
    )
    expression: OperandNode | None = Field(
        default=None,
        description="Arbitrary operand expression when type is 'expression'",
    )

    @field_validator("value", "period", "multiplier", "expression", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)

    @model_validator(mode="after")
    def _validate_mode_fields(self) -> StopLossSpec:
        if (
            self.type in {"fixed_pips", "fixed_points", "percent"}
            and self.value is None
        ):
            msg = f"StopLossSpec type '{self.type}' requires 'value'."
            raise ValueError(msg)
        if self.type == "atr" and (self.period is None or self.multiplier is None):
            msg = "StopLossSpec type 'atr' requires both 'period' and 'multiplier'."
            raise ValueError(msg)
        if self.type == "indicator" and self.indicator is None:
            msg = "StopLossSpec type 'indicator' requires 'indicator'."
            raise ValueError(msg)
        if self.type == "expression" and self.expression is None:
            msg = "StopLossSpec type 'expression' requires 'expression'."
            raise ValueError(msg)
        return self


class TakeProfitSpec(BaseModel):
    """Typed take-profit sub-DSL specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: TakeProfitType = Field(
        default="none",
        description="Take-profit calculation mode",
    )
    value: OperandNode | None = Field(
        default=None,
        description="Distance value for fixed_pips, fixed_points, or percent modes",
    )
    period: OperandNode | None = Field(
        default=None,
        description="ATR period operand when type is 'atr'",
    )
    multiplier: OperandNode | None = Field(
        default=None,
        description="ATR multiplier operand when type is 'atr'",
    )
    multiple: OperandNode | None = Field(
        default=None,
        description="Risk-reward multiple operand when type is 'risk_multiple'",
    )
    expression: OperandNode | None = Field(
        default=None,
        description="Arbitrary operand expression when type is 'expression'",
    )

    @field_validator(
        "value", "period", "multiplier", "multiple", "expression", mode="before"
    )
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)

    @model_validator(mode="after")
    def _validate_mode_fields(self) -> TakeProfitSpec:
        if (
            self.type in {"fixed_pips", "fixed_points", "percent"}
            and self.value is None
        ):
            msg = f"TakeProfitSpec type '{self.type}' requires 'value'."
            raise ValueError(msg)
        if self.type == "atr" and (self.period is None or self.multiplier is None):
            msg = "TakeProfitSpec type 'atr' requires both 'period' and 'multiplier'."
            raise ValueError(msg)
        if self.type == "risk_multiple" and self.multiple is None:
            msg = "TakeProfitSpec type 'risk_multiple' requires 'multiple'."
            raise ValueError(msg)
        if self.type == "expression" and self.expression is None:
            msg = "TakeProfitSpec type 'expression' requires 'expression'."
            raise ValueError(msg)
        return self


class MoneyManagementSpec(BaseModel):
    """Typed position sizing and money management sub-DSL specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    type: MoneyManagementType = Field(
        default="fixed_size",
        description="Position sizing algorithm",
    )
    size: OperandNode | None = Field(
        default=None,
        description="Order quantity or lots when type is 'fixed_size'",
    )
    amount: OperandNode | None = Field(
        default=None,
        description="Cash notional amount when type is 'fixed_cash'",
    )
    percent: OperandNode | None = Field(
        default=None,
        description="Percentage of account equity when type is 'percent_equity'",
    )
    risk_pct: OperandNode | None = Field(
        default=None,
        description="Percentage of equity risked per trade when type is 'risk_percent'",
    )
    max_lots: float | None = Field(
        default=None,
        gt=0.0,
        description="Optional upper cap on position size in lots",
    )

    @field_validator("size", "amount", "percent", "risk_pct", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)

    @model_validator(mode="after")
    def _validate_sizing_fields(self) -> MoneyManagementSpec:
        if self.type == "fixed_size" and self.size is None:
            object.__setattr__(
                self,
                "size",
                ValueLiteralNode(value=1.0, value_type="float"),
            )
        elif self.type == "fixed_cash" and self.amount is None:
            msg = "MoneyManagementSpec type 'fixed_cash' requires 'amount'."
            raise ValueError(msg)
        elif self.type == "percent_equity" and self.percent is None:
            msg = "MoneyManagementSpec type 'percent_equity' requires 'percent'."
            raise ValueError(msg)
        elif self.type == "risk_percent" and self.risk_pct is None:
            msg = "MoneyManagementSpec type 'risk_percent' requires 'risk_pct'."
            raise ValueError(msg)
        logger.debug("Validated MoneyManagementSpec mode=%s", self.type)
        return self


class RiskManagementSpec(BaseModel):
    """Portfolio and strategy-level risk limits."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    max_open_positions: int = Field(
        default=1,
        ge=1,
        description="Maximum concurrent open positions allowed",
    )
    max_daily_loss_pct: float | None = Field(
        default=None,
        gt=0.0,
        description="Maximum daily loss percentage before halting entries",
    )
    max_drawdown_pct: float | None = Field(
        default=None,
        gt=0.0,
        description="Maximum peak-to-trough drawdown percentage limit",
    )
    allow_opposite_signals: bool = Field(
        default=False,
        description="Whether opposite direction signals may open hedged positions",
    )
    default_stop_loss: StopLossSpec = Field(
        default_factory=StopLossSpec,
        description="Strategy-wide default stop-loss specification",
    )
    default_take_profit: TakeProfitSpec = Field(
        default_factory=TakeProfitSpec,
        description="Strategy-wide default take-profit specification",
    )


class BreakevenSpec(BaseModel):
    """Breakeven stop-loss adjustment specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    enabled: bool = Field(default=True, description="Whether breakeven is active")
    trigger_pips: OperandNode = Field(
        default_factory=lambda: ValueLiteralNode(value=20.0, value_type="float"),
        description="Favorable excursion in pips required to trigger breakeven",
    )
    lock_pips: OperandNode = Field(
        default_factory=lambda: ValueLiteralNode(value=0.0, value_type="float"),
        description="Profit offset in pips locked above/below entry price",
    )

    @field_validator("trigger_pips", "lock_pips", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class TrailingStopSpec(BaseModel):
    """Dynamic trailing-stop specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    enabled: bool = Field(default=True, description="Whether trailing stop is active")
    type: Literal["fixed_pips", "atr", "expression"] = Field(
        default="fixed_pips",
        description="Trailing stop distance mode",
    )
    distance: OperandNode = Field(
        default_factory=lambda: ValueLiteralNode(value=25.0, value_type="float"),
        description="Trailing distance operand",
    )
    activation_pips: OperandNode | None = Field(
        default=None,
        description="Optional minimum profit in pips before trailing activates",
    )

    @field_validator("distance", "activation_pips", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class PartialExitSpec(BaseModel):
    """Partial position scale-out rule specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    trigger_pips: OperandNode = Field(
        ...,
        description="Profit distance in pips triggering the partial close",
    )
    close_pct: float = Field(
        ...,
        gt=0.0,
        le=100.0,
        description="Percentage of position quantity to close",
    )

    @field_validator("trigger_pips", mode="before")
    @classmethod
    def _coerce_scalars(cls, v: Any) -> Any:
        return coerce_operand_value(v)


class TradeManagementSpec(BaseModel):
    """Active trade lifecycle management specification."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    breakeven: BreakevenSpec | None = Field(
        default=None,
        description="Optional breakeven rule",
    )
    trailing_stop: TrailingStopSpec | None = Field(
        default=None,
        description="Optional trailing stop rule",
    )
    time_stop_bars: int | None = Field(
        default=None,
        ge=1,
        description="Maximum bars to hold an open position before forced exit",
    )
    partial_exits: tuple[PartialExitSpec, ...] = Field(
        default_factory=tuple,
        description="Ordered partial scale-out rules",
    )


class TradingOptionsSpec(BaseModel):
    """Session, time-filter, and execution constraints."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)

    timezone: str = Field(default="UTC", description="IANA trading session timezone")

    exit_at_end_of_day: bool = Field(
        default=False,
        description="Close all open positions at end of trading day",
    )
    end_of_day_time: str | None = Field(
        default=None,
        description="HH:MM session close timestamp when exit_at_end_of_day is enabled",
    )
    exit_on_friday: bool = Field(
        default=False,
        description="Close all open positions before weekend close on Friday",
    )
    friday_exit_time: str | None = Field(
        default=None,
        description="HH:MM Friday close timestamp",
    )
    limit_time_range: bool = Field(
        default=False,
        description="Restrict new order entries to a daily time window",
    )
    time_range_start: str | None = Field(
        default=None,
        description="HH:MM daily entry window start",
    )
    time_range_end: str | None = Field(
        default=None,
        description="HH:MM daily entry window end",
    )
    max_trades_per_day: int | None = Field(
        default=None,
        ge=1,
        description="Maximum trade entries permitted per calendar day",
    )
    min_distance_from_market_pips: float = Field(
        default=0.0,
        ge=0.0,
        description="Minimum distance in pips from market price for pending orders",
    )


IndicatorExpressionNode.model_rebuild()
MathExpressionNode.model_rebuild()
FunctionExpressionNode.model_rebuild()
StopLossSpec.model_rebuild()
TakeProfitSpec.model_rebuild()
MoneyManagementSpec.model_rebuild()
RiskManagementSpec.model_rebuild()
BreakevenSpec.model_rebuild()
TrailingStopSpec.model_rebuild()
PartialExitSpec.model_rebuild()
TradeManagementSpec.model_rebuild()
