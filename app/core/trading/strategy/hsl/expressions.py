"""Causal HSL expressions over explicitly supplied market contexts.

Description:
    Resolves typed operands using timestamp-bounded feeds and registered blocks.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Shared causal expression execution.
Key Capabilities:
    - FR-hsl-expressions: Reject missing feeds and log block execution.
Python API Usage:
    Construct Expressions inside the shared HSL event evaluator.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

import math
import operator
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, NoReturn

import numpy as np

from app.core.enums import Timeframe
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.blocks.registry import BlockRegistry
from app.core.trading.blocks.series import BarData
from app.core.trading.strategy.contracts import (
    BarUpdateEvent,
    EvaluationEvent,
    LifecycleEvent,
    StrategyContext,
    TickUpdateEvent,
)
from app.core.trading.strategy.hsl import value_models as vm
from app.core.trading.strategy.hsl.library import WizardBlockLibrary

logger = get_logger(__name__)


def fail(message: str, code: str = "HSL_CAPABILITY_UNAVAILABLE") -> NoReturn:
    """Raise a typed diagnostic instead of inventing execution inputs."""
    logger.warning("FR-hsl-expressions: %s", message)
    raise DomainError(code=code, message=message)


def event_time(event: EvaluationEvent) -> int:
    """Return the event's data-availability timestamp in UTC seconds."""
    if isinstance(event, TickUpdateEvent):
        return event.tick.time_msc // 1000
    if isinstance(event, LifecycleEvent):
        return event.time
    return event.bar.time + (event.timeframe.to_seconds() if event.is_bar_close else 0)


def event_kind(event: EvaluationEvent) -> str:
    """Resolve lifecycle kind without an ALL fallback."""
    if isinstance(event, TickUpdateEvent):
        return "on_tick"
    if isinstance(event, LifecycleEvent):
        return event.kind
    return "on_bar_close" if event.is_bar_close else "on_bar_open"


