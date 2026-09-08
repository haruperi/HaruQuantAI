"""Feature specification for immutable artifact custody."""

from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import ARTIFACTS_CAPABILITY, PERSISTENCE_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-WS-MANAGE_ARTIFACTS",
    domain="workspace",
    provides=frozenset({ARTIFACTS_CAPABILITY}),
    requires=frozenset({PERSISTENCE_CAPABILITY, RESERVE_RESOURCES_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Publish, authorize, retain and clean immutable artifact bytes under Workspace custody.",
    state=StateDeclaration(
        namespace="workspace.artifacts",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Immutable artifact metadata, references and legal holds.",
    ),
    config_keys=frozenset(),
)
