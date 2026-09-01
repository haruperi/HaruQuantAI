"""Internal Broker provider-gateway contracts.

These contracts are feature-to-feature only and are intentionally absent from the
public wire registry. Each concrete provider publishes exactly one provider-local
gateway capability; the dispatcher consumes any installed gateways and is the only
feature that republishes the three public Broker capability bundles.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.broker.errors import BrokerFailure
    from app.contracts.broker.models import (
        BrokerProviderKind,
        BrokerSessionRef,
        ManageSessionsRequest,
        ManageSessionsSuccess,
        ReadProviderStateRequest,
        ReadProviderStateSuccess,
        TransportOrdersRequest,
        TransportOrdersSuccess,
    )
    from app.contracts.common.models import Uuid7


@runtime_checkable
class BrokerProviderGateway(Protocol):
    """Provider-local gateway consumed only by the Broker dispatcher."""

    @property
    def provider_kind(self) -> BrokerProviderKind:
        """Return the fixed provider kind implemented by this feature."""
        ...

    @property
    def profile_id(self) -> Uuid7:
        """Return the configured immutable provider-profile identity."""
        ...

    @property
    def supports_order_transport(self) -> bool:
        """Return whether this provider can perform external order transport."""
        ...

    def accepts(self, session: BrokerSessionRef) -> bool:
        """Return whether this feature owns the exact session profile."""
        ...

    async def manage_sessions(
        self,
        request: ManageSessionsRequest,
    ) -> ManageSessionsSuccess | BrokerFailure:
        """Execute provider-local session lifecycle behavior."""
        ...

    async def read_provider_state(
        self,
        request: ReadProviderStateRequest,
    ) -> ReadProviderStateSuccess | BrokerFailure:
        """Execute provider-local genuine reads."""
        ...

    async def transport_orders(
        self,
        request: TransportOrdersRequest,
    ) -> TransportOrdersSuccess | BrokerFailure:
        """Execute provider-local authorized mutation transport."""
        ...


MT5_PROVIDER_GATEWAY_CAPABILITY: CapabilityKey[BrokerProviderGateway] = CapabilityKey(
    name="broker.provider.mt5",
    major=1,
)
CTRADER_PROVIDER_GATEWAY_CAPABILITY: CapabilityKey[BrokerProviderGateway] = (
    CapabilityKey(name="broker.provider.ctrader", major=1)
)
BINANCE_PROVIDER_GATEWAY_CAPABILITY: CapabilityKey[BrokerProviderGateway] = (
    CapabilityKey(name="broker.provider.binance", major=1)
)
DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY: CapabilityKey[BrokerProviderGateway] = (
    CapabilityKey(name="broker.provider.dukascopy", major=1)
)
YAHOO_PROVIDER_GATEWAY_CAPABILITY: CapabilityKey[BrokerProviderGateway] = CapabilityKey(
    name="broker.provider.yahoo",
    major=1,
)

PROVIDER_GATEWAY_CAPABILITIES: tuple[CapabilityKey[BrokerProviderGateway], ...] = (
    MT5_PROVIDER_GATEWAY_CAPABILITY,
    CTRADER_PROVIDER_GATEWAY_CAPABILITY,
    BINANCE_PROVIDER_GATEWAY_CAPABILITY,
    DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY,
    YAHOO_PROVIDER_GATEWAY_CAPABILITY,
)
