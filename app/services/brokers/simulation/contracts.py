"""Structural authority contract for the socket-free simulation channel."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.services.brokers.canonical_contracts import BrokerAdapter, StandardResponse


@runtime_checkable
class SimulationAuthorityPort(BrokerAdapter, Protocol):
    """Brokers-owned delegation surface implemented by an injected authority."""

    async def finalize_session(self) -> StandardResponse[None]:
        """Finalize the injected run-scoped session.

        Returns:
            Canonical finalization response.
        """
        ...


__all__ = ("SimulationAuthorityPort",)
