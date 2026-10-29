"""Common strategy block metadata and descriptor specifications."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any


def _freeze_mapping(val: Any) -> Any:
    """Recursively convert dictionaries and lists to immutable mapping/tuple proxies."""
    if isinstance(val, (dict, Mapping)):
        return MappingProxyType({k: _freeze_mapping(v) for k, v in val.items()})
    if isinstance(val, (list, tuple)):
        return tuple(_freeze_mapping(x) for x in val)
    return val


class ExecutionKind(StrEnum):
    """Categorization of block execution behavior."""

    EXPRESSION = "expression"  # Pure mathematical or series evaluation
    CONDITION = "condition"  # Boolean predicate or comparison
    STATE_READ_WRITE = "state_read_write"  # Variable read/write
    ACTION = "action"  # Explicit side effect (e.g. logging, annotation)
    ORDER = "order"  # Order placement or modification intent


class ChartPane(StrEnum):
    """Chart rendering target pane for indicator outputs."""

    MAIN = "main"  # Overlaid directly onto the main price chart
    SUB = "sub"  # Rendered in a separate oscillator pane below


class PortType(StrEnum):
    """Data types for block input and output ports."""

    NUMBER = "number"
    SERIES = "series"
    BOOLEAN = "boolean"
    BOOLEAN_SERIES = "boolean_series"
    STRING = "string"
    ANY = "any"


@dataclass(frozen=True)
class InputPort:
    """Descriptor for a declared input port on a block."""

    name: str
    port_type: PortType = PortType.SERIES
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class OutputPort:
    """Descriptor for a declared output port on a block."""

    name: str
    port_type: PortType = PortType.SERIES
    description: str = ""
    unit: str = ""
    lower_bound: float | None = None
    upper_bound: float | None = None


@dataclass(frozen=True)
class BlockSpec:
    """Comprehensive specification and contract descriptor for a strategy block."""

    id: str  # Stable unique ID, e.g. 'indicator.trend.sma'
    version: str = "1.0.0"
    name: str = ""  # Display name in UI / AlgoWizard
    description: str = ""
    category: str = "indicators"
    tags: tuple[str, ...] = ()

    execution_kind: ExecutionKind = ExecutionKind.EXPRESSION
    chart_pane: ChartPane = ChartPane.MAIN

    inputs: tuple[InputPort, ...] = ()
    outputs: tuple[OutputPort, ...] = ()

    required_market_inputs: tuple[str, ...] = ("close",)
    required_history_lookback: int = 1

    is_generation_eligible: bool = True
    parameter_search_space: Mapping[str, Any] = field(default_factory=dict)

    is_deterministic: bool = True
    is_causal: bool = True
    supports_incremental: bool = False

    dependencies: tuple[str, ...] = ()
    revision_fingerprint: str = ""

    def __post_init__(self) -> None:
        """Deeply freeze nested metadata collections."""
        if isinstance(self.parameter_search_space, (dict, Mapping)):
            object.__setattr__(
                self,
                "parameter_search_space",
                _freeze_mapping(dict(self.parameter_search_space)),
            )


__all__ = [
    "BlockSpec",
    "ChartPane",
    "ExecutionKind",
    "InputPort",
    "OutputPort",
    "PortType",
    "_freeze_mapping",
]
