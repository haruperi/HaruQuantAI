"""Draw up arrow chart annotation action block."""

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


class DrawUpArrowAction(BaseBlock):
    """Action block to record an up arrow chart annotation."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.draw_up_arrow",
        version="1.0.0",
        name="Draw Up Arrow",
        description="Records an up arrow chart annotation",
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
        """Execute up arrow annotation action."""
        logger.debug(
            "FR-SERVICES-ACTION-DRAW: DrawUpArrow(shift=%d)",
            self.shift,
        )
        return ActionRecord(
            action_type="draw_up_arrow",
            params={"shift": self.shift},
        )


def draw_up_arrow(shift: int = 0) -> ActionRecord:
    """Record an up arrow annotation descriptor.

    Args:
        shift: Relative bar shift (default: 0).

    Returns:
        ActionRecord describing up arrow.
    """
    action = DrawUpArrowAction(shift=shift)
    return action.execute()


__all__ = ["DrawUpArrowAction", "draw_up_arrow"]
