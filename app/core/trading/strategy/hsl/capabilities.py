"""Executable HSL capability validation and reproducible block bindings.

Description:
    Checks registry contracts beyond JSON shape and fingerprints executable code.
Purpose:
    FEAT-WIZARD-HSL-LANGUAGE: Fail-closed compilation and stale-plan detection.
Key Capabilities:
    - FR-hsl-capabilities: Reject unsupported nodes and log compilation bindings.
Python API Usage:
    Call validate_capabilities before compiling a strategy.
CLI Usage:
    uv run pytest tests/core/trading/strategy --no-cov
"""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Iterator, Mapping
from dataclasses import fields, is_dataclass, replace
from types import CodeType
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.blocks.composition_runtime import CompositionExecutor
from app.core.trading.blocks.metadata import ExecutionKind
from app.core.trading.blocks.registry import BlockDescriptor, BlockRegistry
from app.core.trading.strategy.hsl import value_models as vm
from app.core.trading.strategy.hsl.library import WizardBlockLibrary
from app.core.trading.strategy.hsl.models import (
    BlockConditionNode,
    HSLStrategyDocument,
    ParameterSpec,
    VariableSpec,
)

logger = get_logger(__name__)
PERCENT = 100


def walk(value: Any) -> Iterator[BaseModel]:
    """Traverse typed nodes without interpreting metadata as executable code."""
    if isinstance(value, BaseModel):
        yield value
        for name in type(value).model_fields:
            if name != "metadata":
                yield from walk(getattr(value, name))
    elif isinstance(value, Mapping):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from walk(child)


def _json_value(value: Any) -> Any:
    """Normalize immutable registry metadata for deterministic hashing."""
    if is_dataclass(value) and (not isinstance(value, type)):
        return {item.name: getattr(value, item.name) for item in fields(value)}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (set, frozenset, tuple)):
        return sorted(value, key=str)
    raise TypeError(f"Unsupported fingerprint metadata: {type(value).__name__}")


def _code_bytes(code: CodeType) -> bytes:
    """Hash stable bytecode fields without marshal's mutable string-intern flags."""

    def encode(value: Any) -> Any:
        if isinstance(value, CodeType):
            return {
                "code": value.co_code.hex(),
                "constants": value.co_consts,
                "names": value.co_names,
                "variables": value.co_varnames,
                "free": value.co_freevars,
                "cells": value.co_cellvars,
                "arguments": (
                    value.co_argcount,
                    value.co_posonlyargcount,
                    value.co_kwonlyargcount,
                ),
                "flags": value.co_flags,
            }
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, frozenset):
            return sorted(value, key=repr)
        return repr(value)

    return json.dumps(code, default=encode, sort_keys=True).encode()


def fingerprint(descriptor: BlockDescriptor) -> str:
    """Hash executable source and schema, not just the display identifier."""
    original = descriptor.target
    target = (
        original
        if inspect.isfunction(original) or inspect.isclass(original)
        else type(original)
    )
    try:
        source = inspect.getsource(inspect.getmodule(target) or target).encode()
    except OSError, TypeError:
        code = getattr(target, "__code__", None)
        if code is None:
            code = getattr(getattr(target, "calculate", None), "__code__", None)
        if code is None:
            raise DomainError(
                code="HSL_UNPINNABLE_BLOCK",
                message=f"Cannot fingerprint {descriptor.spec.id}",
            ) from None
        source = _code_bytes(code)
    implementation = getattr(target, "calculate", target)
    if isinstance(original, CompositionExecutor):
        implementation = original.__call__
    visited: set[int] = set()

    def dependencies(function: Any) -> bytes:
        if inspect.ismethod(function):
            function = function.__func__
        if id(function) in visited or not inspect.isfunction(function):
            return b""
        visited.add(id(function))
        code = function.__code__
        payload = _code_bytes(code)
        for name in code.co_names:
            child = function.__globals__.get(name)
            if inspect.isfunction(child) and child.__module__.startswith("app."):
                payload += dependencies(child)
        return payload

    source += dependencies(implementation)
    metadata = _json_value(descriptor.spec)
    metadata["composition"] = descriptor.composition
    source += json.dumps(metadata, sort_keys=True, default=_json_value).encode()
    schema = json.dumps(
        dict(descriptor.parameter_schema),
        sort_keys=True,
        default=lambda value: (
            dict(value) if isinstance(value, Mapping) else list(value)
        ),
    )
    return hashlib.sha256(
        source + descriptor.spec.version.encode() + schema.encode()
    ).hexdigest()


