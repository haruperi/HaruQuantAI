"""Structural authority contract for the socket-free simulation channel."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.services.brokers.canonical_contracts import (
    BrokerAdapter,
    BrokerCapabilityId,
    StandardResponse,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationReadEnvelope:
    """Authority-owned canonical payload and delivery evidence."""

    payload: object
    source_sequence: int
    observed_at: datetime
    received_at: datetime
    available_at: datetime
    simulated_at: datetime
    stale: bool = False
    gap: bool = False
    duplicate: bool = False
    out_of_order: bool = False
    session_revision: str | None = None


@runtime_checkable
class SimulationAuthorityPort(BrokerAdapter, Protocol):
    """Brokers-owned delegation surface implemented by an injected authority."""

    async def finalize_session(self) -> StandardResponse[None]:
        """Finalize the injected run-scoped session.

        Returns:
            Canonical finalization response.
        """
        ...

    async def read(
        self,
        operation: BrokerCapabilityId,
        arguments: Mapping[str, object],
    ) -> SimulationReadEnvelope:
        """Return one canonical authority read with delivery evidence.

        Args:
            operation: Admitted canonical read capability.
            arguments: Immutable public-call arguments.

        Returns:
            Canonical payload and authoritative timing/sequence evidence.
        """
        ...


__all__ = ("SimulationAuthorityPort", "SimulationReadEnvelope")
