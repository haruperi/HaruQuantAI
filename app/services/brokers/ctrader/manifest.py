"""Feature specification for cTrader external-provider connectivity."""

from app.contracts.broker.internal import CTRADER_PROVIDER_GATEWAY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_CTRADER",
    domain="brokers",
    provides=frozenset({CTRADER_PROVIDER_GATEWAY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own one removable cTrader application/account provider integration.",
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
