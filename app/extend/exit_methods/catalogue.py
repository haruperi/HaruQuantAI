"""Catalog registry and descriptors for StrategyQuant exit methods.

Description:
    Provides metadata, parameter specifications, builder ranges, and factory
    lookup for all 5 StrategyQuant exit method definitions matching donor
    classes in SQ.ExitMethods.

Purpose:
    FEAT-EXIT-METHODS: StrategyQuant donor-faithful exit methods.

Key Capabilities:
    - FR-exit-methods-catalogue: Catalog registry and descriptors for exit methods.

Python API Usage:
    from app.extend.exit_methods.catalogue import list_exit_methods
    methods = list_exit_methods()

CLI Usage:
    python -m app.cli exit-method list
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.extend.exit_methods.base import ExitMethod, ExitType
from app.extend.exit_methods.exit_after_bars import ExitAfterBars
from app.extend.exit_methods.move_sl_2_be import MoveSL2BE
from app.extend.exit_methods.profit_target import ProfitTarget
from app.extend.exit_methods.stop_loss import StopLoss
from app.extend.exit_methods.trailing_stop import TrailingStop

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ExitMethodDescriptor:
    """Metadata descriptor for an exit method snippet."""

    class_name: str
    display_name: str
    category: str
    sort_order: int
    for_engine: str
    exit_type: ExitType
    donor_source: str
    description: str
    parameters: tuple[dict[str, Any], ...]


EXIT_METHODS_CATALOGUE: dict[str, ExitMethodDescriptor] = {
    "ExitAfterBars": ExitMethodDescriptor(
        class_name="ExitAfterBars",
        display_name="Exit After Bars",
        category="ExitMethods",
        sort_order=500,
        for_engine="*",
        exit_type=ExitType.EXIT_AFTER_BARS,
        donor_source="SQ.ExitMethods.ExitAfterBars",
        description=(
            "Number of bars after which this trade will automatically be closed"
        ),
        parameters=(
            {
                "name": "exit_after_bars",
                "type": "int",
                "default": 0,
                "min_value": 0,
                "max_value": 99999,
                "builder_min_value": 5,
                "builder_max_value": 500,
                "step": 1,
            },
        ),
    ),
    "MoveSL2BE": ExitMethodDescriptor(
        class_name="MoveSL2BE",
        display_name="Move SL to BE",
        category="ExitMethods",
        sort_order=300,
        for_engine="*,-SP,-SA",
        exit_type=ExitType.MOVE_SL_2_BE,
        donor_source="SQ.ExitMethods.MoveSL2BE",
        description="Move StopLoss to Break Even",
        parameters=(
            {
                "name": "move_sl_to_be",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "RangeLevel",
            },
            {
                "name": "sl_to_be_add_pips",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "Range",
            },
        ),
    ),
    "ProfitTarget": ExitMethodDescriptor(
        class_name="ProfitTarget",
        display_name="Profit Target",
        category="ExitMethods",
        sort_order=200,
        for_engine="*",
        exit_type=ExitType.PROFIT_TARGET,
        donor_source="SQ.ExitMethods.ProfitTarget",
        description="Target exit price for the position",
        parameters=(
            {
                "name": "profit_target",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "SLPT",
            },
        ),
    ),
    "StopLoss": ExitMethodDescriptor(
        class_name="StopLoss",
        display_name="Stop Loss",
        category="ExitMethods",
        sort_order=100,
        for_engine="*",
        exit_type=ExitType.STOP_LOSS,
        donor_source="SQ.ExitMethods.StopLoss",
        description="Protective stop loss exit price for the position",
        parameters=(
            {
                "name": "stop_loss",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "SLPT",
            },
        ),
    ),
    "TrailingStop": ExitMethodDescriptor(
        class_name="TrailingStop",
        display_name="Trailing Stop",
        category="ExitMethods",
        sort_order=400,
        for_engine="*,-SP,-SA",
        exit_type=ExitType.TRAILING_STOP,
        donor_source="SQ.ExitMethods.TrailingStop",
        description="Trailing stop with optional activation threshold",
        parameters=(
            {
                "name": "trailing_stop",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "RangeLevel",
            },
            {
                "name": "trailing_activation",
                "type": "float",
                "default": 0.0,
                "editor": "Formula",
                "formula_name": "Range",
            },
        ),
    ),
}

_CONSTRUCTORS: dict[str, type[ExitMethod]] = {
    "ExitAfterBars": ExitAfterBars,
    "MoveSL2BE": MoveSL2BE,
    "ProfitTarget": ProfitTarget,
    "StopLoss": StopLoss,
    "TrailingStop": TrailingStop,
}


def get_exit_method_descriptor(name: str) -> ExitMethodDescriptor | None:
    """Retrieve an exit method descriptor by its class name.

    Args:
        name: Name of the exit method class.

    Returns:
        Descriptor if found, otherwise None.
    """
    return EXIT_METHODS_CATALOGUE.get(name)


def list_exit_methods() -> list[ExitMethodDescriptor]:
    """Return all exit method descriptors sorted by sort_order.

    Returns:
        List of all 5 exit method descriptors.
    """
    return sorted(EXIT_METHODS_CATALOGUE.values(), key=lambda d: d.sort_order)


def create_exit_method(name: str, **kwargs: Any) -> ExitMethod:
    """Instantiate an exit method class by name.

    Args:
        name: Name of the exit method class.
        **kwargs: Arguments passed to class constructor.

    Returns:
        Instantiated ExitMethod instance.

    Raises:
        KeyError: If exit method name is not registered.
    """
    cls = _CONSTRUCTORS.get(name)
    if cls is None:
        logger.error("FR-exit-methods-catalogue: unknown exit method %s", name)
        raise KeyError(f"Unknown exit method: {name}")
    return cls(**kwargs)
