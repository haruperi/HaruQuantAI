"""Pips to real price level conversion strategy block."""

from __future__ import annotations

import inspect
import math
from typing import Any

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.functions._common import (
    resolve_pip_size,
    resolve_shift_value,
)
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

convert_pips_to_price_spec = BlockSpec(
    id="function.convert_pips_to_price",
    version="1.0.0",
    name="Convert Pips to Price",
    description="Converts pips to price offset using broker point resolution",
    category="functions",
    tags=("forex", "pips", "conversion", "price"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("pips", PortType.ANY, "Pips operand (scalar, series, or callable)"),
        InputPort("point", PortType.NUMBER, "Point size", default=None),
        InputPort("digits", PortType.NUMBER, "Precision digits", default=None),
        InputPort(
            "pip_size", PortType.NUMBER, "Explicit pip size override", default=None
        ),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Price offset"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(convert_pips_to_price_spec)
def convert_pips_to_price(
    pips: Any,
    shift: int = 0,
    *,
    point: float | None = None,
    digits: int | None = None,
    pip_size: float | None = None,
) -> float:
    """Convert pips to real price level using point resolution.

    Example: converts 20 pips to 0.002 for 5-digit quote with point=0.00001.

    Args:
        pips: Number of pips operand (scalar, series, array, or callable).
        shift: Historical bar offset when pips is shift-indexed.
        point: Instrument point (e.g. from MT5 symbol.Point()).
        digits: Instrument digits.
        pip_size: Explicit pip size override.

    Returns:
        Price offset as float, or NaN on invalid pip sizing or operand.
    """
    val = resolve_shift_value(pips, shift)
    eff_pip = resolve_pip_size(point=point, digits=digits, pip_size=pip_size)
    if eff_pip <= 0.0 or math.isnan(val):
        return float("nan")
    res = float(val * eff_pip)
    logger.debug(
        "FR-SERVICES-FUNCTION-PIPS: convert_pips_to_price(%f, pip=%f) = %f",
        val,
        eff_pip,
        res,
    )
    return res


async def convert_pips_to_price_symbol(pips: Any, symbol: Any, shift: int = 0) -> float:
    """Convert pips to real price querying real MT5 broker symbol properties.

    Args:
        pips: Pip count operand (scalar, series, array, or callable).
        symbol: MT5 SymbolInfo proxy or mock.
        shift: Historical bar offset when pips is shift-indexed.

    Returns:
        Converted price offset as float.
    """
    pt_call = symbol.Point()
    pt = await pt_call if inspect.isawaitable(pt_call) else pt_call

    dig_call = symbol.Digits()
    dig = await dig_call if inspect.isawaitable(dig_call) else dig_call

    return convert_pips_to_price(
        pips,
        shift=shift,
        point=float(pt),
        digits=int(dig) if dig is not None else None,
    )


__all__ = [
    "convert_pips_to_price",
    "convert_pips_to_price_spec",
    "convert_pips_to_price_symbol",
]
