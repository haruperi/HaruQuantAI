"""Feature specification for Real-Time Market Events."""

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-STREAM_MARKET_EVENTS",
    domain="data",
    provides=frozenset({STREAM_MARKET_EVENTS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Normalize genuine live quotes, ticks, depth, status events, "
        "feed lifecycle, bounded buffering, gaps, and reconnect evidence."
    ),
    state=StateDeclaration(
        namespace="data.realtime_market_events",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained real-time market event records, "
            "feed states, and replay partitions."
        ),
    ),
    config_keys=frozenset(
        {
            "database_path",
            "buffer_capacity",
            "max_subscriptions",
            "max_instruments_per_subscription",
            "stale_timeout_seconds",
            "heartbeat_timeout_seconds",
            "max_replay_limit",
            "default_ordering_mode",
            "backpressure_policy",
        }
    ),
)
