"""Unified Types facade for primitive types and variables."""

from __future__ import annotations

from app.host.logging import get_logger
from app.include.blocks.types.boolean import boolean_constant
from app.include.blocks.types.boolean_variable import boolean_variable
from app.include.blocks.types.double_variable import double_variable
from app.include.blocks.types.int_variable import int_variable
from app.include.blocks.types.number import number_constant
from app.include.blocks.types.variable import Variable

logger = get_logger(__name__)

__all__ = ["Types"]


class Types:
    """Centralized facade for primitive type and variable blocks."""

    @staticmethod
    def boolean(value: bool = False, shift: int = 0) -> float:
        """Evaluate a boolean constant.

        Args:
            value: Boolean value.
            shift: Relative bar shift.

        Returns:
            1.0 if True else 0.0.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.boolean(val=%s, shift=%d)",
            value,
            shift,
        )
        return boolean_constant(value, shift)

    @staticmethod
    def boolean_var(variable: Variable[bool] | bool, shift: int = 0) -> float:
        """Evaluate a boolean variable.

        Args:
            variable: Variable container or boolean value.
            shift: Relative bar shift.

        Returns:
            1.0 if True else 0.0.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.boolean_var(shift=%d)",
            shift,
        )
        return boolean_variable(variable, shift)

    @staticmethod
    def double_var(variable: Variable[float] | float, shift: int = 0) -> float:
        """Evaluate a double variable.

        Args:
            variable: Variable container or float value.
            shift: Relative bar shift.

        Returns:
            Float value.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.double_var(shift=%d)",
            shift,
        )
        return double_variable(variable, shift)

    @staticmethod
    def int_var(variable: Variable[int] | int, shift: int = 0) -> float:
        """Evaluate an integer variable.

        Args:
            variable: Variable container or int value.
            shift: Relative bar shift.

        Returns:
            Float value.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.int_var(shift=%d)",
            shift,
        )
        return int_variable(variable, shift)

    @staticmethod
    def number(number: float = 0.0, shift: int = 0) -> float:
        """Evaluate a number constant.

        Args:
            number: Float constant value.
            shift: Relative bar shift.

        Returns:
            Float value.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.number(val=%s, shift=%d)",
            number,
            shift,
        )
        return number_constant(number, shift)

    @staticmethod
    def create_variable[T](name: str, var_type: str, initial_value: T) -> Variable[T]:
        """Factory method to construct a typed variable.

        Args:
            name: Variable identifier name.
            var_type: Data type string.
            initial_value: Initial typed value.

        Returns:
            Configured Variable instance.
        """
        logger.debug(
            "FR-SERVICES-TYPES-FACADE: Types.create_variable(name='%s', type=%s)",
            name,
            var_type,
        )
        return Variable[T](name, var_type, initial_value)
