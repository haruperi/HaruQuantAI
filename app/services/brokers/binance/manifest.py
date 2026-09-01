"""Feature specification for Binance direct broker channel."""

from app.contracts.broker.capabilities import PROVIDER_BINANCE_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_BINANCE",
    domain="brokers",
    provides=frozenset({PROVIDER_BINANCE_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Genuine bounded Binance Spot market data, order book, quotes, and streams."
    ),
    state=None,
    config_keys=frozenset(
        {
            "probe_symbol",
            "api_key",
            "api_secret",
            "request_timeout_sec",
            "connect_timeout_sec",
            "circuit_failure_threshold",
            "circuit_recovery_timeout_sec",
            "circuit_half_open_max_calls",
            "environment",
            "stream_buffer_size",
        }
    ),
)
