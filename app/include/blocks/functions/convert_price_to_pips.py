"""Price to pips conversion strategy block."""

from __future__ import annotations

import inspect
import math
from typing import Any

from app.core.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.functions._common import (
    resolve_pip_size,
    resolve_shift_value,
)
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

convert_price_to_pips_spec = BlockSpec(
    id="function.convert_price_to_pips",
    version="1.0.0",
    name="Convert Price to Pips",
    description="Converts price difference to pips using broker point sizing",
    category="functions",
    tags=("forex", "pips", "conversion", "price"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("price_diff", PortType.ANY, "Price difference operand"),
        InputPort("point", PortType.NUMBER, "Point size", default=None),
        InputPort("digits", PortType.NUMBER, "Precision digits", default=None),
        InputPort(
            "pip_size", PortType.NUMBER, "Explicit pip size override", default=None
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Value in pips"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(convert_price_to_pips_spec)
def convert_price_to_pips(
    price_diff: Any,
    shift: int = 0,
    *,
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Convert price difference to pips using point resolution.

    Example: converts 0.002 to 20 pips for 5-digit quote with point=0.00001.

    Args:
        price_diff: Raw price difference operand (scalar, series, array, or callable).
        shift: Historical bar offset when price_diff is shift-indexed.
        point: Instrument point (e.g. from MT5 symbol.Point()).
        digits: Instrument digits.
        pip_size: Explicit pip size override.

    Returns:
        Pip value as float, or NaN on invalid pip sizing or operand.
    """
    val = resolve_shift_value(price_diff, shift)
    eff_pip = resolve_pip_size(point=point, digits=digits, pip_size=pip_size)
    if eff_pip <= 0.0 or math.isnan(val):
        return float("nan")
    res = float(val / eff_pip)
    logger.debug(
        "FR-SERVICES-FUNCTION-PIPS: convert_price_to_pips(%f, pip=%f) = %f",
        val,
        eff_pip,
        res,
    )
    return res


async def convert_price_to_pips_symbol(
    price_diff: Any, symbol: Any, shift: int = 0
) -> float:
    """Convert price difference to pips querying real MT5 broker symbol properties.

    Args:
        price_diff: Raw price difference operand (scalar, series, array, or callable).
        symbol: MT5 SymbolInfo proxy or mock.
        shift: Historical bar offset when price_diff is shift-indexed.

    Returns:
        Converted pips as float.
    """
    pt_call = symbol.Point()
    pt = await pt_call if inspect.isawaitable(pt_call) else pt_call

    dig_call = symbol.Digits()
    dig = await dig_call if inspect.isawaitable(dig_call) else dig_call

    return convert_price_to_pips(
        price_diff,
        shift=shift,
        point=float(pt),
        digits=int(dig) if dig is not None else None,
    )


__all__ = [
    "convert_price_to_pips",
    "convert_price_to_pips_spec",
    "convert_price_to_pips_symbol",
]
