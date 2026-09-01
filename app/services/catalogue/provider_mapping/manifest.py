"""Feature specification for Provider and Broker Mapping."""

from app.contracts.catalogue.capabilities import MAP_PROVIDERS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-CAT-MAP_PROVIDERS",
    domain="catalogue",
    provides=frozenset({MAP_PROVIDERS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Map broker and provider identities to canonical instruments.",
    state=StateDeclaration(
        namespace="catalogue.provider_mappings",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Retained external provider and broker symbol mappings.",
    ),
    config_keys=frozenset({"database_path"}),
)
