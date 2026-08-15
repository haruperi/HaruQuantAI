"""Function-only public operations for the simulation broker channel."""

from __future__ import annotations

from app.services.brokers._shared.factory import create_broker_adapter
from app.services.brokers.canonical_contracts import (
    BrokerAdapter,
    BrokerConnectionConfig,
    StandardResponse,
)
from app.services.brokers.simulation.adapter import SimulationBrokerAdapter


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
    "create_simulation_broker_adapter",
    "finalize_simulation_broker_session",
)