class Expressions:
    """Evaluate one event against isolated variables and causal market feeds."""

    def __init__(
        self,
        context: StrategyContext,
        event: EvaluationEvent,
        parameters: Mapping[str, Any],
        variables: Mapping[str, Any],
        registry: BlockRegistry,
    ) -> None:
        self.context = context
        self.event = event
        self.parameters = parameters
        self.variables = variables
        self.library = WizardBlockLibrary(registry=registry, seed_defaults=False)
        self.cache: dict[str, Any] = {}

    def feed(self, context: vm.EvaluationContext) -> BarData:
        """Select fully closed bars by actual availability, never row alignment."""
        symbol = (
            self.event.symbol if context.symbol == "$current_symbol" else context.symbol
        )
        current_tf = str(getattr(self.event, "timeframe", ""))
        timeframe = (
            current_tf
            if context.timeframe == "$current_timeframe"
            else context.timeframe
        )
        key = (symbol, timeframe)
        bars = self.context.bars_by_context.get(key)
        if bars is None and symbol == self.event.symbol and (timeframe == current_tf):
            bars = self.context.bars
        if bars is None:
            fail(f"Market feed {symbol}/{timeframe} is unavailable", "HSL_MISSING_FEED")
        if not len(bars.timestamps):
            fail(f"Market feed {symbol}/{timeframe} requires UTC timestamps")
        timestamps = np.asarray(bars.timestamps, dtype=np.int64)
        if np.any(timestamps[1:] <= timestamps[:-1]):
            fail("Market feed timestamps must be strictly increasing")
        explicit = self.context.bar_close_times.get(key)
        if explicit is not None:
            closes = np.asarray(explicit, dtype=np.int64)
            if (
                len(closes) != len(timestamps)
                or np.any(closes <= timestamps)
                or np.any(closes[1:] <= closes[:-1])
            ):
                fail("Bar close times must align with opening times")
        else:
            try:
                tf = Timeframe(timeframe)
            except ValueError:
                fail(f"Feed {key} requires explicit bar close times")
            if tf == Timeframe.PERIOD_CURRENT or timeframe == "MN1":
                fail(f"Feed {key} requires explicit bar close times")
            closes = timestamps + tf.to_seconds()
        count = int(np.searchsorted(closes, event_time(self.event), side="right"))
        if not count:
            fail(f"No closed bars available for {symbol}/{timeframe}", "HSL_WARMUP")
        inputs = {
            name: getattr(bars, name)[:count]
            for name in ("open", "high", "low", "close", "volume")
            if bars.has_input(name)
        }
        inputs.update({name: values[:count] for name, values in bars.auxiliary.items()})
        return replace(
            BarData.from_arrays(**inputs, timestamps=timestamps[:count]),
            symbol=symbol,
            timeframe=timeframe,
        )

    def numeric(self, node: vm.OperandNode | None) -> float:
        """Resolve a finite numeric expression for a financial action."""
        if node is None:
            fail("A financial expression is required")
        value = self.value(node)
        if isinstance(value, float) and math.isnan(value):
            fail("Financial expression is warming up", "HSL_WARMUP")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (not math.isfinite(value))
        ):
            fail(
                "Financial expressions must produce finite numbers", "HSL_INVALID_VALUE"
            )
        return float(value)

    def value(self, node: vm.OperandNode, shift_delta: int = 0) -> Any:
        """Evaluate one typed operand using an explicit node dispatcher."""
        dispatch = {
            "value": self._value_literal,
            "parameter": self._value_parameter,
            "variable": self._value_variable,
            "position_attr": self._value_position_attr,
            "math": self._value_math,
            "function": self._value_function,
            "price": self._value_market,
            "indicator": self._value_market,
        }
        return dispatch[node.type](node, shift_delta)

    def _value_literal(self, node: Any, _shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        return node.value

    def _value_parameter(self, node: Any, _shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        return self.parameters[node.name]

    def _value_variable(self, node: Any, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        if shift_delta:
            fail(
                "Previous mutable state requires an explicit history snapshot",
                "HSL_STATE_HISTORY_UNAVAILABLE",
            )
        return self.variables[node.name]

    def _value_position_attr(self, node: Any, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        if shift_delta:
            fail(
                "Previous position state is unavailable",
                "HSL_STATE_HISTORY_UNAVAILABLE",
            )
        positions = [p for p in self.context.positions if p.symbol == self.event.symbol]
        if len(positions) > 1:
            fail("Position attributes require a unique owned position")
        if not positions:
            return "flat" if node.field == "side" else 0.0
        pos = positions[0]
        if node.field == "side":
            return "long" if pos.position_type == 0 else "short"
        if node.field == "bars_held":
            tf = str(getattr(self.event, "timeframe", ""))
            return max(
                0, (event_time(self.event) - pos.time) // Timeframe(tf).to_seconds()
            )
        return {
            "open_price": pos.price_open,
            "unrealized_pnl": pos.profit,
            "size": pos.volume,
        }[node.field]

    def _value_math(self, node: Any, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        left = self.value(node.left, shift_delta)
        if node.operator == "abs":
            return abs(left)
        right = (
            self.value(node.right, shift_delta) if node.right is not None else math.nan
        )
        functions: dict[str, Any] = {
            "add": operator.add,
            "subtract": operator.sub,
            "multiply": operator.mul,
            "divide": lambda a, b: a / b if b else math.nan,
            "min": min,
            "max": max,
        }
        return functions[node.operator](left, right)

    def _value_function(self, node: Any, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        builtin = {"math.min": min, "math.max": max, "math.abs": abs}
        if node.name in builtin:
            function: Any = builtin[node.name]
            return function(*(self.value(arg, shift_delta) for arg in node.args))
        entry = self.library.require(node.name)
        descriptor = self.library.registry.require(entry.registry_id)
        if descriptor.is_class:
            fail("Function expressions require registered pure callables")
        return descriptor.target(*(self.value(arg, shift_delta) for arg in node.args))

    def _price(self, node: Any, bars: Any, index: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        if node.field in ("open", "high", "low", "close", "volume"):
            bars.require_inputs((node.field,))
            return float(getattr(bars, node.field)[index])
        bars.require_inputs(("high", "low", "close"))
        high, low, close = (bars.high[index], bars.low[index], bars.close[index])
        return float(
            {
                "median": (high + low) / 2,
                "typical": (high + low + close) / 3,
                "weighted": (high + low + 2 * close) / 4,
            }[node.field]
        )

    def _indicator(self, node: Any, bars: Any, index: int, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        entry = self.library.require(node.name)
        descriptor = self.library.registry.require(entry.registry_id)
        if not descriptor.spec.is_causal:
            fail(f"Non-causal indicator {entry.registry_id} cannot execute")
        params = {
            key: self.value(value, shift_delta)
            if not isinstance(value, (str, int, float, bool))
            else value
            for key, value in node.params.items()
        }
        instance = descriptor.instantiate(**params)
        if node.inputs:
            arrays = {
                name: getattr(bars, name)
                for name in ("open", "high", "low", "close", "volume")
                if bars.has_input(name)
            }
            for name, operand in node.inputs.items():
                destination = "close" if name == "source" else name
                if not isinstance(operand, vm.MarketPriceNode):
                    fail("Indicator input expressions require a price-series binding")
                selected = self.feed(operand.context)
                if not np.array_equal(selected.timestamps, bars.timestamps):
                    fail("Indicator inputs need identical availability timestamps")
                selected.require_inputs((operand.field,))
                arrays[destination] = getattr(selected, operand.field)
            bars = BarData.from_arrays(**arrays, timestamps=bars.timestamps)
        if index + 1 < instance.required_history():
            return math.nan
        key = node.model_dump_json() + str(params)
        if key not in self.cache:
            logger.debug("FR-hsl-expressions: calculating %s", entry.registry_id)
            self.cache[key] = instance.calculate(bars)
        outputs = self.cache[key]
        output = node.output
        if output == "main" and output not in outputs:
            output = descriptor.spec.outputs[0].name
        if output not in outputs:
            fail(f"Unknown indicator output {node.output}")
        return float(outputs[output].values[index])

    def _value_market(self, node: Any, shift_delta: int) -> Any:
        """Evaluate this typed node using the shared execution context."""
        shift = node.context.shift + shift_delta
        primary_open = (
            isinstance(self.event, BarUpdateEvent)
            and (not self.event.is_bar_close)
            and (node.context.symbol in ("$current_symbol", self.event.symbol))
            and (
                node.context.timeframe
                in ("$current_timeframe", str(self.event.timeframe))
            )
        )
        if isinstance(node, vm.MarketPriceNode) and primary_open and (shift == 0):
            if node.field != "open":
                fail("Only the current open is available on bar-open events")
            if not isinstance(self.event, BarUpdateEvent):
                fail("Current open requires a bar event")
            return float(self.event.bar.open)
        bars = self.feed(node.context)
        index = len(bars) - 1 - shift + (1 if primary_open else 0)
        if index < 0 or index >= len(bars):
            return math.nan
        if isinstance(node, vm.MarketPriceNode):
            return self._price(node, bars, index)
        if primary_open and shift == 0:
            fail("Current indicator values require a closed bar")
        return self._indicator(node, bars, index, shift_delta)
