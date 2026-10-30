"""Validated indicator recipes evaluated through shared comparison algorithms."""

from __future__ import annotations

import math
import operator
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any

import numpy as np

from app.core.trading.blocks.series import (
    COMPUTED_PRICE_INPUTS,
    BarData,
    computed_price,
)
from app.include.blocks.comparisons.equals import equals
from app.include.blocks.comparisons.is_greater import is_greater
from app.include.blocks.comparisons.is_greater_or_equal import is_greater_or_equal
from app.include.blocks.comparisons.is_lower import is_lower
from app.include.blocks.comparisons.is_lower_or_equal import is_lower_or_equal
from app.include.blocks.comparisons.not_equals import not_equals

_COMPARISONS: Mapping[str, Callable[..., Any]] = MappingProxyType(
    {
        "condition.is_greater": is_greater,
        "condition.is_lower": is_lower,
        "condition.is_greater_or_equal": is_greater_or_equal,
        "condition.is_lower_or_equal": is_lower_or_equal,
        "condition.equals": equals,
        "condition.not_equals": not_equals,
    }
)
_ARITHMETIC: Mapping[str, Callable[..., Any]] = MappingProxyType(
    {
        "add": operator.add,
        "sub": operator.sub,
        "mul": operator.mul,
        "div": operator.truediv,
        "neg": operator.neg,
        "abs": abs,
    }
)
_MIN_BOOLEAN_NODE_SIZE = 2
_MARKET_FIELDS = frozenset(("open", "high", "low", "close", "volume"))


def _offset(offset: Any, shift: int) -> int:
    result = offset["absolute"] if isinstance(offset, Mapping) else shift + offset
    if type(result) is not int or result < 0:
        raise ValueError("Composition reads require nonnegative historical shifts")
    return result


def _binding(value: Any, config: Mapping[str, Any]) -> Any:
    if value[0] == "parameter":
        return config[value[1]]
    if value[0] == "constant":
        return value[1]
    raise ValueError("Invalid calculation parameter binding")


def _validate_read(
    expr: Any, recipe: Mapping[str, Any], calculations: Mapping[str, Any]
) -> None:
    if expr[0] == "output":
        node = recipe["nodes"][expr[1]]
        cls = calculations[node["indicator"]]
        if expr[2] not in {p.name for p in cls.spec.outputs}:
            raise ValueError(f"Unknown output: {expr[2]}")
        _offset(expr[3], 0)
    elif expr[0] == "external":
        if not isinstance(expr[1], str) or not expr[1]:
            raise ValueError("External reads require a named aligned feed")
        _offset(expr[2], 0)
    else:
        if expr[1] not in _MARKET_FIELDS:
            raise ValueError("Unknown market field")
        _offset(expr[2], 0)
    digits = expr[-1]
    if digits is not None and (type(digits) is not int or digits < 0):
        raise ValueError("Read precision must be a nonnegative integer")


def _validate_shape(expr: Any) -> None:
    if not isinstance(expr, (list, tuple)) or not expr:
        raise ValueError("Malformed composition expression")
    kind = expr[0]
    sizes = {
        "constant": 2,
        "parameter": 2,
        "output": 5,
        "market": 4,
        "external": 4,
        "comparison": 4,
        "not": 2,
    }
    expected = sizes.get(kind)
    if kind == "arithmetic" and len(expr) < _MIN_BOOLEAN_NODE_SIZE:
        raise ValueError("Arithmetic compositions require an operator")
    if kind == "arithmetic":
        expected = 3 if expr[1] in ("neg", "abs") else 4
    if expected is not None and len(expr) != expected:
        raise ValueError(f"Invalid arity for {kind}")
    if kind in ("all", "any") and len(expr) < _MIN_BOOLEAN_NODE_SIZE:
        raise ValueError("Boolean compositions require operands")


