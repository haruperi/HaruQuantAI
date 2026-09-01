"""Broker runtime capability keys.

The Broker domain intentionally exposes only provider session lifecycle,
provider-truth reads, and authorized order transport. Runtime availability,
provider selection, permissions, environment admission, and adapter certification
belong to Kernel/Composition, Workspace/Trading/Risk, and tests/CI respectively.
"""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.broker.ports import (
        ManageSessionsCapability,
        ReadProviderStateCapability,
        TransportOrdersCapability,
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
