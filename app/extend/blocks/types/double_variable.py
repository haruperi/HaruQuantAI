"""Double variable building block matching StrategyQuant SQ.Blocks.Other.DoubleVariable.

Description:
    Provides variable-backed double/float evaluation returning floating-point values,
    supporting both functional @block evaluation with Variable[float] / float and
    object-oriented DoubleVariable class instantiation.
Purpose:
    FEAT-TYPES-BLOCKS: StrategyQuant donor-faithful primitive type and variable blocks.
Key Capabilities:
    - FR-TYPES-DOUBLE-VARIABLE: Evaluate double precision variable to float.
Python API Usage:
    from app.extend.blocks.types.double_variable import DoubleVariable, double_variable
    from app.extend.blocks.types.variable import Variable
    var = Variable("target_rate", "double", 1.2345)
    val = double_variable(var)
    block_obj = DoubleVariable(var)
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

__all__ = ["DoubleVariable", "double_variable", "double_variable_spec"]

double_variable_spec = BlockSpec(
    id="types.double_variable",
    version="1.0.0",
    name="Double Variable",
    description="Double precision variable evaluation block",
    category="types",
    tags=("types", "variable", "double"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("variable", PortType.ANY, "Variable reference or float value"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.NUMBER, "Evaluated double variable value"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(double_variable_spec)
def double_variable(variable: Variable[float] | float, shift: int = 0) -> float:
    """Evaluate double variable to float.

    Args:
        variable: Variable reference or float value.
        shift: Relative bar shift (default: 0).

    Returns:
        Floating-point number.
    """
    raw_val = variable.get_value() if isinstance(variable, Variable) else variable
    res = float(raw_val)
    logger.debug(
        "FR-TYPES-DOUBLE-VARIABLE: double_variable(shift=%d) -> %s",
        shift,
        res,
    )
    return res


class DoubleVariable:
    """Double variable building block."""

    def __init__(self, variable: Variable[float] | float) -> None:
        """Initialize double variable block.

        Args:
            variable: Variable reference or raw float value.
        """
        self.variable = variable

    def evaluate(self, shift: int = 0) -> float:
        """Evaluate double variable.

        Args:
            shift: Relative bar shift.

        Returns:
            Floating-point numeric value.
        """
        raw_val = (
            self.variable.get_value()
            if isinstance(self.variable, Variable)
            else self.variable
        )
        res = float(raw_val)
        logger.debug(
            "FR-TYPES-DOUBLE-VARIABLE: DoubleVariable(shift=%d) -> %s",
            shift,
            res,
        )
        return res
