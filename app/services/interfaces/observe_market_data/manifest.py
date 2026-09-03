"""Feature specification for the market data observation gateway."""

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_DATA_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-IFACE-OBSERVE_MARKET_DATA",
    domain="interfaces",
    provides=frozenset({OBSERVE_MARKET_DATA_CAPABILITY}),
    requires=frozenset({STREAM_MARKET_EVENTS_CAPABILITY}),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Expose market tick snapshots and observation events.",
    state=None,
    config_keys=frozenset({"stale_after_seconds", "max_symbols"}),
)
