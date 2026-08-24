"""Plugins domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.plugins.ports import (
        DeclareManifestsCapability,
        RegisterContributionsCapability,
    )

DECLARE_MANIFESTS_CAPABILITY: CapabilityKey[DeclareManifestsCapability] = CapabilityKey(
    name="plugins.declare-manifests",
    major=1,
)

REGISTER_CONTRIBUTIONS_CAPABILITY: CapabilityKey[RegisterContributionsCapability] = (
    CapabilityKey(
        name="plugins.register-contributions",
        major=1,
    )
)
