# ruff: noqa: D105, EM102
"""Strategies contracts module.

Defines StrategyInput and StrategySignal contracts.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import ConfigDict, Field, field_validator, model_validator

from app.services.contracts.base import Contract
from app.utils.normalization import normalize_timestamp


class StrategyInput(Contract):
    """Canonical input for strategy execution.

    Attributes:
        market_data_refs: Hashes or IDs of input DataSlice contracts.
        indicator_refs: Hashes or IDs of computed IndicatorResult contracts.
        portfolio_context: Current portfolio snapshot values.
        config: Strategy hyperparameters and settings.
        start_time: UTC ISO 8601 start boundary of the evaluation window.
        end_time: UTC ISO 8601 end boundary of the evaluation window.
    """

    market_data_refs: list[str] = Field(
        default_factory=list,
        description="References (hashes or IDs) of input market data slices.",
    )
    indicator_refs: list[str] = Field(
        default_factory=list,
        description="References (hashes or IDs) of computed indicators.",
    )
    portfolio_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Current portfolio context snapshot values.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy hyperparameters and settings.",
    )
    start_time: str = Field(..., description="UTC ISO 8601 start boundary.")
    end_time: str = Field(..., description="UTC ISO 8601 end boundary.")

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_boundary_times(cls, v: str) -> str:
        """Validate and normalize evaluation window boundary timestamps.

        Args:
            v: The timestamp string to validate.

        Returns:
            ISO 8601 UTC timestamp string.

        Raises:
            ValueError: If ``v`` cannot be parsed as a valid timestamp.
        """
        try:
            return normalize_timestamp(v).isoformat()
        except Exception as e:
            # Catch broadly: normalize_timestamp may raise app.utils.errors
            # ValidationError (not stdlib ValueError) for bad input strings.
            raise ValueError(f"Invalid boundary timestamp: {v}") from e


class StrategySignal(Contract):
    """Canonical output from a strategy to be reviewed by Risk."""

    # Restrict fields to prevent direct broker-specific placement fields
    model_config = ConfigDict(extra="forbid")

    strategy_id: str = Field(..., description="Strategy identifier.")
    strategy_version: str = Field(..., description="Strategy code version.")
    parameter_hash: str = Field(..., description="Hash of the parameters config used.")
    symbol: str = Field(..., description="Target symbol name.")
    side: Literal["buy", "sell", "exit"] = Field(
        ..., description="Signal side direction."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Signal confidence level."
    )
    validity_window: int = Field(
        ..., gt=0, description="Validity window duration in seconds."
    )
    reason: str = Field(..., description="Human or rule-based reason for generation.")
    evidence_references: list[str] = Field(
        default_factory=list,
        description="Required audit references proving the signal logic.",
    )
    source_data_hash: str = Field(
        ..., description="Hash of the triggering market data state."
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol_non_empty(cls, v: str) -> str:
        """Reject empty or whitespace-only symbol strings.

        Args:
            v: Symbol string to validate.

        Returns:
            Stripped, non-empty symbol string.

        Raises:
            ValueError: If ``v`` is empty or whitespace-only.
        """
        if not v or not v.strip():
            raise ValueError("symbol must be a non-empty string.")
        return v.strip()

    @model_validator(mode="after")
    def validate_signal_integrity(self) -> StrategySignal:
        """Validate evidence references and reject expired signals.

        A signal is considered expired if more seconds have elapsed since
        ``created_at`` than ``validity_window`` allows.  Evidence must be
        non-empty to guarantee audit traceability.

        Returns:
            The validated StrategySignal instance.

        Raises:
            ValueError: If ``evidence_references`` is empty, if
                ``created_at`` cannot be parsed, or if the signal has
                already expired relative to the current UTC time.
        """
        if not self.evidence_references:
            raise ValueError("evidence_references is required and cannot be empty.")
        # Parse created_at and compute elapsed seconds outside any branch
        # that raises ValueError so the expiry check propagates cleanly.
        try:
            created = datetime.fromisoformat(self.created_at)
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            elapsed = (datetime.now(UTC) - created).total_seconds()
        except Exception as e:
            # Broad catch is intentional: datetime.fromisoformat may raise
            # ValueError; timezone arithmetic may raise OverflowError.
            raise ValueError(
                f"Could not evaluate signal expiry from created_at "
                f"'{self.created_at}': {e}"
            ) from e
        if elapsed > self.validity_window:
            raise ValueError(
                f"Signal has expired: {elapsed:.1f}s elapsed, "
                f"validity_window={self.validity_window}s."
            )
        return self


class RuntimeMode(StrEnum):
    """Permitted execution environments for strategy evaluation."""

    SIMULATOR = "SIMULATOR"
    PAPER = "PAPER"
    LIVE = "LIVE"


class Direction(StrEnum):
    """Trade direction."""

    LONG = "LONG"
    SHORT = "SHORT"


class IntentAction(StrEnum):
    """Broker-neutral proposal action."""

    OPEN = "OPEN"
    CLOSE = "CLOSE"
    MODIFY = "MODIFY"
    PARTIAL_CLOSE = "PARTIAL_CLOSE"
    CANCEL_PENDING = "CANCEL_PENDING"


class EntryType(StrEnum):
    """Order-entry classification independent of a particular broker API."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    REVERSE = "REVERSE"


