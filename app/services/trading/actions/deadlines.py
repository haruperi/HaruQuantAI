"""Injected asynchronous deadline authority for Trading evaluation cycles."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from contextlib import AbstractAsyncContextManager
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.services.trading.contracts.models import JsonValue


class EvaluationDeadlineFactory(Protocol):
    """Construct one route-owned deadline context for an evaluation cycle."""

    def __call__(
        self,
        timeout_seconds: Decimal,
        evidence: Mapping[str, JsonValue],
    ) -> AbstractAsyncContextManager[object]:
        """Return a context that raises ``TimeoutError`` at its exact bound."""
        ...


def create_monotonic_deadline_factory(
    monotonic: Callable[[], float],
) -> EvaluationDeadlineFactory:
    """Create the live/demo adapter over the event loop's monotonic clock.

    Args:
        monotonic: Explicit event-loop-compatible monotonic clock.

    Returns:
        Structural asynchronous deadline context factory.
    """

    def factory(
        timeout_seconds: Decimal,
        evidence: Mapping[str, JsonValue],
    ) -> AbstractAsyncContextManager[object]:
        del evidence
        deadline = monotonic() + float(timeout_seconds)
        return asyncio.timeout_at(deadline)

    return factory


__all__ = ["EvaluationDeadlineFactory", "create_monotonic_deadline_factory"]
