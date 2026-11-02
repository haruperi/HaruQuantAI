"""Draw down arrow chart annotation action block.

Description:
    Records a down arrow annotation on the chart at a given relative bar
    shift according to StrategyQuant chart visualization rules.
Purpose:
    FEAT-ACTION-BLOCKS: StrategyQuant donor-faithful action blocks.
Key Capabilities:
    - FR-ACTIONS-DRAW-DOWN-ARROW: Record down arrow chart annotation descriptor.
Python API Usage:
    from app.extend.blocks.actions.draw_down_arrow import (
        DrawDownArrow,
        draw_down_arrow,
    )
    rec = draw_down_arrow(shift=1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_actions.py --no-cov
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.extend.blocks.actions.base import ActionRecord
from app.extend.blocks.base import BaseBlock
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)


class DrawDownArrowAction(BaseBlock):
    """Action block to record a down arrow chart annotation."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.draw_down_arrow",
        version="1.0.0",
        name="Draw Down Arrow",
        description="Records a down arrow chart annotation",
        category="actions",
        tags=("action", "draw", "annotation", "arrow"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort(
                "shift",
                PortType.NUMBER,
                "Relative bar shift",
                default=0,
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    shift: int = Field(
        default=0,
        title="Shift",
        description="Relative bar shift",
    )

    def execute(self) -> ActionRecord:
        """Execute down arrow annotation action."""
        logger.debug(
            "FR-ACTIONS-DRAW-DOWN-ARROW: DrawDownArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_down_arrow",
            params={"shift": self.shift},
        )


# Direct donor class alias matching SQ.Blocks.OtherActions.DrawDownArrow
DrawDownArrow = DrawDownArrowAction


def draw_down_arrow(shift: int = 0) -> ActionRecord:
    """Record a down arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing down arrow.
    """
    action = DrawDownArrowAction(shift=shift)
    return action.execute()


__all__ = ["DrawDownArrow", "DrawDownArrowAction", "draw_down_arrow"]
