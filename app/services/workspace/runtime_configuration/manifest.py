"""Feature specification for Runtime Configuration and Admission."""

from app.contracts.workspace.capabilities import (
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-CONFIGURE_RUNTIME",
    domain="workspace",
    provides=frozenset({CONFIGURE_RUNTIME_CAPABILITY}),
    requires=frozenset({MANAGE_WORKSPACES_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Validate settings, resource guards, launcher settings, and "
    "support profiles.",
    state=StateDeclaration(
        namespace="workspace",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Versioned workspace settings persisted in the "
        "workspace_setting_versions table of the workspace metadata database",
    ),
    config_keys=frozenset(),
)
