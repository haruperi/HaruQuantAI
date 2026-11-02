"""Canonical account equity strategy block."""

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


@block(
    BlockSpec(
        id="strategy_control.account_equity",
        name="Account Equity",
        description="Return account equity in account currency.",
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
async def account_equity(context: TradingRuntime) -> float:
    """Return account equity in account currency."""
    return (await context.account.AccountInfo()).equity
