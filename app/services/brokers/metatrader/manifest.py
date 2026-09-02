"""Feature specification for MetaTrader 5 Connection."""

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
)
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-METATRADER",
    domain="broker",
    provides=frozenset({PROVIDER_METATRADER_CAPABILITY, BROKER_OPERATIONS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Live MetaTrader 5 direct client connection and operations provider.",
    state=StateDeclaration(
        namespace="broker.metatrader",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="MetaTrader 5 connection configuration and channel state",
    ),
    config_keys=frozenset(
        {"database_path", "terminal_path", "login", "password", "server", "timeout"}
    ),
)
