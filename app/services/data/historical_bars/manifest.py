"""Feature specification and capability metadata for Historical Bars."""

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.kernel.feature import FeatureSpec

SPEC = FeatureSpec(
    feature_id="FEAT-DATA-RETRIEVE_BARS",
    domain="data",
    provides=frozenset({HISTORICAL_BARS}),
    requires=frozenset({BROKER_MARKET_DATA}),
    optional=frozenset({BAR_CACHE}),
    description="Retrieve and normalize historical OHLCV bars from broker",
)