@dataclass(frozen=True, slots=True)
class Bar:
    """A completed canonical OHLCV bar.

    ``open_time`` must be timezone-aware.  The data module is responsible for
    normalizing timestamps and supplying only bars that are complete at the
    strategy evaluation point.
    """

    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.open_time.tzinfo is None:
            raise ValueError("Bar.open_time must be timezone-aware.")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("Bar.high must be at least open, close, and low.")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("Bar.low must be at most open, close, and high.")
        if self.volume < 0:
            raise ValueError("Bar.volume cannot be negative.")


@dataclass(frozen=True, slots=True)
class QuoteSnapshot:
    """Executable bid/ask quote and instrument precision at evaluation time."""

    bid: float
    ask: float
    point_size: float

    def __post_init__(self) -> None:
        if self.bid <= 0 or self.ask <= 0:
            raise ValueError("Quote prices must be positive.")
        if self.ask < self.bid:
            raise ValueError("Quote ask must be greater than or equal to bid.")
        if self.point_size <= 0:
            raise ValueError("Quote point_size must be positive.")

    def entry_price(self, direction: Direction) -> float:
        """Return the natural executable market-entry price for a direction."""
        return self.ask if direction is Direction.LONG else self.bid

    def exit_price(self, direction: Direction) -> float:
        """Return the natural executable market-exit price for a position."""
        return self.bid if direction is Direction.LONG else self.ask


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    """Minimal account data needed for strategy-side sizing formulas.

    The value is advisory only.  The Risk Governor remains the authority for
    final quantity, margin approval, portfolio limits, and execution routing.
    """

    balance: float
    volume_min: float = 0.01
    volume_max: float = 100.0
    volume_step: float = 0.01

    def __post_init__(self) -> None:
        if self.balance < 0:
            raise ValueError("Account balance cannot be negative.")
        if self.volume_min <= 0 or self.volume_max < self.volume_min:
            raise ValueError("Invalid account volume bounds.")
        if self.volume_step <= 0:
            raise ValueError("Account volume_step must be positive.")


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    """Read-only view of an open broker/portfolio position."""

    position_id: str
    symbol: str
    direction: Direction
    quantity: float
    strategy_id: str | None = None
    magic_number: int | None = None
    entry_price: float | None = None
    stop_loss_price: float | None = None
    profit_target_price: float | None = None
    comment: str = ""


