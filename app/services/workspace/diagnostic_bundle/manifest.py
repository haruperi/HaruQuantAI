"""Feature specification for Diagnostic Bundle."""

from app.contracts.workspace.capabilities import (
    BUILD_DIAGNOSTICS_CAPABILITY,
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-BUILD_DIAGNOSTICS",
    domain="workspace",
    provides=frozenset({BUILD_DIAGNOSTICS_CAPABILITY}),
    requires=frozenset(
        {
            MANAGE_WORKSPACES_CAPABILITY,
            CONFIGURE_RUNTIME_CAPABILITY,
        }
    ),
    optional=frozenset({SECURE_LOCAL_ACCESS_CAPABILITY}),
    conflicts=frozenset(),
    description="Produce a redacted diagnostic bundle.",
    state=None,
    config_keys=frozenset(),
)
