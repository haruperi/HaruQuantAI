"""Feature specification for workspace management."""

from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-MANAGE_WORKSPACES",
    domain="workspace",
    provides=frozenset({MANAGE_WORKSPACES_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Open, fence, recover, back up, and restore a workspace.",
    state=StateDeclaration(
        namespace="workspace",
        schema_version=2,
        retention_policy=RetentionPolicy.RETAIN,
        description="Workspace metadata database, schema migrations, and leases",
    ),
    config_keys=frozenset(
        {
            "auto_migrate",
            "busy_timeout_seconds",
            "staged_grace_period_seconds",
            "max_manifest_files",
            "max_backup_bytes",
        }
    ),
)
