"""Pydantic data models for the Strategy Module."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class OrderSide(StrEnum):
    """Trading side of an order."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """Order type for execution."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class TradeIntent(BaseModel):
    """Pydantic model representing a strategy's trade decision intent.

    Intents are passed to the risk and execution routing systems for validation
    and order dispatching.
    """

    intent_id: str = Field(
        ..., description="Deterministic unique identifier for this intent."
    )
    decision_id: str = Field(
        ..., description="Links intent to the strategy decision event."
    )
    idempotency_key: str = Field(
        ..., description="Idempotency key to ensure execution safety."
    )
    strategy_id: str = Field(
        ..., description="Unique identifier of the strategy."
    )
    strategy_version: str = Field(
        ..., description="Version of the strategy generating the intent."
    )
    symbol: str = Field(..., description="Asset ticker symbol.")
    side: OrderSide = Field(..., description="Order side: BUY or SELL.")
    order_type: OrderType = Field(
        default=OrderType.MARKET, description="Order type."
    )
    quantity: float = Field(..., gt=0.0, description="Order quantity.")
    price: float | None = Field(
        default=None, description="Limit or stop price if applicable."
    )
    allow_partial_fills: bool = Field(
        default=False, description="Whether partial fills are permitted."
    )
    min_fill_size: float | None = Field(
        default=None, description="Minimum size of a partial fill."
    )
    signal_timestamp: datetime = Field(
        ..., description="Timestamp when the signal was generated."
    )
    stop_loss: float | None = Field(
        default=None, description="Optional stop loss price."
    )
    take_profit: float | None = Field(
        default=None, description="Optional take profit price."
    )
    expiration: datetime | None = Field(
        default=None, description="Optional expiration time for the intent."
    )
    rationale: str | None = Field(
        default=None, description="Text rationale explaining the decision."
    )


class StrategyConfig(BaseModel):
    """Pydantic configuration model for strategy parameters."""

    strategy_id: str = Field(..., description="Unique strategy identifier.")
    strategy_version: str = Field(
        ..., description="Version of the strategy."
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Custom parameters."
    )


class PortfolioState(BaseModel):
    """Pydantic model representing the current state of a portfolio."""

    cash: float = Field(..., description="Available cash balance.")
    positions: dict[str, float] = Field(
        default_factory=dict,
        description="Active positions mapped as Symbol -> Quantity.",
    )
    equity: float = Field(..., description="Total equity value of account.")


class StrategyContext(BaseModel):
    """Pydantic model representing the runtime execution context."""

    current_time: datetime = Field(
        ..., description="Current system execution time."
    )
    portfolio: PortfolioState = Field(
        ..., description="Current state of the portfolio."
    )
    market_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Latest snapshot of market data feeds.",
    )


class StrategyResult(BaseModel):
    """Pydantic model representing the output of a strategy run."""

    strategy_id: str = Field(..., description="Unique strategy identifier.")
    equity_curve: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Historical equity values at each step.",
    )
    metrics: dict[str, Any] = Field(
        default_factory=dict, description="Key performance indicators."
    )
    trade_log: list[TradeIntent] = Field(
        default_factory=list, description="Emitted trade intents."
    )


class StrategyManifest(BaseModel):
    """Pydantic model representing the metadata manifest of a strategy."""

    strategy_id: str = Field(..., description="Unique strategy identifier.")
    strategy_version: str = Field(
        ..., description="Version of the strategy."
    )
    description: str = Field(
        ..., description="Detailed description of the strategy."
    )
    required_symbols: list[str] = Field(
        ..., description="Symbols required by the strategy."
    )
    required_timeframes: list[str] = Field(
        ..., description="Timeframes required by the strategy."
    )
    max_drawdown_limit: float = Field(
        ..., description="Maximum allowed drawdown fraction."
    )
    max_position_size: float = Field(
        ..., description="Maximum allowed position size."
    )
