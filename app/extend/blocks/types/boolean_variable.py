"""Boolean variable block matching StrategyQuant SQ.Blocks.Other.BooleanVariable.

Description:
    Provides variable-backed boolean evaluation returning 1.0 for True and 0.0 for
    False, supporting both functional @block evaluation with Variable[bool] / bool
    and object-oriented BooleanVariable class instantiation.
Purpose:
    FEAT-TYPES-BLOCKS: StrategyQuant donor-faithful primitive type and variable blocks.
Key Capabilities:
    - FR-TYPES-BOOLEAN-VARIABLE: Evaluate boolean variable container to 1.0 or 0.0.
Python API Usage:
    from app.extend.blocks.types.boolean_variable import (
        BooleanVariable,
        boolean_variable,
    )
    from app.extend.blocks.types.variable import Variable
    var = Variable("my_flag", "bool", True)
    val = boolean_variable(var)
    block_obj = BooleanVariable(var)
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

__all__ = ["BooleanVariable", "boolean_variable", "boolean_variable_spec"]

boolean_variable_spec = BlockSpec(
    id="types.boolean_variable",
    version="1.0.0",
    name="Boolean Variable",
    description="Boolean variable evaluation block",
    category="types",
    tags=("types", "variable", "boolean"),
    execution_kind=ExecutionKind.EXPRESSION,
    chart_pane=ChartPane.MAIN,
    inputs=(
        InputPort("variable", PortType.ANY, "Variable reference or boolean value"),
        InputPort("shift", PortType.NUMBER, "Historical bar shift", default=0),
    ),
    outputs=(OutputPort("value", PortType.BOOLEAN, "Evaluated boolean variable"),),
    is_generation_eligible=True,
    is_deterministic=True,
    is_causal=True,
)


@block(boolean_variable_spec)
def boolean_variable(variable: Variable[bool] | bool, shift: int = 0) -> float:
    """Evaluate boolean variable to 1.0 or 0.0.

    Args:
        variable: Variable reference or boolean value.
        shift: Relative bar shift (default: 0).

    Returns:
        1.0 if variable evaluates to True else 0.0.
    """
    raw_val = variable.get_value() if isinstance(variable, Variable) else variable
    res = 1.0 if raw_val else 0.0
    logger.debug(
        "FR-TYPES-BOOLEAN-VARIABLE: boolean_variable(shift=%d) -> %s",
        shift,
        res,
    )
    return res


class BooleanVariable:
    """Boolean variable building block."""

    def __init__(self, variable: Variable[bool] | bool) -> None:
        """Initialize boolean variable block.

        Args:
            variable: Variable reference or raw boolean value.
        """
        self.variable = variable

    def evaluate(self, shift: int = 0) -> float:
        """Evaluate variable to numeric representation (1.0 or 0.0).

        Args:
            shift: Relative bar shift.

        Returns:
            1.0 if evaluated variable is True else 0.0.
        """
        raw_val = (
            self.variable.get_value()
            if isinstance(self.variable, Variable)
            else self.variable
        )
        res = 1.0 if raw_val else 0.0
        logger.debug(
            "FR-TYPES-BOOLEAN-VARIABLE: BooleanVariable(shift=%d) -> %s",
            shift,
            res,
        )
        return res
