"""Open order building blocks and specifications.

Description:
    Exposes canonical strategy order opening blocks matching StrategyQuant
    SQ.Blocks.Order.Open donor classes.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-ENTER-AT-LIMIT: Open limit order with pending replacement.
    - FR-ORDER-ENTER-AT-MARKET: Open market order at current price.
    - FR-ORDER-ENTER-AT-STOP: Open stop order with pending replacement.
    - FR-ORDER-ENTER-REVERSE-AT-MARKET: Reverse position at market.
Python API Usage:
    from app.extend.blocks.order.open import (
        enter_at_limit,
        enter_at_market,
        enter_at_stop,
        enter_reverse_at_market,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.order.open._common import execute_entry
from app.extend.blocks.order.open.enter_at_limit import (
    enter_at_limit,
    enter_at_limit_spec,
)
from app.extend.blocks.order.open.enter_at_market import (
    enter_at_market,
    enter_at_market_spec,
)
from app.extend.blocks.order.open.enter_at_stop import (
    enter_at_stop,
    enter_at_stop_spec,
)
from app.extend.blocks.order.open.enter_reverse_at_market import (
    enter_reverse_at_market,
    enter_reverse_at_market_spec,
)

__all__ = [
    "enter_at_limit",
    "enter_at_limit_spec",
    "enter_at_market",
    "enter_at_market_spec",
    "enter_at_stop",
    "enter_at_stop_spec",
    "enter_reverse_at_market",
    "enter_reverse_at_market_spec",
    "execute_entry",
]
