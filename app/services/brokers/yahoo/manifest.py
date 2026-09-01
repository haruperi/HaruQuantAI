"""Feature specification for Yahoo direct broker channel."""

from app.contracts.broker.capabilities import PROVIDER_YAHOO_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_YAHOO",
    domain="brokers",
    provides=frozenset({PROVIDER_YAHOO_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Genuine bounded Yahoo Finance historical bars for research "
        "and sandbox exploration."
    ),
    state=None,
    config_keys=frozenset(
        {
            "probe_symbol",
            "request_timeout_sec",
            "circuit_failure_threshold",
            "circuit_recovery_timeout_sec",
            "circuit_half_open_max_calls",
            "environment",
        }
    ),
)
