"""Named program lookup and registration protocol."""

import logging
from typing import Protocol

from app.core.lib.errors import DomainError, JSONValue

logger = logging.getLogger("haruquant.core.programs")


class Program(Protocol):
    """Protocol declaring callable interface for registered programs."""

    def call(self, operation: str, *args: JSONValue) -> JSONValue:
        """Execute a named operation on the program.

        Args:
            operation: Name of the operation to invoke.
            *args: JSON-compatible arguments.

        Returns:
            JSON-compatible result.
        """
        ...


class ProgramRegistry:
    """Registry maintaining named programs with first-registration-wins semantics."""

    def __init__(self) -> None:
        """Initialize empty program registry without built-ins."""
        self._programs: dict[str, Program] = {}

    def register(self, name: str, program: Program) -> bool:
        """Register a program under the given name.

        If a program with this name already exists, logs an error and returns False.

        Args:
            name: Exact name under which to register the program.
            program: Program implementation matching Program protocol.

        Returns:
            True if registered, False if duplicate.
        """
        if name in self._programs:
            logger.error(
                "Duplicate registered program with name '%s', "
                "skipping second registration!",
                name,
            )
            return False
        self._programs[name] = program
        return True

    def is_registered(self, name: str) -> bool:
        """Check if a program with the exact name is registered.

        Args:
            name: Exact case-sensitive name to query.

        Returns:
            True if present in registry, False otherwise.
        """
        return name in self._programs

    def get(self, name: str) -> Program:
        """Retrieve registered program by exact name.

        Args:
            name: Exact case-sensitive name of the program.

        Returns:
            Registered Program instance.

        Raises:
            DomainError: If program with specified name is not found.
        """
        if name not in self._programs:
            raise DomainError(
                code="PROGRAM_NOT_FOUND",
                message=f"Program '{name}' doesn't exist",
                details={"name": name},
            )
        return self._programs[name]
