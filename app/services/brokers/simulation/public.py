"""Function-only public operations for the simulation broker channel."""

from __future__ import annotations

from datetime import datetime

from app.services.brokers._shared.factory import create_broker_adapter
from app.services.brokers.canonical_contracts import (
    BrokerAdapter,
    BrokerConnectionConfig,
    StandardResponse,
)
from app.services.brokers.simulation.adapter import SimulationBrokerAdapter
from app.services.brokers.simulation.contracts import SimulationReadEnvelope


def build_simulation_read_envelope(
    *,
    payload: object,
    source_sequence: int,
    observed_at: datetime,
    received_at: datetime,
    available_at: datetime,
    simulated_at: datetime,
    stale: bool = False,
    gap: bool = False,
    duplicate: bool = False,
    out_of_order: bool = False,
    session_revision: str | None = None,
) -> object:
    """Build one authority-owned simulation read envelope.

    Args:
        payload: Already-canonical authoritative payload.
        source_sequence: Monotonic source sequence for this read stream.
        observed_at: Provider or ledger observation time.
        received_at: Broker receipt time.
        available_at: Earliest simulated availability time.
        simulated_at: Injected simulated clock value.
        stale: Whether the authority marks the observation stale.
        gap: Whether delivery has a known sequence gap.
        duplicate: Whether delivery duplicates a prior observation.
        out_of_order: Whether delivery arrived out of source order.
        session_revision: Optional injected Data evidence revision.

    Returns:
        Opaque Brokers-owned envelope for an authority port.
    """
    return SimulationReadEnvelope(
        payload=payload,
        source_sequence=source_sequence,
        observed_at=observed_at,
        received_at=received_at,
        available_at=available_at,
        simulated_at=simulated_at,
        stale=stale,
        gap=gap,
        duplicate=duplicate,
        out_of_order=out_of_order,
        session_revision=session_revision,
    )


def create_simulation_broker_adapter(
    config: object, authority_port: object
) -> StandardResponse[BrokerAdapter]:
    """Create the exact socket-free simulation adapter.

    Args:
        config: Root-built broker connection configuration.
        authority_port: Structurally typed authority implementation.

    Returns:
        Canonical factory response.

    Raises:
        TypeError: If ``config`` is not a broker configuration.
    """
    if not isinstance(config, BrokerConnectionConfig):
        raise TypeError("config must be a BrokerConnectionConfig")
    return create_broker_adapter(config.broker_id, config, authority_port)


async def finalize_simulation_broker_session(
    adapter: object,
) -> StandardResponse[None]:
    """Finalize one simulation adapter session.

    Args:
        adapter: Opaque simulation adapter returned by the package root.

    Returns:
        Canonical finalization response.

    Raises:
        TypeError: If ``adapter`` is not a simulation adapter.
    """
    if not isinstance(adapter, SimulationBrokerAdapter):
        raise TypeError("adapter must be a simulation broker adapter")
    return await adapter.finalize_session()


__all__ = (
    "build_simulation_read_envelope",
    "create_simulation_broker_adapter",
    "finalize_simulation_broker_session",
)
