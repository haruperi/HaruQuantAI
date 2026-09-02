"""Broker domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.broker.ports import (
        BrokerResolverCapability,
        ManageSessionsCapability,
        ProviderBackend,
        ReadProviderStateCapability,
        TransportOrdersCapability,
    )

BROKER_RESOLVER_CAPABILITY: CapabilityKey[BrokerResolverCapability] = CapabilityKey(
    name="broker.resolver",
    major=1,
)

MANAGE_SESSIONS_CAPABILITY: CapabilityKey[ManageSessionsCapability] = CapabilityKey(
    name="broker.manage-sessions",
    major=1,
)

READ_PROVIDER_STATE_CAPABILITY: CapabilityKey[ReadProviderStateCapability] = (
    CapabilityKey(
        name="broker.read-provider-state",
        major=1,
    )
)

TRANSPORT_ORDERS_CAPABILITY: CapabilityKey[TransportOrdersCapability] = CapabilityKey(
    name="broker.transport-orders",
    major=1,
)

PROVIDER_METATRADER_CAPABILITY: CapabilityKey[ProviderBackend] = CapabilityKey(
    name="broker.provider.metatrader",
    major=1,
)

PROVIDER_CTRADER_CAPABILITY: CapabilityKey[ProviderBackend] = CapabilityKey(
    name="broker.provider.ctrader",
    major=1,
)

PROVIDER_BINANCE_CAPABILITY: CapabilityKey[ProviderBackend] = CapabilityKey(
    name="broker.provider.binance",
    major=1,
)

PROVIDER_DUKASCOPY_CAPABILITY: CapabilityKey[ProviderBackend] = CapabilityKey(
    name="broker.provider.dukascopy",
    major=1,
)

PROVIDER_YAHOO_CAPABILITY: CapabilityKey[ProviderBackend] = CapabilityKey(
    name="broker.provider.yahoo",
    major=1,
)
