"""Canonical account balance strategy block."""

from __future__ import annotations

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order.runtime import TradingRuntime


@block(
    BlockSpec(
        id="strategy_control.account_balance",
        name="Account Balance",
        description="Return account balance in account currency.",
        category="strategy_control",
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(InputPort("context", PortType.ANY),),
        outputs=(OutputPort("result", PortType.NUMBER),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def account_balance(context: TradingRuntime) -> float:
    """Return account balance in account currency."""
    return (await context.account.AccountInfo()).balance
