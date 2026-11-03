"""Named program lookup and registration protocol matching donor Program.java.

Description:
    Provides canonical named program registration and retrieval matching
    StrategyQuant Program.java runtime behavior. Maintains first-registration-wins
    semantics and explicit duplicate rejection.

Purpose:
    FEAT-CORE-LIB-PROGRAMS: Provide verified named program registry utilities.

Key Capabilities:
    - FR-core-lib-program-register: Register named program with first-wins semantics
      and non-silent error logging for duplicates.
    - FR-core-lib-program-lookup: Retrieve registered program or raise DomainError
      when not found.

Python API Usage:
    ```python
    from app.core.lib.programs import ProgramRegistry, get, register

    register("my_plugin", my_instance)
    prog = get("my_plugin")
    ```

CLI Usage:
    ```bash
    uv run pytest tests/core/lib/test_programs.py -q
    ```
"""

from __future__ import annotations

from typing import Protocol

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError, JSONValue

logger = get_logger(__name__)

__all__ = [
    "Program",
    "ProgramRegistry",
    "default_program_registry",
    "get",
    "is_registered",
    "register",
]


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
        logger.debug("Program '%s' was registered.", name)
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


default_program_registry: ProgramRegistry = ProgramRegistry()


def register(name: str, program: Program) -> bool:
    """Register a program in the default global registry."""
    return default_program_registry.register(name, program)


def is_registered(name: str) -> bool:
    """Check if a program is registered in the default global registry."""
    return default_program_registry.is_registered(name)


def get(name: str) -> Program:
    """Retrieve a program from the default global registry."""
    return default_program_registry.get(name)
