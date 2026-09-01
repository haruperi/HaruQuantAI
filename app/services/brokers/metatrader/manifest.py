"""Feature specification for MetaTrader external-provider connectivity."""

from app.contracts.broker.internal import MT5_PROVIDER_GATEWAY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_METATRADER",
    domain="brokers",
    provides=frozenset({MT5_PROVIDER_GATEWAY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Own one removable MetaTrader provider session, provider-truth reads, "
        "and authorized external order transport."
    ),
    config_keys=frozenset(
        {
            "profile_id",
            "profile_version_id",
            "profile_version",
            "account_ref",
            "environment",
            "credentials",
            "probe_symbol",
            "connect_timeout_sec",
            "request_timeout_sec",
        }
    ),
)