def _validate_composition_bindings(
    descriptor: BlockDescriptor, registry: BlockRegistry
) -> None:
    """Reject a recipe still bound to an older dependency after a registry reload."""
    executor = descriptor.target
    if not isinstance(executor, CompositionExecutor):
        return
    for identifier, calculation in executor.calculations.items():
        current = registry.require(identifier)
        bound = replace(
            current,
            target=calculation,
            spec=calculation.spec,
            parameter_schema=calculation.get_parameter_schema(),
        )
        if fingerprint(bound) != fingerprint(current):
            raise DomainError(
                code="HSL_STALE_COMPOSITION",
                message="Recipe owner must be reloaded after dependency changes",
            )


def block_fingerprints(
    document: HSLStrategyDocument, registry: BlockRegistry
) -> dict[str, str]:
    """Resolve actual registry IDs and pin all transitive declared dependencies."""
    library = WizardBlockLibrary(registry=registry, seed_defaults=False)
    result: dict[str, str] = {}

    def bind(identifier: str) -> None:
        entry = library.require(identifier)
        descriptor = registry.require(entry.registry_id)
        if entry.registry_id in result:
            return
        _validate_composition_bindings(descriptor, registry)
        result[entry.registry_id] = fingerprint(descriptor)
        for dependency in descriptor.spec.dependencies:
            bind(dependency)

    for node in walk(document):
        if isinstance(node, BlockConditionNode):
            bind(node.block_id)
        elif isinstance(node, (vm.IndicatorExpressionNode, vm.FunctionExpressionNode)):
            if node.name not in ("math.min", "math.max", "math.abs"):
                bind(node.name)
        elif (
            isinstance(node, (vm.StopLossSpec, vm.TakeProfitSpec))
            and node.type == "atr"
        ):
            bind("indicator.volatility.atr")
    return result


def _validate_parameters(node: Any, descriptor: Any, document: Any) -> None:
    """Validate a concrete executable capability."""
    static = {}
    dynamic = False
    for key, value in node.params.items():
        if isinstance(value, vm.ParameterRefNode):
            static[key] = document.strategy.parameters[value.name].default
        elif isinstance(value, vm.ValueLiteralNode):
            static[key] = value.value
        elif isinstance(value, BaseModel):
            dynamic = True
        else:
            static[key] = value
    if not dynamic:
        descriptor.instantiate(**static)


def _validate_indicator(node: Any, descriptor: Any, document: Any) -> None:
    """Validate a concrete executable capability."""
    outputs = {port.name for port in descriptor.spec.outputs}
    if node.output not in outputs and node.output != "main":
        raise DomainError(
            code="HSL_UNKNOWN_OUTPUT",
            message=f"Unknown output {node.output} for {node.name}",
        )
    inputs = {port.name for port in descriptor.spec.inputs}
    if inputs == {"close"}:
        inputs.add("source")
    if not set(node.inputs).issubset(inputs):
        raise DomainError(
            code="HSL_UNKNOWN_INPUT", message=f"Unknown input binding for {node.name}"
        )
    for operand in node.inputs.values():
        if isinstance(operand, vm.MarketPriceNode) and operand.context.shift:
            raise DomainError(
                code="HSL_UNSUPPORTED_INPUT",
                message="Shifted indicator input bindings are not supported",
            )
        if not isinstance(operand, vm.MarketPriceNode) or operand.field not in (
            "open",
            "high",
            "low",
            "close",
            "volume",
        ):
            raise DomainError(
                code="HSL_UNSUPPORTED_INPUT",
                message="Indicator inputs require direct price-series bindings",
            )
    _validate_parameters(node, descriptor, document)


