"""Define boundary-safe shared exceptions for domain extension.

Exceptions retain only validated symbolic tokens and never wrap raw provider
objects or messages that could leak through an application boundary.
"""

import re

_SYMBOLIC_TOKEN = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


class HaruQuantError(Exception):
    """Represent a failure using only boundary-safe symbolic evidence.

    Attributes:
        code: Stable uppercase category token supplied by the owning domain.
        detail: Stable uppercase detail token safe for boundary mapping.
    """

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize a shared exception with safe symbolic tokens.

        Args:
            code: Uppercase symbolic failure category.
            detail: Uppercase symbolic detail, defaulting to ``UNSPECIFIED``.

        Raises:
            ValueError: Either token violates the symbolic-token grammar.
        """
        if _SYMBOLIC_TOKEN.fullmatch(code) is None:
            raise ValueError("code must be an uppercase symbolic token")
        if _SYMBOLIC_TOKEN.fullmatch(detail) is None:
            raise ValueError("detail must be an uppercase symbolic token")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


class ConfigurationError(HaruQuantError):
    """Represent invalid or unavailable configuration evidence."""


class ValidationError(HaruQuantError):
    """Represent an invalid value at a shared boundary."""


class SecurityError(HaruQuantError):
    """Represent a security-policy or secret-handling failure."""


class ExternalServiceError(HaruQuantError):
    """Represent a sanitized external-service boundary failure."""
