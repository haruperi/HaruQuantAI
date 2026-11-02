"""Chart annotation action blocks.

Description:
    Groups and re-exports chart annotation building blocks for visual markup.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-ANNOTATIONS-REEXPORT: Grouped export of chart annotation actions.
Python API Usage:
    from app.extend.blocks.actions.annotations import (
        DrawDownArrow,
        draw_down_arrow,
    )
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from app.extend.blocks.actions.draw_down_arrow import (
    DrawDownArrow,
    DrawDownArrowAction,
    draw_down_arrow,
)
from app.extend.blocks.actions.draw_up_arrow import (
    DrawUpArrow,
    DrawUpArrowAction,
    draw_up_arrow,
)
from app.extend.blocks.actions.draw_vertical_line import (
    DrawVerticalLine,
    DrawVerticalLineAction,
    draw_vertical_line,
)

__all__ = [
    "DrawDownArrow",
    "DrawDownArrowAction",
    "DrawUpArrow",
    "DrawUpArrowAction",
    "DrawVerticalLine",
    "DrawVerticalLineAction",
    "draw_down_arrow",
    "draw_up_arrow",
    "draw_vertical_line",
]
