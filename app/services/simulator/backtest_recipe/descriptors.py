"""Registered strategy descriptors for the canonical backtest recipe.

Each descriptor declares exactly what the recipe needs to drive one registered
Strategy evaluator through a canonical Simulation run: its configuration
parameters, the warm-up window those parameters imply, and the mapping from the
evaluator's own signal vocabulary onto the recipe's entry/exit actions.

An evaluator is ``runnable`` only when the recipe can honour it end to end with
no invented behaviour. Two conditions block a strategy today:

* it consumes Indicators-owned series (EMA, RSI, ATR), which the recipe does not
  yet supply; or
* it publishes no exit vocabulary, so a position opened on its signal could only
  ever be closed by end-of-run liquidation.

Blocked descriptors stay registered and carry their exact reason so the boundary
presents the real catalogue and never silently drops a strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

_EVALUATOR_MODULE_ROOT = "app.services.strategy.evaluators"


@dataclass(frozen=True, slots=True)
class StrategyParameter:
    """One declared strategy configuration parameter."""

    name: str
    label: str
    kind: Literal["integer", "decimal"]
    default: str
    minimum: str | None = None
    maximum: str | None = None
    #: Whether this parameter's value contributes to the warm-up bar requirement.
    warmup: bool = False


@dataclass(frozen=True, slots=True)
class StrategyDescriptor:
    """One registered evaluator and its recipe binding."""

    evaluator_name: str
    strategy_id: str
    strategy_version: str
    label: str
    parameters: tuple[StrategyParameter, ...]
    long_entry_signals: frozenset[str]
    short_entry_signals: frozenset[str]
    long_exit_signals: frozenset[str]
    short_exit_signals: frozenset[str]
    required_indicators: tuple[str, ...]
    runnable: bool
    unavailable_reason: str | None

    @property
    def module_path(self) -> str:
        """Return the evaluator's approved module path.

        Returns:
            Dotted module path under the approved evaluator root.
        """
        return f"{_EVALUATOR_MODULE_ROOT}.{self.evaluator_name}"

    def warmup_bars(self, parameters: dict[str, object]) -> int:
        """Return the warm-up bar count implied by resolved parameters.

        Args:
            parameters: Resolved parameter values for this strategy.

        Returns:
            One more than the largest warm-up-contributing parameter value, so
            the window always satisfies evaluators that compare a value against
            its own previous bar. Two when no parameter contributes.
        """
        values = [
            int(str(parameters[item.name]))
            for item in self.parameters
            if item.warmup and item.name in parameters
        ]
        return (max(values) + 1) if values else 2


def _periods() -> tuple[StrategyParameter, ...]:
    """Return the shared moving-average period parameter set.

    Returns:
        Fast, slow, and filter moving-average parameters.
    """
    return (
        StrategyParameter(
            name="fast_ma_period",
            label="Fast MA period",
            kind="integer",
            default="20",
            minimum="2",
            warmup=True,
        ),
        StrategyParameter(
            name="slow_ma_period",
            label="Slow MA period",
            kind="integer",
            default="50",
            minimum="2",
            warmup=True,
        ),
        StrategyParameter(
            name="filter_ma_period",
            label="Filter MA period",
            kind="integer",
            default="200",
            minimum="2",
            warmup=True,
        ),
    )


def _rsi_parameters() -> tuple[StrategyParameter, ...]:
    """Return the shared RSI threshold parameter set.

    Returns:
        RSI period and oversold/overbought threshold parameters.
    """
    return (
        StrategyParameter(
            name="rsi_period",
            label="RSI period",
            kind="integer",
            default="14",
            minimum="2",
            warmup=True,
        ),
        StrategyParameter(
            name="oversold", label="Oversold", kind="decimal", default="30"
        ),
        StrategyParameter(
            name="overbought", label="Overbought", kind="decimal", default="70"
        ),
    )


_NEEDS_INDICATORS = (
    "This evaluator consumes Indicators-owned series, which the backtest recipe "
    "does not yet supply."
)
_NO_EXITS = (
    "This evaluator publishes no exit signal, so an opened position could only "
    "be closed by end-of-run liquidation."
)

_DESCRIPTORS: tuple[StrategyDescriptor, ...] = (
    StrategyDescriptor(
        evaluator_name="naive_ma_trend_incremental",
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        label="Naive MA Trend (incremental)",
        parameters=_periods(),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset({"LONG_EXIT"}),
        short_exit_signals=frozenset({"SHORT_EXIT"}),
        required_indicators=(),
        runnable=True,
        unavailable_reason=None,
    ),
    StrategyDescriptor(
        evaluator_name="naive_ma_trend",
        strategy_id="naive-ma-trend-official",
        strategy_version="1.0.0",
        label="Naive MA Trend (official EMA series)",
        parameters=_periods(),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset({"LONG_EXIT"}),
        short_exit_signals=frozenset({"SHORT_EXIT"}),
        required_indicators=("ema",),
        runnable=False,
        unavailable_reason=_NEEDS_INDICATORS,
    ),
    StrategyDescriptor(
        evaluator_name="white_fairy",
        strategy_id="white-fairy",
        strategy_version="1.0.0",
        label="White Fairy (RSI reversal)",
        parameters=_rsi_parameters(),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=("rsi",),
        runnable=False,
        unavailable_reason=_NEEDS_INDICATORS,
    ),
    StrategyDescriptor(
        evaluator_name="decomposing_trade",
        strategy_id="decomposing-trade",
        strategy_version="1.0.0",
        label="Decomposing Trade (RSI)",
        parameters=_rsi_parameters(),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=("rsi",),
        runnable=False,
        unavailable_reason=_NEEDS_INDICATORS,
    ),
    StrategyDescriptor(
        evaluator_name="sqx_breakout_atr_trailing",
        strategy_id="sqx-breakout-atr-trailing",
        strategy_version="1.0.0",
        label="SQX Breakout with ATR Trailing",
        parameters=(
            StrategyParameter(
                name="breakout_lookback",
                label="Breakout lookback",
                kind="integer",
                default="20",
                minimum="2",
                warmup=True,
            ),
        ),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=("atr",),
        runnable=False,
        unavailable_reason=_NEEDS_INDICATORS,
    ),
    StrategyDescriptor(
        evaluator_name="harriet_hedging",
        strategy_id="harriet-hedging",
        strategy_version="1.0.0",
        label="Harriet Hedging",
        parameters=(
            StrategyParameter(
                name="pip_multiplier",
                label="Pip multiplier",
                kind="decimal",
                default="10",
            ),
            StrategyParameter(
                name="higher_min_distance_pips",
                label="Higher minimum distance (pips)",
                kind="decimal",
                default="20",
            ),
            StrategyParameter(
                name="lower_min_distance_pips",
                label="Lower minimum distance (pips)",
                kind="decimal",
                default="20",
            ),
        ),
        long_entry_signals=frozenset({"LONG_ENTRY"}),
        short_entry_signals=frozenset({"SHORT_ENTRY"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=(),
        runnable=False,
        unavailable_reason=_NO_EXITS,
    ),
    StrategyDescriptor(
        evaluator_name="market_structure",
        strategy_id="market-structure",
        strategy_version="1.0.0",
        label="Market Structure Break",
        parameters=(),
        long_entry_signals=frozenset({"BULLISH_STRUCTURE_BREAK"}),
        short_entry_signals=frozenset({"BEARISH_STRUCTURE_BREAK"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=(),
        runnable=False,
        unavailable_reason=_NO_EXITS,
    ),
    StrategyDescriptor(
        evaluator_name="random_walk",
        strategy_id="random-walk",
        strategy_version="1.0.0",
        label="Random Walk Basket",
        parameters=(
            StrategyParameter(
                name="buy_magic_number",
                label="Buy magic number",
                kind="integer",
                default="1",
            ),
            StrategyParameter(
                name="sell_magic_number",
                label="Sell magic number",
                kind="integer",
                default="2",
            ),
        ),
        long_entry_signals=frozenset({"LONG_BASKET_TRIGGER"}),
        short_entry_signals=frozenset({"SHORT_BASKET_TRIGGER"}),
        long_exit_signals=frozenset(),
        short_exit_signals=frozenset(),
        required_indicators=(),
        runnable=False,
        unavailable_reason=_NO_EXITS,
    ),
)

_BY_ID = {descriptor.strategy_id: descriptor for descriptor in _DESCRIPTORS}


def get_backtest_strategy_descriptors() -> tuple[StrategyDescriptor, ...]:
    """Return every registered backtest strategy descriptor.

    Returns:
        Immutable descriptor tuple in stable registration order.
    """
    return _DESCRIPTORS


def get_backtest_strategy_descriptor(strategy_id: str) -> StrategyDescriptor:
    """Return one registered descriptor by its stable strategy identity.

    Args:
        strategy_id: Registered strategy identifier.

    Returns:
        The matching descriptor.

    Raises:
        ValueError: If the identifier is not registered.
    """
    descriptor = _BY_ID.get(strategy_id)
    if descriptor is None:
        message = f"unknown backtest strategy: {strategy_id}"
        raise ValueError(message)
    return descriptor


def resolve_strategy_parameters(
    descriptor: StrategyDescriptor, overrides: dict[str, object]
) -> dict[str, object]:
    """Resolve declared parameters from defaults and caller overrides.

    Args:
        descriptor: Registered strategy descriptor.
        overrides: Caller-supplied parameter values.

    Returns:
        Complete normalized parameter mapping for the evaluator.

    Raises:
        ValueError: If an override is unknown or not a valid declared value.
    """
    declared = {item.name: item for item in descriptor.parameters}
    unknown = set(overrides) - set(declared)
    if unknown:
        message = f"unknown strategy parameters: {sorted(unknown)}"
        raise ValueError(message)
    resolved: dict[str, object] = {}
    for name, item in declared.items():
        raw = str(overrides.get(name, item.default))
        if item.kind == "integer":
            try:
                value: object = int(raw)
            except ValueError as error:
                message = f"{name} must be an integer"
                raise ValueError(message) from error
        else:
            value = raw
        if item.minimum is not None and float(str(value)) < float(item.minimum):
            message = f"{name} must be at least {item.minimum}"
            raise ValueError(message)
        if item.maximum is not None and float(str(value)) > float(item.maximum):
            message = f"{name} must be at most {item.maximum}"
            raise ValueError(message)
        resolved[name] = value
    return resolved


__all__ = (
    "StrategyDescriptor",
    "StrategyParameter",
    "get_backtest_strategy_descriptor",
    "get_backtest_strategy_descriptors",
    "resolve_strategy_parameters",
)
