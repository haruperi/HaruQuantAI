"""Quantitative type and variable building blocks implementation."""

from __future__ import annotations

from typing import override

from app.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "BooleanConstant",
    "BooleanVariable",
    "DoubleVariable",
    "IntVariable",
    "NumberConstant",
    "Types",
    "Variable",
    "boolean_constant",
    "boolean_variable",
    "double_variable",
    "int_variable",
    "number_constant",
]


class Variable[T]:
    """Generic mutable state container for strategy variables.

    Encapsulates a variable name, type identifier, and typed value,
    providing getters and setters with non-silent audit logging.
    """

    def __init__(self, name: str, var_type: str, initial_value: T) -> None:
        """Initialize variable state.

        Args:
            name: Human-readable variable identifier.
            var_type: Data type name (e.g. 'bool', 'int', 'double', 'float').
            initial_value: Initial value stored in the container.
        """
        self.name = name
        self.var_type = var_type
        self._value: T = initial_value
        logger.debug(
            "FR-SERVICES-TYPES-VARIABLES: Initialized variable '%s' (type=%s, val=%s)",
            self.name,
            self.var_type,
            self._value,
        )

    def get_value(self) -> T:
        """Return the current value."""
        return self._value

    def set_value(self, value: T) -> None:
        """Update the stored value and log mutation.

        Args:
            value: New value to assign.
        """
        self._value = value
        logger.debug(
            "FR-SERVICES-TYPES-VARIABLES: Updated variable '%s' to %s",
            self.name,
            self._value,
        )

    @property
    def value(self) -> T:
        """Property getter for the current value."""
        return self._value

    @value.setter
    def value(self, new_val: T) -> None:
        """Property setter for the current value."""
        self.set_value(new_val)

    @override
    def __repr__(self) -> str:
        """Return developer representation."""
        return (
            f"Variable(name={self.name!r}, type={self.var_type!r}, "
            f"value={self._value!r})"
        )


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
            "FR-SERVICES-TYPES-BOOLEAN: BooleanConstant(val=%s, shift=%d) -> %s",
            self.value,
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
            "FR-SERVICES-TYPES-VARIABLES: DoubleVariable(shift=%d) -> %s",
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


# ---------------------------------------------------------------------------
# Functional Evaluator Primitives
# ---------------------------------------------------------------------------


def boolean_constant(value: bool = False, shift: int = 0) -> float:
    """Evaluate boolean constant to 1.0 or 0.0.

    Args:
        value: Boolean constant flag (default: False).
        shift: Relative bar shift (default: 0).

    Returns:
        1.0 if value is True else 0.0.
    """
    res = 1.0 if value else 0.0
    logger.debug(
        "FR-SERVICES-TYPES-BOOLEAN: boolean_constant(val=%s, shift=%d) -> %s",
        value,
        shift,
        res,
    )
    return res


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
        "FR-SERVICES-TYPES-VARIABLES: double_variable(shift=%d) -> %s",
        shift,
        res,
    )
    return res


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


def number_constant(number: float = 0.0, shift: int = 0) -> float:
    """Evaluate number constant to float.

    Args:
        number: Float or numeric constant (default: 0.0).
        shift: Relative bar shift (default: 0).

    Returns:
        Floating-point number.
    """
    res = float(number)
    logger.debug(
        "FR-SERVICES-TYPES-NUMBER: number_constant(val=%s, shift=%d) -> %s",
        number,
        shift,
        res,
    )
    return res


# ---------------------------------------------------------------------------
# Unified Types Facade
# ---------------------------------------------------------------------------


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
