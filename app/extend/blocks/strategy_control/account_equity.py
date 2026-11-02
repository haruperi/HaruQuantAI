"""Account equity strategy block.

Description:
    Returns the account equity in account currency from the active trading
    runtime context.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ACCOUNT-EQUITY: Account equity retrieval.
Python API Usage:
    from app.extend.blocks.strategy_control.account_equity import (
        AccountEquity,
        account_equity,
    )
    equity = await account_equity(context)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.runtime import TradingRuntime

logger = get_logger(__name__)

account_equity_spec = BlockSpec(
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


@block(account_equity_spec)
async def account_equity(context: TradingRuntime) -> float:
    """Return account equity in account currency.

    Args:
        context: Active trading runtime context.

    Returns:
        Current account equity as float.
    """
    logger.debug("FR-STRATEGY-CONTROL-ACCOUNT-EQUITY: Querying account equity")
    info = await context.account.AccountInfo()
    return float(info.equity)


# Exact StrategyQuant donor snippet class alias
AccountEquity = account_equity

__all__ = ["AccountEquity", "account_equity", "account_equity_spec"]
