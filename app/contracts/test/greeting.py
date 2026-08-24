"""Greeting capability contract for the temporary test domain."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey


@dataclass(frozen=True, slots=True)
class GreetingRequest:
    """Request payload for greeting generation.

    Attributes:
        name: Name of the caller to greet.
        salutation: Optional custom salutation overriding the default.
    """

    name: str
    salutation: str | None = None


@dataclass(frozen=True, slots=True)
class GreetingResponse:
    """Response payload containing the generated greeting.

    Attributes:
        message: Formatted deterministic greeting string.
        name: Trimmed name of the caller.
        salutation: Salutation used in the greeting.
    """

    message: str
    name: str
    salutation: str


@runtime_checkable
class GreetingService(Protocol):
    """Protocol for greeting generation providers."""

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
        ...


GREETING_SERVICE = CapabilityKey[GreetingService](
    name="test.greeting",
    major=1,
)
