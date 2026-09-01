"""Feature specification for transactional plugin lifecycle management."""

from app.contracts.plugins.capabilities import (
    DECLARE_MANIFESTS_CAPABILITY,
    MANAGE_LIFECYCLE_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-PLUG-MANAGE_LIFECYCLE",
    domain="plugins",
    provides=frozenset({MANAGE_LIFECYCLE_CAPABILITY}),
    requires=frozenset({DECLARE_MANIFESTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Persist and transactionally replace plugin package activations.",
    state=StateDeclaration(
        namespace="plugins.lifecycle",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained plugin receipts, immutable versions, and workspace activations."
        ),
    ),
    config_keys=frozenset({"database_path"}),
)
