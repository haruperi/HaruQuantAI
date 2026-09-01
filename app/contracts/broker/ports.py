"""Public Broker capability protocols.

Brokers is a thin external-provider integration boundary. These are the only
runtime capability bundles exposed by the domain; provider discovery and routing
are composition concerns implemented by the Broker dispatcher feature.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from app.contracts.broker.errors import BrokerFailure
    from app.contracts.broker.models import (
        ManageSessionsRequest,
        ManageSessionsSuccess,
        ReadProviderStateRequest,
        ReadProviderStateSuccess,
        TransportOrdersRequest,
        TransportOrdersSuccess,
    )


@runtime_checkable
class ManageSessionsCapability(Protocol):
    """Provider session lifecycle operations."""

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Open, transition, reconnect, assess, and close fenced sessions."""
        ...


@runtime_checkable
class ReadProviderStateCapability(Protocol):
    """Genuine provider-truth read operations."""

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read normalized account, trading, market, or bounded history state."""
        ...


@runtime_checkable
class TransportOrdersCapability(Protocol):
    """Authorized provider order-transport operations."""

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Validate or transmit one already-authorized provider operation."""
        ...
