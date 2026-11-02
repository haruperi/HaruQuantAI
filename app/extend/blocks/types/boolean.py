"""Boolean constant building block matching StrategyQuant SQ.Blocks.Other.Boolean.

Description:
    Provides constant boolean value evaluation returning 1.0 for True and 0.0 for
    False, supporting both functional @block decoration and object-oriented
    BooleanConstant / Boolean class instantiation.
Purpose:
    FEAT-TYPES-BLOCKS: StrategyQuant donor-faithful primitive type and variable blocks.
Key Capabilities:
    - FR-TYPES-BOOLEAN: Constant boolean flag evaluation returning 1.0 or 0.0.
Python API Usage:
    from app.extend.blocks.types.boolean import Boolean, boolean
    val = boolean(True)
    block_obj = Boolean(True)
    res = block_obj.evaluate()
CLI Usage:
    uv run pytest tests/extend/blocks/test_types.py --no-cov
"""

from __future__ import annotations

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)

logger = get_logger(__name__)

boolean_spec = BlockSpec(
    id="types.boolean",
    version="1.0.0",
    name="Boolean",
    description="Boolean constant value block",
    category="types",
    tags=("types", "constant", "boolean"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("value", PortType.BOOLEAN, "Boolean constant flag", default=False),
        InputPort("shift", PortType.NUMBER, "Historical bar shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.BOOLEAN, "Boolean flag (1.0 or 0.0)"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(boolean_spec)
def boolean(value: bool = False, shift: int = 0) -> float:
    """Evaluate boolean constant to 1.0 or 0.0.

    Args:
        value: Boolean constant flag (default: False).
        shift: Relative bar shift (default: 0).

    Returns:
        1.0 if value is True else 0.0.
    """
    res = 1.0 if value else 0.0
    logger.debug(
        "FR-TYPES-BOOLEAN: boolean(val=%s, shift=%d) -> %s",
        value,
        shift,
        res,
    )
    return res


boolean_constant = boolean


class BooleanConstant:
    """Boolean constant building block."""

    def __init__(self, value: bool = False) -> None:
        """Initialize boolean constant.

        Args:
            value: Boolean value flag (default: False).
        """
        self.value = value

    def evaluate(self, shift: int = 0) -> float:
        """Evaluate block to numeric representation (1.0 or 0.0).

        Args:
            shift: Relative bar shift (unused for constants).

        Returns:
            1.0 if value is True else 0.0.
        """
        res = 1.0 if self.value else 0.0
        logger.debug(
            "FR-TYPES-BOOLEAN: BooleanConstant(val=%s, shift=%d) -> %s",
            self.value,
            shift,
            res,
        )
        return res


Boolean = BooleanConstant

__all__ = [
    "Boolean",
    "BooleanConstant",
    "boolean",
    "boolean_constant",
    "boolean_spec",
]
