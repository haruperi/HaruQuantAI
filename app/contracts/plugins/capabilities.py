"""Plugins domain capability keys."""

from typing import TYPE_CHECKING

from app.kernel.capability import CapabilityKey

if TYPE_CHECKING:
    from app.contracts.plugins.ports import (
        DeclareManifestsCapability,
        IsolateAnalysisCapability,
        MaintainCompatibilityCapability,
        ManageLifecycleCapability,
        RegisterContributionsCapability,
        RenderResultPanelsCapability,
        SandboxPermissionsCapability,
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

MANAGE_LIFECYCLE_CAPABILITY: CapabilityKey[ManageLifecycleCapability] = CapabilityKey(
    name="plugins.manage-lifecycle",
    major=1,
)

SANDBOX_PERMISSIONS_CAPABILITY: CapabilityKey[SandboxPermissionsCapability] = (
    CapabilityKey(
        name="plugins.sandbox-permissions",
        major=1,
    )
)

ISOLATE_ANALYSIS_CAPABILITY: CapabilityKey[IsolateAnalysisCapability] = CapabilityKey(
    name="plugins.isolate-analysis",
    major=1,
)

RENDER_RESULT_PANELS_CAPABILITY: CapabilityKey[RenderResultPanelsCapability] = (
    CapabilityKey(
        name="plugins.render-result-panels",
        major=1,
    )
)

MAINTAIN_COMPATIBILITY_CAPABILITY: CapabilityKey[MaintainCompatibilityCapability] = (
    CapabilityKey(
        name="plugins.maintain-compatibility",
        major=1,
    )
)
