"""Feature specification for Broker Provider Gateway."""

from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
    PROVIDER_CTRADER_CAPABILITY,
    PROVIDER_DUKASCOPY_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
    PROVIDER_YAHOO_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
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
    optional=frozenset(
        {
            PROVIDER_METATRADER_CAPABILITY,
            PROVIDER_CTRADER_CAPABILITY,
            PROVIDER_BINANCE_CAPABILITY,
            PROVIDER_DUKASCOPY_CAPABILITY,
            PROVIDER_YAHOO_CAPABILITY,
        }
    ),
    conflicts=frozenset(),
    description=(
        "Dispatch explicitly addressed Broker operations to mounted provider backends "
        "without fallback or cross-provider ranking."
    ),
    state=None,
    config_keys=frozenset(),
)
