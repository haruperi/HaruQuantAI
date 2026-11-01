"""Number constant building block."""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

__all__ = ["NumberConstant", "number", "number_constant", "number_spec"]

number_spec = BlockSpec(
    id="types.number",
    version="1.0.0",
    name="Number",
    description="Numeric constant value block",
    category="types",
    tags=("types", "constant", "number"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("number", PortType.NUMBER, "Numeric constant value", default=0.0),
        InputPort("shift", PortType.NUMBER, "Historical bar shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Evaluated numeric constant"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(number_spec)
def number(number: float = 0.0, shift: int = 0) -> float:
    """Evaluate number constant to float.

    Args:
        number: Float or numeric constant (default: 0.0).
        shift: Relative bar shift (default: 0).

    Returns:
        Floating-point number.
    """
    res = float(number)
    logger.debug(
        "FR-SERVICES-TYPES-NUMBER: number(val=%s, shift=%d) -> %s",
        number,
        shift,
        res,
    )
    return res


number_constant = number


class NumberConstant:
    """Number constant building block."""

    def __init__(self, number: float = 0.0) -> None:
        """Initialize number constant block.

        Args:
            number: Constant numeric value (default: 0.0).
        """
        self.number = float(number)

    def evaluate(self, shift: int = 0) -> float:
        """Evaluate number constant.

        Args:
            shift: Relative bar shift (unused for constants).

        Returns:
            Floating-point numeric value.
        """
        res = float(self.number)
        logger.debug(
            "FR-SERVICES-TYPES-NUMBER: NumberConstant(val=%s, shift=%d) -> %s",
            self.number,
            shift,
            res,
        )
        return res
