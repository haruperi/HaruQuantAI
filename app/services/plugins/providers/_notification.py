"""Shared transport adapter primitives for notification provider plugins."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class NotificationBackend(Protocol):
    """Minimal backend consumed by a notification provider adapter."""

    @property
    def active(self) -> bool:
        """Return whether external delivery is ready."""
        ...

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> Mapping[str, object] | None:
        """Attempt one transport-specific delivery."""
        ...


class DisabledNotificationBackend:
    """Explicitly disabled backend for offline usage examples."""

    active = False

    def send(
        self, title: str, text: str, html_body: str | None = None
    ) -> Mapping[str, object] | None:
        """Reject delivery because this backend is intentionally disabled.

        Raises:
            RuntimeError: Always, because no transport is configured.
        """
        del title, text, html_body
        raise RuntimeError("notification backend is disabled")


def validate_backend(value: object, provider_name: str) -> NotificationBackend:
    """Validate a structurally compatible injected backend.

    Returns:
        Validated notification backend.

    Raises:
        ValueError: If the object lacks required backend members.
    """
    if not hasattr(value, "active") or not callable(getattr(value, "send", None)):
        message = f"{provider_name} notification provider requires only 'configuration'"
        raise ValueError(message)
    return value  # type: ignore[return-value]


def recipient_count(result: Mapping[str, object] | None) -> int:
    """Extract a safe recipient count from a backend result.

    Returns:
        Non-negative recipient count, defaulting to one.
    """
    if result is None:
        return 1
    raw_count = result.get("recipients")
    if (
        isinstance(raw_count, int)
        and not isinstance(raw_count, bool)
        and raw_count >= 0
    ):
        return raw_count
    if isinstance(raw_count, str) and raw_count.isdecimal():
        return int(raw_count)
    return 1
