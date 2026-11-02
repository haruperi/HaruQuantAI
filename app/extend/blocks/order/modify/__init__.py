"""Modify order building blocks and specifications.

Description:
    Exposes canonical strategy order modification blocks matching StrategyQuant
    SQ.Blocks.Order.Modify donor classes.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-SET-PROFIT-TARGET: Set or update order profit target.
    - FR-ORDER-SET-STOP-LOSS: Set or update order stop loss with tightening policy.
Python API Usage:
    from app.extend.blocks.order.modify import (
        set_profit_target,
        set_stop_loss,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.order.modify.set_profit_target import (
    set_profit_target,
    set_profit_target_spec,
)
from app.extend.blocks.order.modify.set_stop_loss import (
    set_stop_loss,
    set_stop_loss_spec,
)

__all__ = [
    "set_profit_target",
    "set_profit_target_spec",
    "set_stop_loss",
    "set_stop_loss_spec",
]
