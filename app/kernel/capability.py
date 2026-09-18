"""Typed Capability Tokens for Decoupled Service Injection.

In modular architectures, features often need to collaborate. If Feature A
directly imports Feature B's concrete implementation, the two become tightly
coupled, difficult to test in isolation, and prone to circular dependency errors.

To solve this, the runtime uses Capability Tokens:
- A `Capability` is an immutable, typed token representing an abstract contract
  or protocol.
- Provider features register their concrete implementations into the application
  context under a specific `Capability` key.
- Consumer features request that `Capability` from the context at startup.

Thanks to Python 3.12+ PEP 695 generics (`class Capability[T]`), static type
checkers (such as mypy and IDE autocomplete) know the exact type returned by
`ctx.require(KEY)` without requiring any direct import of concrete classes.

Example:
    Define a public capability token in a shared contract module:
    >>> from typing import Protocol
    >>> class AuthService(Protocol):
    ...     def authenticate(self, token: str) -> bool: ...
    >>> AUTH = Capability[AuthService]("auth.service", major=1)

    A provider registers its implementation:
    >>> ctx.provide(AUTH, RealAuthService())

    A consumer safely retrieves it with full static type verification:
    >>> auth_service = ctx.require(AUTH)
    >>> is_valid = auth_service.authenticate("secret_token")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import override


@dataclass(frozen=True)
class Capability[T]:
    """Identify a public service contract; T is enforced by static type checking.

    A `Capability` acts as a unique, strongly typed token used to store and
    retrieve services from `Context` and `Runtime`. Think of it like a unique
    key to a specific locker: the `Context` is the locker room, and the
    `Capability` ensures you open the exact locker you need with full static
    type safety.

    Attributes:
        name: A unique, human-readable string identifying the capability
            (e.g., "auth.service", "database.pool").
        major: Positive integer representing the major contract version
            (e.g., 1 for "auth.service@1"). Changing the major version indicates
            a breaking change in the public contract protocol.
        description: An optional human-readable explanation of what service or
            responsibility this capability represents.
    """

    name: str
    major: int = 1
    description: str = field(default="", compare=False, hash=False)

    def __post_init__(self) -> None:
        """Validate token names and positive major version numbers.

        Raises:
            ValueError: If name is empty or whitespace, or if major < 1.
        """
        if not self.name.strip() or self.major < 1:
            raise ValueError("Capabilities require a name and a positive major")

    @property
    def identifier(self) -> str:
        """Return the fully qualified capability identifier string.

        Returns:
            Formatted string identifier for the capability (e.g. 'auth.service@1').
        """
        return f"{self.name}@{self.major}"

    @override
    def __repr__(self) -> str:
        """Return a readable developer string representation.

        Returns:
            Formatted representation (e.g. "Capability('auth.service', major=1)").
        """
        return f"Capability({self.name!r}, major={self.major})"


class CapabilityUnavailableError(LookupError):
    """Exception raised when a declared capability has no active provider.

    Attributes:
        capability: Identifier or name of the capability that was requested.
        blocked_by: Optional name of the upstream dependency that caused the failure.
    """

    def __init__(self, capability: str, *, blocked_by: str | None = None) -> None:
        """Initialize the missing capability error.

        Args:
            capability: Name or identifier of the missing capability.
            blocked_by: Optional name of the dependency that failed or blocked it.
        """
        self.capability = capability
        self.blocked_by = blocked_by
        message = capability
        if blocked_by:
            message += f" (blocked by {blocked_by!r})"
        super().__init__(message)
