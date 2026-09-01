"""Feature specification for point-in-time market-news tracking."""

from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.kernel.feature import FeatureSpec
from app.kernel.state import RetentionPolicy, StateDeclaration

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-TRACK_MARKET_NEWS",
    domain="data",
    provides=frozenset({TRACK_MARKET_NEWS_CAPABILITY}),
    requires=frozenset(),
    optional=frozenset(),
    conflicts=frozenset(),
    description="Record and query point-in-time market-news observations and revisions.",
    config_keys=frozenset({"database_path"}),
    state=StateDeclaration(
        namespace="data.market_news",
        schema_version=1,
        retention_policy=RetentionPolicy.RETAIN,
        description="Immutable observations and visible-from revisions/cancellations.",
    ),
)
