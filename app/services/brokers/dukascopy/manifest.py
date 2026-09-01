"""Feature specification for Dukascopy direct broker channel."""

from app.contracts.broker.capabilities import PROVIDER_DUKASCOPY_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_DUKASCOPY",
    domain="brokers",
    provides=frozenset({PROVIDER_DUKASCOPY_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Genuine bounded Dukascopy ticks and BID historical candles for research "
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
