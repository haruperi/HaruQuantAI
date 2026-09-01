"""Feature specification for cTrader direct broker channel."""

from app.contracts.broker.capabilities import PROVIDER_CTRADER_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_CTRADER",
    domain="brokers",
    provides=frozenset({PROVIDER_CTRADER_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Genuine bounded cTrader Open API market data, account state, and streams."
    ),
    state=None,
    config_keys=frozenset(
        {
            "client_id",
            "client_secret",
            "access_token",
            "account_id",
            "environment",
            "probe_symbol",
            "request_timeout_sec",
            "connect_timeout_sec",
            "circuit_failure_threshold",
            "circuit_recovery_timeout_sec",
            "circuit_half_open_max_calls",
            "stream_buffer_size",
        }
    ),
)
