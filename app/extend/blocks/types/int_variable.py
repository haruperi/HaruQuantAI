"""Int variable building block matching StrategyQuant SQ.Blocks.Other.IntVariable.

Description:
    Provides variable-backed integer evaluation returning float-cast values,
    supporting both functional @block evaluation with Variable[int] / int and
    object-oriented IntVariable class instantiation.
Purpose:
    FEAT-TYPES-BLOCKS: StrategyQuant donor-faithful primitive type and variable blocks.
Key Capabilities:
    - FR-TYPES-INT-VARIABLE: Evaluate integer variable container cast to float.
Python API Usage:
    from app.extend.blocks.types.int_variable import IntVariable, int_variable
    from app.extend.blocks.types.variable import Variable
    var = Variable("bar_counter", "int", 42)
    val = int_variable(var)
    block_obj = IntVariable(var)
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
from app.extend.blocks.types.variable import Variable

logger = get_logger(__name__)

__all__ = ["IntVariable", "int_variable", "int_variable_spec"]

int_variable_spec = BlockSpec(
    id="types.int_variable",
    version="1.0.0",
    name="Int Variable",
    description="Integer variable evaluation block",
    category="types",
    tags=("types", "variable", "int"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("variable", PortType.ANY, "Variable reference or int value"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Evaluated int variable"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(int_variable_spec)
def int_variable(variable: Variable[int] | int, shift: int = 0) -> float:
    """Evaluate integer variable to float.

    Args:
        variable: Variable reference or int value.
        shift: Relative bar shift (default: 0).

    Returns:
        Value cast to float.
    """
    raw_val = variable.get_value() if isinstance(variable, Variable) else variable
    res = float(raw_val)
    logger.debug(
        "FR-TYPES-INT-VARIABLE: int_variable(shift=%d) -> %s",
        shift,
        res,
    )
    return res


class IntVariable:
    """Integer variable building block."""

    def __init__(self, variable: Variable[int] | int) -> None:
        """Initialize integer variable block.

        Args:
            variable: Variable reference or raw int value.
        """
        self.variable = variable

    def evaluate(self, shift: int = 0) -> float:
        """Evaluate integer variable cast to float.

        Args:
            shift: Relative bar shift.

        Returns:
            Value cast to float.
        """
        raw_val = (
            self.variable.get_value()
            if isinstance(self.variable, Variable)
            else self.variable
        )
        res = float(raw_val)
        logger.debug(
            "FR-TYPES-INT-VARIABLE: IntVariable(shift=%d) -> %s",
            shift,
            res,
        )
        return res
