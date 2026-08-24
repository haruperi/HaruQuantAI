"""Feature specification for Local Access and Health."""

from app.contracts.workspace.capabilities import (
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-SECURE_LOCAL_ACCESS",
    domain="workspace",
    provides=frozenset({SECURE_LOCAL_ACCESS_CAPABILITY}),
    requires=frozenset({MANAGE_WORKSPACES_CAPABILITY}),
    optional=frozenset({CONFIGURE_RUNTIME_CAPABILITY}),
    conflicts=frozenset(),
    description="Issue local credentials and report health/readiness.",
    state=None,
    config_keys=frozenset(),
)
