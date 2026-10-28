"""Boolean variable building block."""

from __future__ import annotations

from app.host.logging import get_logger
from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.types.variable import Variable

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
        "FR-SERVICES-TYPES-VARIABLES: boolean_variable(shift=%d) -> %s",
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
            "FR-SERVICES-TYPES-VARIABLES: BooleanVariable(shift=%d) -> %s",
            shift,
            res,
        )
        return res
