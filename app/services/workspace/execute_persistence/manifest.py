"""Feature specification for bounded persistence execution."""

from app.contracts.workspace.capabilities import (
    MANAGE_WORKSPACES_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-EXECUTE_PERSISTENCE",
    domain="workspace",
    provides=frozenset({PERSISTENCE_CAPABILITY}),
    requires=frozenset({MANAGE_WORKSPACES_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Execute bounded feature-owned transactions, ordered additive migrations, "
        "and immutable append-only evidence."
    ),
    state=StateDeclaration(
        namespace="workspace_persistence",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Feature migrations, revisions, idempotency receipts, and evidence",
    ),
    config_keys=frozenset(
        {
            "busy_timeout_seconds",
            "max_export_limit",
            "max_statements_per_tx",
        }
    ),
)
