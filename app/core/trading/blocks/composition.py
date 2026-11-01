"""Immutable, validated indicator-composition metadata and execution binding."""

from __future__ import annotations

import importlib.resources
import inspect
import json
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from pydantic import ConfigDict, Field, create_model

from app.core.trading.blocks.indicator import BaseIndicator
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
    _freeze_mapping,
)


@dataclass(frozen=True)
class CompositionSpec:
    """One named recipe, owned by an indicator source rather than another algorithm."""

    id: str
    name: str
    donor: str
    owner_id: str
    recipe: Mapping[str, Any]
    generation_eligible: bool = False

    def __post_init__(self) -> None:
        """Freeze all nested recipe data before publication."""
        object.__setattr__(self, "recipe", _freeze_mapping(dict(self.recipe)))


@lru_cache(maxsize=1)
def _parsed_manifest(text: str) -> Mapping[str, Any]:
    return cast("Mapping[str, Any]", _freeze_mapping(json.loads(text)))


def composition_manifest() -> Mapping[str, Any]:
    """Read content-addressed metadata; reloading sources sees current recipes."""
    try:
        ref = importlib.resources.files("app.extend.blocks.indicators").joinpath(
            "donor_compositions.json"
        )
        text = ref.read_text(encoding="utf-8")
    except FileNotFoundError, ModuleNotFoundError, OSError:
        path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "extend"
            / "blocks"
            / "indicators"
            / "donor_compositions.json"
        )
        text = path.read_text(encoding="utf-8")
    return _parsed_manifest(text)


def owned_compositions(owner_id: str) -> tuple[CompositionSpec, ...]:
    """Find executable definitions belonging to one canonical indicator."""
    return tuple(
        CompositionSpec(
            row["id"],
            row["name"],
            row["donor"],
            owner_id,
            row["recipe"],
            row.get("generation_eligible", False),
        )
        for row in composition_manifest()["mappings"]
        if row.get("status") == "composition" and row["owner_id"] == owner_id
    )


def _parameter_model(spec: CompositionSpec) -> Any:
    fields: dict[str, Any] = {}
    for name, item in spec.recipe["parameters"].items():
        annotation = {"integer": int, "number": float, "boolean": bool, "string": str}[
            item["type"]
        ]
        kwargs = {
            out: item[key]
            for key, out in [("minimum", "ge"), ("maximum", "le")]
            if key in item
        }
        fields[name] = (
            annotation,
            Field(default=... if item.get("required") else item["default"], **kwargs),
        )
    return create_model(
        "CompositionConfig",
        __config__=ConfigDict(
            strict=True,
            extra="forbid",
            frozen=True,
            validate_default=True,
            allow_inf_nan=False,
        ),
        **fields,
    )


def bind_composition(
    spec: CompositionSpec,
    owner: type[BaseIndicator],
    available: Mapping[str, Any] | None = None,
) -> tuple[Any, Any, BlockSpec]:
    """Pin algorithms and validate recipes before publication."""
    from app.core.trading.blocks.composition_runtime import CompositionExecutor

    if owner.spec.id != spec.owner_id:
        raise ValueError("Composition owner does not match its source indicator")
    model = _parameter_model(spec)
    validation_values = {
        name: item.get("default", item.get("minimum", 0))
        for name, item in spec.recipe["parameters"].items()
    }
    defaults = model(**validation_values).model_dump()
    calculations = {}
    catalog = composition_manifest()["calculations"]
    for block_id in {
        identifier
        for node in spec.recipe["nodes"].values()
        for identifier in (
            node.get("alternatives", {}).values() or (node["indicator"],)
        )
    }:
        if block_id == owner.spec.id:
            cls = owner
        elif available is not None and block_id in available:
            cls = available[block_id]
        else:
            info = catalog[block_id]
            cls = getattr(import_module(info["module"]), info["class"])
        calculations[block_id] = cls
    executable = CompositionExecutor(spec, model, calculations)
    executable.validate(defaults)
    dependencies = set(calculations)

    def operations(expr: Any) -> None:
        if isinstance(expr, (tuple, list)):
            if expr and expr[0] == "comparison":
                dependencies.add(expr[1])
            for child in expr:
                operations(child)

    operations(spec.recipe["expression"])
    required_inputs = executable.required_inputs(**defaults)
    block_spec = BlockSpec(
        id=spec.id,
        name=spec.name,
        description=f"Indicator composition for {spec.donor}",
        category="indicator_signals",
        execution_kind=ExecutionKind.CONDITION,
        inputs=(InputPort("bars", PortType.ANY, "Aligned market and external series"),),
        outputs=(OutputPort("condition", PortType.BOOLEAN),),
        required_market_inputs=required_inputs,
        required_history_lookback=executable.required_history(**defaults),
        dependencies=tuple(sorted(dependencies)),
        is_causal=all(cls.spec.is_causal for cls in calculations.values()),
        is_generation_eligible=spec.generation_eligible
        and not any(
            field not in ("open", "high", "low", "close", "volume")
            for field in required_inputs
        )
        and owner.spec.is_generation_eligible
        and all(cls.spec.is_generation_eligible for cls in calculations.values()),
        parameter_search_space=spec.recipe["parameters"],
    )
    return executable, model, block_spec


def owned_specializations(
    owner: type[BaseIndicator],
) -> tuple[tuple[Any, BlockSpec, Mapping[str, Any]], ...]:
    """Bind retained algorithms directly from their owning class or module."""
    import sys

    result = []
    for row in composition_manifest()["mappings"]:
        if (
            row.get("status") != "specialized_signal"
            or row["owner_id"] != owner.spec.id
        ):
            continue
        helper = row["helper"]
        namespace = owner if helper["class"] else sys.modules[owner.__module__]
        target = getattr(namespace, helper["function"])
        return_type = inspect.signature(target).return_annotation
        numeric = str(return_type).strip("'") in ("float", "int")
        spec = BlockSpec(
            id=row["id"],
            name=row["name"],
            description=f"Specialized signal from {row['donor']}",
            category="indicator_signals",
            execution_kind=ExecutionKind.EXPRESSION
            if numeric
            else ExecutionKind.CONDITION,
            inputs=tuple(
                InputPort(
                    p["name"],
                    {
                        "series": PortType.SERIES,
                        "number": PortType.NUMBER,
                        "any": PortType.ANY,
                    }[p["type"]],
                    required=p["required"],
                )
                for p in helper["inputs"]
            ),
            outputs=(
                OutputPort(
                    "value" if numeric else "condition",
                    PortType.NUMBER if numeric else PortType.BOOLEAN,
                ),
            ),
            required_market_inputs=(),
            dependencies=(owner.spec.id,),
            is_causal=owner.spec.is_causal,
            is_generation_eligible=False,
        )
        result.append((target, spec, helper["bindings"]))
    return tuple(result)


__all__ = [
    "CompositionSpec",
    "bind_composition",
    "composition_manifest",
    "owned_compositions",
    "owned_specializations",
]
