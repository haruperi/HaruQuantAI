"""Plugins domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.plugins.ports import DeclareManifestsCapability

DECLARE_MANIFESTS_CAPABILITY: CapabilityKey[DeclareManifestsCapability] = CapabilityKey(
    name="plugins.declare-manifests",
    major=1,
)
