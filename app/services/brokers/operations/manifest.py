"""Feature specification for Broker Operations."""

from app.contracts.broker.capabilities import BROKER_OPERATIONS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-OPERATIONS",
    domain="broker",
    provides=frozenset({BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Standard broker neutral operational functions without business logic.",
    state=StateDeclaration(
        namespace="broker.operations",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Broker operations subscriptions and execution tracking",
    ),
    config_keys=frozenset({"database_path"}),
)
