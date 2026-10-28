"""Action block to assign values or formulas to variables."""

from __future__ import annotations

from typing import Any

from app.host.logging import get_logger
from app.include.actions.base import ORDER_NOT_DEFINED, ActionRecord
from app.include.blocks.types import Variable

logger = get_logger(__name__)


class AssignVariableAction:
    """Action block to assign a value or evaluated formula to a variable."""

    def __init__(
        self,
        variable: Variable[Any],
        value: Any,
        is_boolean: bool = False,
    ) -> None:
        """Initialize assign variable action.

        Args:
            variable: Target Variable state container.
            value: Value or callable returning a value.
            is_boolean: Whether to coerce value to boolean.
        """
        self.variable = variable
        self.value = value
        self.is_boolean = is_boolean

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

        self.variable.set_value(final_val)
        logger.debug(
            "FR-SERVICES-ACTION-ASSIGN: Assigned '%s' = %s (is_bool=%s)",
            self.variable.name,
            final_val,
            self.is_boolean,
        )
        return ActionRecord(
            action_type="assign_variable",
            params={
                "name": self.variable.name,
                "value": final_val,
                "is_boolean": self.is_boolean,
            },
        )


def assign_variable(
    variable: Variable[Any],
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
    action = AssignVariableAction(variable, value, is_boolean)
    return action.execute()


__all__ = ["AssignVariableAction", "assign_variable"]
