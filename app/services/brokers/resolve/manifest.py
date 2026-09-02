"""Feature specification for Service-Level Broker Resolver."""

from app.contracts.broker.capabilities import BROKER_RESOLVER_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-RESOLVE",
    domain="broker",
    provides=frozenset({BROKER_RESOLVER_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Centralizes active broker module selection so API routes do not own "
    "broker adapter policy.",
    state=StateDeclaration(
        namespace="broker.resolve",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Active broker definitions and mappings in haruquantai.db",
    ),
    config_keys=frozenset({"database_path"}),
)
