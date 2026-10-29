"""Action block to assign values or formulas to variables."""

from __future__ import annotations

from typing import Any, ClassVar

from pydantic import Field

from app.core.host.logging import get_logger
from app.include.blocks.actions.base import ORDER_NOT_DEFINED, ActionRecord
from app.include.blocks.base import BaseBlock
from app.include.blocks.metadata import (
    BlockSpec,
    ChartPane,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.types import Variable

logger = get_logger(__name__)


class AssignVariableAction(BaseBlock):
    """Action block to assign a value or evaluated formula to a variable."""

    spec: ClassVar[BlockSpec] = BlockSpec(
        id="action.assign_variable",
        version="1.0.0",
        name="Assign Variable",
        description="Assigns a value or evaluated formula to a variable",
        category="actions",
        tags=("action", "variable", "assign"),
        execution_kind=ExecutionKind.ACTION,
        chart_pane=ChartPane.MAIN,
        inputs=(
            InputPort("variable", PortType.ANY, "Target variable container"),
            InputPort("value", PortType.ANY, "Value or callable"),
            InputPort(
                "is_boolean",
                PortType.BOOLEAN,
                "Coerce to boolean",
                default=False,
            ),
        ),
        outputs=(OutputPort("record", PortType.ANY, "Execution ActionRecord"),),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )

    variable: Any = Field(
        ...,
        title="Variable",
        description="Target variable state container",
    )
    value: Any = Field(
        ...,
        title="Value",
        description="Value or callable returning a value",
    )
    is_boolean: bool = Field(
        default=False,
        title="Is Boolean",
        description="Whether to coerce value to boolean",
    )

    def execute(self) -> ActionRecord:
        """Execute variable assignment."""
        resolved = (
            self.value()
            if callable(self.value)
            else (
                self.value.evaluate()
                if hasattr(self.value, "evaluate") and callable(self.value.evaluate)
                else self.value
            )
        )

        if self.is_boolean:
            # Truthiness: 0 or ORDER_NOT_DEFINED (-99999999.0) is False; otherwise True.
            if isinstance(resolved, (int, float)):
                final_val: Any = resolved not in (0.0, ORDER_NOT_DEFINED)
            else:
                final_val = bool(resolved)
        else:
            final_val = resolved

        if hasattr(self.variable, "set_value"):
            self.variable.set_value(final_val)
        var_name = getattr(self.variable, "name", str(self.variable))
        logger.debug(
            "FR-SERVICES-ACTION-ASSIGN: Assigned '%s' = %s (is_bool=%s)",
            var_name,
            final_val,
            self.is_boolean,
        )
        return ActionRecord(
            action_type="assign_variable",
            params={
                "name": var_name,
                "value": final_val,
                "is_boolean": self.is_boolean,
            },
        )


def assign_variable(
    variable: Variable[Any] | Any,
    value: Any,
    is_boolean: bool = False,
) -> ActionRecord:
    """Assign a value or formula result to a variable.

    Args:
        variable: Target variable container.
        value: New value or callable.
        is_boolean: Coerce to boolean (0 and ORDER_NOT_DEFINED map to False).

    Returns:
        ActionRecord summarizing the operation.
    """
    action = AssignVariableAction(
        variable=variable,
        value=value,
        is_boolean=is_boolean,
    )
    return action.execute()


__all__ = ["AssignVariableAction", "assign_variable"]
