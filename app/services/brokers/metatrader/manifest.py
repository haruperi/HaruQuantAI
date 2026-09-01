"""Feature specification for MetaTrader direct broker channel."""

from app.contracts.broker.capabilities import PROVIDER_METATRADER_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-BRK-CONNECT_METATRADER",
    domain="brokers",
    provides=frozenset({PROVIDER_METATRADER_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Genuine bounded MetaTrader 5 market data, account state, and mutations."
    ),
    state=None,
    config_keys=frozenset(
        {
            "terminal_path",
            "login",
            "password",
            "server",
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
