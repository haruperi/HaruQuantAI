"""Close order building blocks and specifications.

Description:
    Exposes canonical strategy order closing blocks matching StrategyQuant
    SQ.Blocks.Order.Close donor classes.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-ALL-PENDING: Cancel all matching pending orders.
    - FR-ORDER-CLOSE-ALL-POSITIONS: Close all matching open positions.
    - FR-ORDER-CLOSE-BEST: Close highest profit matching position.
    - FR-ORDER-CLOSE-PENDING: Cancel first matching pending order.
    - FR-ORDER-CLOSE-POSITION: Close first matching position with volume control.
    - FR-ORDER-CLOSE-WORST: Close lowest profit matching position.
Python API Usage:
    from app.extend.blocks.order.close import (
        close_all_pending_orders,
        close_all_positions,
        close_best_position,
        close_pending_order,
        close_position,
        close_worst_position,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.order.close.close_all_pending_orders import (
    close_all_pending_orders,
    close_all_pending_orders_spec,
)
from app.extend.blocks.order.close.close_all_positions import (
    close_all_positions,
    close_all_positions_spec,
)
from app.extend.blocks.order.close.close_best_position import (
    close_best_position,
    close_best_position_spec,
)
from app.extend.blocks.order.close.close_pending_order import (
    close_pending_order,
    close_pending_order_spec,
)
from app.extend.blocks.order.close.close_position import (
    close_position,
    close_position_spec,
)
from app.extend.blocks.order.close.close_worst_position import (
    close_worst_position,
    close_worst_position_spec,
)

__all__ = [
    "close_all_pending_orders",
    "close_all_pending_orders_spec",
    "close_all_positions",
    "close_all_positions_spec",
    "close_best_position",
    "close_best_position_spec",
    "close_pending_order",
    "close_pending_order_spec",
    "close_position",
    "close_position_spec",
    "close_worst_position",
    "close_worst_position_spec",
]
