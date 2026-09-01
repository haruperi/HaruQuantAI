"""Public capability protocols (ports) for Broker capabilities."""

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
    """Capability protocol for provider session lifecycle operations."""

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Open, transition, reconnect, assess, and close fenced sessions.

        Args:
            request: Operation-discriminated session lifecycle request.

        Returns:
            The session reference, state, and readiness on success,
            otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class ReadProviderStateCapability(Protocol):
    """Capability protocol for provider-truth read operations."""

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read and normalize genuine provider account and market state.

        Args:
            request: Operation-discriminated provider-truth read request.

        Returns:
            The account snapshot, trading state, market state, or history
            page on success, otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class TransportOrdersCapability(Protocol):
    """Capability protocol for authorized execution transport operations."""

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Validate, submit, cancel, modify, and journal transport requests.

        Args:
            request: Operation-discriminated execution transport request.

        Returns:
            The operation outcome, receipt, and correlation identity on
            success, otherwise a structured broker failure.
        """
        ...


@runtime_checkable
class ProviderBackend(Protocol):
    """Typed provider-backend port implemented by each provider feature.

    One mounted provider (MetaTrader, cTrader, Binance, Dukascopy, or
    Yahoo) exposes exactly this protocol through its
    ``broker.provider.<name>@1`` capability. The gateway dispatches one
    explicitly addressed request to one mounted backend; absence fails
    capability-unavailable and there is no ranking, selection, failover,
    or retry across providers, and no business authorization,
    reconciliation, or idempotency policy lives here.
    """

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Handle one explicitly addressed provider session operation."""
        ...

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Read genuine provider truth for one explicitly addressed read."""
        ...

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Transport one upstream-authorized provider order operation."""
        ...
