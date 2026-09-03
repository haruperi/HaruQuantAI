"""Feature specification for Bar Aggregation and Timeframes."""

from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.kernel.feature import FeatureSpec

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-AGGREGATE_BARS",
    domain="data",
    provides=frozenset({AGGREGATE_BARS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Aggregate series and define timeframe semantics.",
    state=None,
    config_keys=frozenset(
        {
            "max_bars_per_request",
            "default_timezone",
            "allow_custom_timeframes",
        }
    ),
)
