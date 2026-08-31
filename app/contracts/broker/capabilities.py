"""Broker domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.broker.ports import (
        CertifyAdaptersCapability,
        ConfigureProvidersCapability,
        DeclareCapabilitiesCapability,
        IsolateEnvironmentsCapability,
        ManageSessionsCapability,
        ReadProviderStateCapability,
        TransportOrdersCapability,
    )

DECLARE_CAPABILITIES_CAPABILITY: CapabilityKey[DeclareCapabilitiesCapability] = (
    CapabilityKey(
        name="broker.declare-capabilities",
        major=1,
    )
)

CONFIGURE_PROVIDERS_CAPABILITY: CapabilityKey[ConfigureProvidersCapability] = (
    CapabilityKey(
        name="broker.configure-providers",
        major=1,
    )
)

ISOLATE_ENVIRONMENTS_CAPABILITY: CapabilityKey[IsolateEnvironmentsCapability] = (
    CapabilityKey(
        name="broker.isolate-environments",
        major=1,
    )
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

CERTIFY_ADAPTERS_CAPABILITY: CapabilityKey[CertifyAdaptersCapability] = CapabilityKey(
    name="broker.certify-adapters",
    major=1,
)
