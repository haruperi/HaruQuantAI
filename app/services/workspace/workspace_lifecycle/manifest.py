"""Feature specification for Workspace Lifecycle."""

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
    description="Initialize, migrate, lock, recover, and back up a workspace.",
    state=StateDeclaration(
        namespace="workspace",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Workspace metadata database, schema migrations, and leases",
    ),
    config_keys=frozenset(),
)
