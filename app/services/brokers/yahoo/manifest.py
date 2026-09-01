"""Feature specification for Yahoo sandbox connectivity."""

from app.contracts.broker.internal import YAHOO_PROVIDER_GATEWAY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_YAHOO",
    domain="brokers",
    provides=frozenset({YAHOO_PROVIDER_GATEWAY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own one removable read-only Yahoo sandbox provider integration.",
    config_keys=frozenset(
        {
            "profile_id",
            "profile_version_id",
            "profile_version",
            "account_ref",
            "environment",
            "probe_symbol",
            "connect_timeout_sec",
            "request_timeout_sec",
        }
    ),
)
