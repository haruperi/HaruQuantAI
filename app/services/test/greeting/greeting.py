"""Greeting generation service and deterministic message formatting.

Purpose:
    Provide deterministic greeting generation and caller-name validation
    for the test domain.

Key capabilities:
    * Validate and sanitize caller names against length and emptiness constraints.
    * Format deterministic greeting messages with default or custom salutations.
    * Enforce strict boundary conditions and raise descriptive ValueErrors.

Python API usage:
    service = GreetingServiceImpl(default_salutation="Hello", max_name_length=100)
    response = await service.generate_greeting(GreetingRequest(name="Alice"))
    print(response.message)  # "Hello, Alice!"

CLI usage:
    uv run python -m app.services.test.greeting.greeting
"""

from __future__ import annotations

import asyncio
import logging
from typing import override

from app.contracts.test.greeting import (
    GreetingRequest,
    GreetingResponse,
    GreetingService,
)

logger = logging.getLogger(__name__)


def generate_greeting_message(
    name: str,
    salutation: str,
    max_name_length: int,
) -> tuple[str, str, str]:
    """Validate caller name and construct formatted greeting components.

    Args:
        name: Name of the caller to greet.
        salutation: Salutation prefix to use.
        max_name_length: Maximum allowed length for caller name.

    Returns:
        Tuple of (formatted_message, trimmed_name, effective_salutation).

    Raises:
        ValueError: If name is empty, blank, non-string, or exceeds max_name_length.
    """
    if not hasattr(name, "strip") or not name.strip():
        raise ValueError("Caller name must not be empty or blank")

    trimmed_name = name.strip()

    if len(trimmed_name) > max_name_length:
        msg = f"Caller name exceeds maximum allowed length of {max_name_length}"
        raise ValueError(msg)

    effective_salutation = (
        salutation.strip() if salutation and salutation.strip() else "Hello"
    )
    formatted_message = f"{effective_salutation}, {trimmed_name}!"
    return formatted_message, trimmed_name, effective_salutation


class GreetingServiceImpl(GreetingService):
    """Implementation of GreetingService protocol."""

    def __init__(
        self,
        default_salutation: str = "Hello",
        max_name_length: int = 100,
    ) -> None:
        """Initialize the greeting service with configuration parameters.

        Args:
            default_salutation: Default salutation prefix.
            max_name_length: Maximum allowed character length for caller names.
        """
        self._default_salutation = default_salutation
        self._max_name_length = max_name_length

    @override
    async def generate_greeting(self, request: GreetingRequest) -> GreetingResponse:
        """Generate a deterministic greeting message for the caller.

        Args:
            request: The greeting request containing caller name and
                optional salutation.

        Returns:
            GreetingResponse containing the formatted greeting.

        Raises:
            ValueError: If caller name is empty, blank, or exceeds max length.
        """
        salutation = (
            request.salutation
            if request.salutation is not None
            else self._default_salutation
        )
        message, trimmed_name, effective_salutation = generate_greeting_message(
            name=request.name,
            salutation=salutation,
            max_name_length=self._max_name_length,
        )
        return GreetingResponse(
            message=message,
            name=trimmed_name,
            salutation=effective_salutation,
        )


async def _run_usage_example() -> None:
    """Run the bounded, deterministic usage demonstration.

    Raises:
        RuntimeError: If greeting output or error handling assertion fails.
    """
    service = GreetingServiceImpl(default_salutation="Hello", max_name_length=100)

    # Scenario 1: Standard greeting with default salutation
    req1 = GreetingRequest(name="Alice")
    res1 = await service.generate_greeting(req1)
    if res1.message != "Hello, Alice!":
        err_msg = f"Unexpected greeting output: {res1.message}"
        raise RuntimeError(err_msg)
    print(f"Scenario 1 (Default greeting): {res1.message}")

    # Scenario 2: Custom salutation
    req2 = GreetingRequest(name="  Bob  ", salutation="Welcome")
    res2 = await service.generate_greeting(req2)
    if res2.message != "Welcome, Bob!":
        err_msg = f"Unexpected greeting output: {res2.message}"
        raise RuntimeError(err_msg)
    print(f"Scenario 2 (Custom salutation): {res2.message}")

    # Scenario 3: Validation error handling - empty name
    try:
        await service.generate_greeting(GreetingRequest(name="   "))
        err_msg = "Expected ValueError for empty name was not raised"
        raise RuntimeError(err_msg)
    except ValueError as e:
        print(f"Scenario 3 (Empty name rejection): Caught expected error '{e}'")

    # Scenario 4: Validation error handling - length exceeded
    try:
        await service.generate_greeting(GreetingRequest(name="A" * 101))
        err_msg = "Expected ValueError for excessive name length was not raised"
        raise RuntimeError(err_msg)
    except ValueError as e:
        print(f"Scenario 4 (Excessive length rejection): Caught expected error '{e}'")

    print("[SUCCESS] All usage demonstration scenarios passed.")


if __name__ == "__main__":
    asyncio.run(_run_usage_example())