def _validate_expression(node: Any, library: Any, registry: Any, document: Any) -> None:
    """Validate a concrete executable capability."""
    if isinstance(node, vm.FunctionExpressionNode) and node.name in (
        "math.min",
        "math.max",
        "math.abs",
    ):
        arity = 1 if node.name == "math.abs" else 2
        if len(node.args) != arity:
            raise DomainError(
                code="HSL_FUNCTION_ARITY", message="Invalid primitive function arity"
            )
        return
    entry = library.require(node.name)
    descriptor = registry.require(entry.registry_id)
    if not descriptor.spec.is_causal:
        raise DomainError(
            code="HSL_NONCAUSAL_BLOCK", message=f"Block {node.name} is non-causal"
        )
    if descriptor.spec.execution_kind != ExecutionKind.EXPRESSION:
        raise DomainError(
            code="HSL_INVALID_BLOCK_FAMILY",
            message=f"Block {node.name} is not a pure expression",
        )
    if isinstance(node, vm.IndicatorExpressionNode):
        _validate_indicator(node, descriptor, document)
    elif descriptor.is_class:
        raise DomainError(
            code="HSL_UNSUPPORTED_FUNCTION",
            message="Function nodes require pure registered callables",
        )
    else:
        try:
            inspect.signature(descriptor.target).bind(*([None] * len(node.args)))
        except (TypeError, ValueError) as error:
            raise DomainError(
                code="HSL_FUNCTION_ARITY",
                message="Function arguments do not match its registered signature",
            ) from error


def _validate_options(document: Any) -> None:
    """Validate a concrete executable capability."""
    options = document.strategy.trading_options
    try:
        ZoneInfo(options.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise DomainError(
            code="HSL_INVALID_TIMEZONE", message="Unknown session timezone"
        ) from error
    from app.core.trading.strategy.hsl.policies import _minute

    if options.limit_time_range:
        _minute(options.time_range_start)
        _minute(options.time_range_end)
    if options.exit_at_end_of_day:
        _minute(options.end_of_day_time)
    if options.exit_on_friday:
        _minute(options.friday_exit_time)


def validate_capabilities(
    document: HSLStrategyDocument, registry: BlockRegistry
) -> None:
    """Reject unsupported runtime semantics even when the AST shape is valid."""
    library = WizardBlockLibrary(registry=registry, seed_defaults=False)
    for node in walk(document):
        if isinstance(node, (ParameterSpec, VariableSpec)):
            value = node.default if isinstance(node, ParameterSpec) else node.initial
            try:
                vm.ValueLiteralNode(value=value, value_type=node.type)
            except ValueError as error:
                raise DomainError(
                    code="HSL_INVALID_DECLARATION",
                    message="Declaration value does not match its scalar type",
                ) from error
        if isinstance(node, BlockConditionNode):
            entry = library.require(node.block_id)
            descriptor = registry.require(entry.registry_id)
            if descriptor.composition is None or not descriptor.spec.is_causal:
                raise DomainError(
                    code="HSL_UNSUPPORTED_CONDITION",
                    message="Condition requires a causal declarative composition",
                )
            descriptor.instantiate(**node.params)
        if isinstance(node, (vm.IndicatorExpressionNode, vm.FunctionExpressionNode)):
            _validate_expression(node, library, registry, document)
    if document.strategy.universe.mode != "explicit":
        raise DomainError(
            code="HSL_UNSUPPORTED_UNIVERSE",
            message="Execution requires an explicit symbol universe",
        )
    if (
        sum(
            partial.close_pct
            for partial in document.strategy.trade_management.partial_exits
        )
        > PERCENT
    ):
        raise DomainError(
            code="HSL_INVALID_PARTIAL_EXITS",
            message="Partial exit percentages exceed the original position",
        )
    _validate_options(document)
    logger.debug("FR-hsl-capabilities: validated %s", document.strategy.id)
