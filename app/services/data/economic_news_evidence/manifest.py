"""Feature specification for Economic Calendar and News Evidence."""

from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC: FeatureSpec = FeatureSpec(
    feature_id="FEAT-DATA-TRACK_MARKET_NEWS",
    domain="data",
    provides=frozenset({TRACK_MARKET_NEWS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description=(
        "Preserve point-in-time economic and news observations, revisions, "
        "coverage, freshness, and restriction evidence."
    ),
    state=StateDeclaration(
        namespace="data.economic_news",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description=(
            "Retained economic calendar and news observations, revisions, and "
            "coverage records."
        ),
    ),
    config_keys=frozenset(
        {
            "database_path",
            "max_query_results",
            "default_rate_limit_per_minute",
            "max_payload_size_bytes",
            "default_freshness_limit_seconds",
            "allowed_sources",
        }
    ),
)
