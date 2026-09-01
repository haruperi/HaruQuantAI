"""Feature specification for explicit Broker provider dispatch."""

from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.contracts.broker.internal import PROVIDER_GATEWAY_CAPABILITIES
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-DISPATCH_PROVIDERS",
    domain="brokers",
    provides=frozenset(
        {
            MANAGE_SESSIONS_CAPABILITY,
            READ_PROVIDER_STATE_CAPABILITY,
            TRANSPORT_ORDERS_CAPABILITY,
        }
    ),
    requires=frozenset(),
    optional=frozenset(PROVIDER_GATEWAY_CAPABILITIES),
    conflicts=frozenset(),
    description=(
        "Dispatch Broker requests to exactly one installed provider profile; "
        "never perform implicit provider fallback."
    ),
    config_keys=frozenset({"reject_duplicate_profiles"}),
)