@dataclass(frozen=True, slots=True)
class PendingOrderSnapshot:
    """Read-only view of a broker pending order."""

    order_id: str
    symbol: str
    direction: Direction
    entry_type: EntryType
    price: float
    quantity: float
    strategy_id: str | None = None
    magic_number: int | None = None
    comment: str = ""


@dataclass(frozen=True, slots=True)
class MarketContext:
    """Everything a strategy may read during one deterministic evaluation.

    ``bars`` is the main chart retained for backwards compatibility.  Use
    ``chart_bars`` for multi-timeframe/multi-symbol strategy inputs.  ``features``
    is intentionally extensible for normalized external calculations such as a
    ZigZag extreme sequence; feature producers live in the data/indicator layer.
    """

    runtime_mode: RuntimeMode
    symbol: str
    timeframe: str
    as_of: datetime
    bars: Sequence[Bar]
    positions: Sequence[PositionSnapshot] = ()
    features: Mapping[str, object] = field(default_factory=dict)
    chart_bars: Mapping[str, Sequence[Bar]] = field(default_factory=dict)
    quote: QuoteSnapshot | None = None
    account: AccountSnapshot | None = None
    pending_orders: Sequence[PendingOrderSnapshot] = ()

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None:
            raise ValueError("MarketContext.as_of must be timezone-aware.")
        if not self.symbol:
            raise ValueError("MarketContext.symbol cannot be empty.")
        if not self.timeframe:
            raise ValueError("MarketContext.timeframe cannot be empty.")
        for chart in (self.bars, *self.chart_bars.values()):
            if any(bar.open_time > self.as_of for bar in chart):
                raise ValueError("Context cannot contain bars from after as_of.")

    @property
    def signal_bar(self) -> Bar:
        """Return the latest completed main-chart bar."""
        if not self.bars:
            raise ValueError("A strategy needs at least one completed bar.")
        return self.bars[-1]

    def bars_for_chart(self, chart_name: str = "main") -> Sequence[Bar]:
        """Return main or named secondary-chart bars."""
        if chart_name == "main":
            return self.bars
        try:
            return self.chart_bars[chart_name]
        except KeyError as error:
            raise KeyError(f"No chart bars supplied for {chart_name!r}.") from error


@dataclass(frozen=True, slots=True)
class ProtectionRequest:
    """Strategy-proposed protection and management changes.

    A distance is relative to the intended entry price; an absolute price is
    used for amendments to existing positions.  Clear flags allow translations
    of MQL5 calls that intentionally remove a previously set TP/SL.
    """

    stop_loss_distance: float | None = None
    profit_target_distance: float | None = None
    trailing_distance: float | None = None
    trailing_activation_distance: float | None = None
    time_exit_bars: int | None = None
    advanced_partial_exit_plan: Mapping[str, object] | None = None
    stop_loss_price: float | None = None
    profit_target_price: float | None = None
    clear_stop_loss: bool = False
    clear_profit_target: bool = False


@dataclass(frozen=True, slots=True)
class TradeIntent:
    """Idempotent broker-neutral request for Risk Governor and execution review."""

    intent_id: str
    strategy_id: str
    signal_time: datetime
    action: IntentAction
    symbol: str
    direction: Direction
    entry_type: EntryType | None
    order_comment: str
    magic_number: int
    protection: ProtectionRequest = field(default_factory=ProtectionRequest)
    target_position_ids: tuple[str, ...] = ()
    target_pending_order_ids: tuple[str, ...] = ()
    requested_quantity: float | None = None
    limit_price: float | None = None
    stop_price: float | None = None
    sizing_hint: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SignalSet:
    """The four canonical SQX-style boolean signal outputs."""

    long_entry: bool = False
    short_entry: bool = False
    long_exit: bool = False
    short_exit: bool = False


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """Complete deterministic result of a strategy evaluation."""

    signal_time: datetime | None
    signals: SignalSet
    intents: tuple[TradeIntent, ...]
    diagnostics: tuple[str, ...] = ()
