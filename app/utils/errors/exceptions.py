"""Minimal shared exception hierarchy for domain extension."""

from __future__ import annotations

import re

_SYMBOLIC_TOKEN = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")


class HaruQuantError(Exception):
    """Base exception carrying only boundary-safe symbolic evidence."""

    def __init__(self, code: str, detail: str = "UNSPECIFIED") -> None:
        """Initialize a shared exception.

        Args:
            code: Uppercase symbolic error code.
            detail: Uppercase symbolic safe detail.

        Raises:
            ValueError: If either token is malformed.
        """
        if _SYMBOLIC_TOKEN.fullmatch(code) is None:
            raise ValueError("code must be an uppercase symbolic token")
        if _SYMBOLIC_TOKEN.fullmatch(detail) is None:
            raise ValueError("detail must be an uppercase symbolic token")
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}")


class ConfigurationError(HaruQuantError):
    """Invalid or unavailable configuration."""


class ValidationError(HaruQuantError):
    """Invalid shared-boundary value."""


class SecurityError(HaruQuantError):
    """Security policy or secret-resolution failure."""


class ExternalServiceError(HaruQuantError):
    """External service boundary failure."""
