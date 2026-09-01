"""Feature specification for Dukascopy sandbox connectivity."""

from app.contracts.broker.internal import DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_DUKASCOPY",
    domain="brokers",
    provides=frozenset({DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Own one removable read-only Dukascopy sandbox provider integration.",
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