def _validate_expression(
    expr: Any,
    recipe: Mapping[str, Any],
    calculations: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    _validate_shape(expr)
    kind = expr[0]
    if kind in ("output", "market", "external"):
        _validate_read(expr, recipe, calculations)
    elif kind == "parameter":
        if expr[1] not in config:
            raise ValueError(f"Unknown composition parameter: {expr[1]}")
    elif kind in ("comparison", "arithmetic"):
        table = _COMPARISONS if kind == "comparison" else _ARITHMETIC
        if expr[1] not in table:
            raise ValueError(f"Unknown {kind} operation")
    elif kind not in ("constant", "all", "any", "not"):
        raise ValueError(f"Unknown expression node: {kind}")
    children = _expression_children(expr)
    for child in children:
        _validate_expression(child, recipe, calculations, config)


def _expression_children(expr: Any) -> Any:
    if expr[0] in ("comparison", "arithmetic"):
        return expr[2:]
    if expr[0] in ("all", "any", "not"):
        return expr[1:]
    return ()


def _read_inputs(expr: Any) -> set[str]:
    fields = {expr[1]} if expr[0] in ("market", "external") else set()
    for child in _expression_children(expr):
        fields.update(_read_inputs(child))
    return fields


def _output_reads(expr: Any) -> set[tuple[str, str]]:
    fields = {(expr[1], expr[2])} if expr[0] == "output" else set()
    for child in _expression_children(expr):
        fields.update(_output_reads(child))
    return fields


def _lookback(expr: Any, shift: int) -> int:
    if expr[0] == "output":
        return _offset(expr[3], shift)
    if expr[0] in ("market", "external"):
        return _offset(expr[2], shift)
    return max(
        (_lookback(child, shift) for child in _expression_children(expr)), default=0
    )


@dataclass(frozen=True)
class _Evaluation:
    outputs: Mapping[str, Any]
    bars: BarData
    config: Mapping[str, Any]

    def _read(self, values: Any, offset: Any, digits: int | None) -> float:
        index = _offset(offset, self.config.get("shift", 0))
        if hasattr(values, "get") and not isinstance(values, np.ndarray):
            value = float(values.get(index))
        else:
            value = float(values[-1 - index]) if index < len(values) else math.nan
        return (
            round(value, digits)
            if digits is not None and math.isfinite(value)
            else value
        )

    def _leaf(self, expr: Any) -> Any:
        kind = expr[0]
        if kind == "constant":
            return expr[1]
        if kind == "parameter":
            return self.config[expr[1]]
        if kind == "output":
            return self._read(self.outputs[expr[1]][expr[2]], expr[3], expr[4])
        self.bars.require_inputs((expr[1],))
        values = (
            getattr(self.bars, expr[1])
            if expr[0] == "market"
            else self.bars.input(expr[1], required=True)
        )
        return self._read(values, expr[2], expr[3])

    def evaluate(self, expr: Any) -> Any:
        kind = expr[0]
        if kind in ("constant", "parameter", "output", "market", "external"):
            result = self._leaf(expr)
        elif kind == "comparison":
            # Only read nodes apply rounding: raw chart prices/levels stay raw.
            result = _COMPARISONS[expr[1]](
                self.evaluate(expr[2]), self.evaluate(expr[3]), precision=308
            )
        elif kind == "all":
            result = all(self.evaluate(child) for child in expr[1:])
        elif kind == "any":
            result = any(self.evaluate(child) for child in expr[1:])
        elif kind == "not":
            result = not self.evaluate(expr[1])
        else:
            try:
                result = _ARITHMETIC[expr[1]](
                    *(self.evaluate(child) for child in expr[2:])
                )
            except ZeroDivisionError:
                result = math.nan
        return result


@dataclass(frozen=True)
class CompositionExecutor:
    """One recipe pinned to concrete calculation classes for its catalog revision."""

    definition: Any
    config_model: Any
    calculations: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Freeze algorithm references so reloads cannot mutate old snapshots."""
        object.__setattr__(
            self, "calculations", MappingProxyType(dict(self.calculations))
        )

    def validate(self, config: Mapping[str, Any]) -> None:
        """Validate references and configuration before publication."""
        recipe = self.definition.recipe
        for node in recipe["nodes"].values():
            cls = self.calculations[self._selected_id(node, config)]
            cls(
                **{
                    key: _binding(value, config)
                    for key, value in node["parameters"].items()
                }
            )
        _validate_expression(recipe["expression"], recipe, self.calculations, config)

    @staticmethod
    def _selected_id(node: Any, config: Mapping[str, Any]) -> str:
        if node.get("alternatives"):
            return str(node["alternatives"][str(config[node["select_parameter"]])])
        return str(node["indicator"])

    def _source(self, bars: BarData, node: Any, config: Mapping[str, Any]) -> BarData:
        if node.get("input_field") is None:
            return bars
        values = computed_price(bars, _binding(node["input_field"], config))
        fields = {
            name: getattr(bars, name) for name in _MARKET_FIELDS if bars.has_input(name)
        }
        fields.update(bars.auxiliary)
        fields["close"] = values
        fields["timestamps"] = bars.timestamps if len(bars.timestamps) else None
        if node.get("output_hint") in ("highest", "lowest"):
            fields["high"] = values
            fields["low"] = values
        return replace(
            BarData.from_arrays(**fields),
            symbol=bars.symbol,
            timeframe=bars.timeframe,
            dataset_revision=bars.dataset_revision,
        )

    def required_history(self, **parameters: Any) -> int:
        """Resolve indicator warmup plus the recipe's historical reads."""
        config = self.config_model(**parameters).model_dump()
        histories = []
        for node in self.definition.recipe["nodes"].values():
            cls = self.calculations[self._selected_id(node, config)]
            settings = {
                name: _binding(value, config)
                for name, value in node["parameters"].items()
            }
            histories.append(cls(**settings).required_history())
        return max(histories, default=1) + _lookback(
            self.definition.recipe["expression"], config.get("shift", 0)
        )

    def required_inputs(self, **parameters: Any) -> tuple[str, ...]:
        """Resolve market and external inputs for the selected configuration."""
        config = self.config_model(**parameters).model_dump()
        required = set(_read_inputs(self.definition.recipe["expression"]))
        for node in self.definition.recipe["nodes"].values():
            cls = self.calculations[self._selected_id(node, config)]
            settings = {
                name: _binding(value, config)
                for name, value in node["parameters"].items()
            }
            fields = set(cls(**settings).required_inputs())
            if node.get("input_field") is not None:
                code = _binding(node["input_field"], config)
                fields.discard("close")
                if node.get("output_hint") in ("highest", "lowest"):
                    fields.difference_update(("high", "low"))
                fields.update(COMPUTED_PRICE_INPUTS[code])
            required.update(fields)
        return tuple(sorted(required))

    def __call__(self, bars: BarData, **parameters: Any) -> bool:
        """Calculate dependencies once, then evaluate the condition."""
        config = self.config_model(**parameters).model_dump()
        bars.require_inputs(self.required_inputs(**config))
        outputs: dict[str, Any] = {}
        cache: dict[tuple[Any, ...], Any] = {}
        for key, node in self.definition.recipe["nodes"].items():
            block_id = self._selected_id(node, config)
            cls = self.calculations[block_id]
            kwargs = {k: _binding(v, config) for k, v in node["parameters"].items()}
            cache_key = (
                block_id,
                repr(sorted(kwargs.items())),
                repr(node.get("input_field")),
            )
            if cache_key not in cache:
                source = self._source(bars, node, config)
                indicator = cls(**kwargs)
                source.require_inputs(indicator.required_inputs())
                cache[cache_key] = indicator.calculate(source)
            outputs[key] = cache[cache_key]
        return self.evaluate_outputs(outputs, bars, **config)

    def evaluate_outputs(
        self, outputs: Mapping[str, Any], bars: BarData, **parameters: Any
    ) -> bool:
        """Evaluate supplied outputs for shared caches or tests."""
        config = self.config_model(**parameters).model_dump()
        for node_key, port in _output_reads(self.definition.recipe["expression"]):
            if len(outputs[node_key][port]) != len(bars.prices):
                raise ValueError(f"Output {node_key}.{port} must align with bars")
        result = _Evaluation(outputs, bars, config).evaluate(
            self.definition.recipe["expression"]
        )
        return (
            bool(result)
            if isinstance(result, (bool, np.bool_))
            else math.isfinite(result) and bool(result)
        )


__all__ = ["CompositionExecutor"]
