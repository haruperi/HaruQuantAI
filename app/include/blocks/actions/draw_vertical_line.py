"""Draw vertical line chart annotation action block."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.include.blocks.actions.base import ActionRecord
from app.include.blocks.base import BaseBlock
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)


class DrawVerticalLineAction(BaseBlock):
    """Action block to record a vertical line chart annotation."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.draw_vertical_line",
        version="1.0.0",
        name="Draw Vertical Line",
        description="Records a vertical line chart annotation",
        category="actions",
        tags=("action", "draw", "annotation", "line"),
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
        """Execute vertical line annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawVerticalLine(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_vertical_line",
            params={"shift": self.shift},
        )


def draw_vertical_line(shift: int = 0) -> ActionRecord:
    """Record a vertical line annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing vertical line.
    """
    action = DrawVerticalLineAction(shift=shift)
    return action.execute()


__all__ = ["DrawVerticalLineAction", "draw_vertical_line"]
