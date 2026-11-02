"""Account balance strategy block.

Description:
    Returns the account balance in account currency from the active trading
    runtime context.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ACCOUNT-BALANCE: Account balance retrieval.
Python API Usage:
    from app.extend.blocks.strategy_control.account_balance import (
        AccountBalance,
        account_balance,
    )
    balance = await account_balance(context)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

account_balance_spec = BlockSpec(
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


@block(account_balance_spec)
async def account_balance(context: TradingRuntime) -> float:
    """Return account balance in account currency.

    Args:
        context: Active trading runtime context.

    Returns:
        Current account balance as float.
    """
    logger.debug("FR-STRATEGY-CONTROL-ACCOUNT-BALANCE: Querying account balance")
    info = await context.account.AccountInfo()
    return float(info.balance)


# Exact StrategyQuant donor snippet class alias
AccountBalance = account_balance

__all__ = ["AccountBalance", "account_balance", "account_balance_spec"]
