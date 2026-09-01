"""Feature specification for Binance external-provider connectivity."""

from app.contracts.broker.internal import BINANCE_PROVIDER_GATEWAY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_BINANCE",
    domain="brokers",
    provides=frozenset({BINANCE_PROVIDER_GATEWAY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own one removable Binance provider profile and genuine provider reads.",
    config_keys=frozenset(
        {
            "profile_id",
            "profile_version_id",
            "profile_version",
            "account_ref",
            "provider_kind",
            "environment",
            "credentials",
            "probe_symbol",
            "connect_timeout_sec",
            "request_timeout_sec",
        }
    ),
)
