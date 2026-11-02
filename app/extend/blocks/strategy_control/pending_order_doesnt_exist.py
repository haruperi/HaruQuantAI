"""Canonical pending order doesnt exist strategy block."""

from __future__ import annotations

from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.strategy_control.pending_order_exists import (
    pending_order_exists,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="strategy_control.pending_order_doesnt_exist",
        name="Pending Order Doesnt Exist",
        description="Return whether no matching pending order exists.",
        category="strategy_control",
        execution_kind=ExecutionKind.CONDITION,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.BOOLEAN),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def pending_order_doesnt_exist(
    context: TradingRuntime, scope: TradeFilter
) -> bool:
    """Return whether no matching pending order exists."""
    return not await pending_order_exists(context, scope)
