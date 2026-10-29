"""Int variable building block."""

from __future__ import annotations

from app.core.host.logging import get_logger
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
        "FR-SERVICES-TYPES-VARIABLES: int_variable(shift=%d) -> %s",
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
            "FR-SERVICES-TYPES-VARIABLES: IntVariable(shift=%d) -> %s",
            shift,
            res,
        )
        return res
