"""Generic mutable state container for strategy variables."""

from __future__ import annotations

from typing import override

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["Variable"]


class Variable[T]:
    """Generic mutable state container for strategy variables.

    Encapsulates a variable name, type identifier, and typed value,
    providing getters and setters with non-silent audit logging.
    """

    __hash__ = None  # type: ignore[assignment]

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

    @override
    def __eq__(self, other: object) -> bool:
        """Check equality with another Variable or raw value."""
        if isinstance(other, Variable):
            return (
                self.name == other.name
                and self.var_type == other.var_type
                and self._value == other._value
            )
        return self._value == other
