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


@dataclass(frozen=True, slots=True, kw_only=True)
class SimulationMutationEnvelope:
    """Authority result bound to the exact immutable mutation request."""

    provider_result: object
    request_echo: object
    simulated_at: datetime
    projected_position: object | None = None
    seeded_fault: bool = False


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

    async def mutate(
        self,
        operation: BrokerCapabilityId,
        request: object,
    ) -> SimulationMutationEnvelope:
        """Return one provider-shaped mutation acknowledgement.

        Args:
            operation: Admitted canonical mutation capability.
            request: Exact immutable canonical request or argument tuple.

        Returns:
            Provider-shaped result bound to the unchanged request.
        """
        ...


__all__ = (
    "SimulationAuthorityPort",
    "SimulationMutationEnvelope",
    "SimulationReadEnvelope",
)
